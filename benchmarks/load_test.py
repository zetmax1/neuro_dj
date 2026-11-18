"""
benchmarks/load_test.py — the Locust load test, end to end (stage 10, SN3, V-F2).

    scripts/dj5433.sh venv/bin/python -m benchmarks.load_test --workers W       # gunicorn, 50 users, 2 min
    scripts/dj5433.sh venv/bin/python -m benchmarks.load_test --server runserver
    scripts/dj5433.sh venv/bin/python -m benchmarks.load_test --probe           # a warm worker's RSS
    scripts/dj5433.sh venv/bin/python -m benchmarks.load_test --quick ...       # 5 users, 20 s; a smoke test

1. Records the checkout (D54) and the machine's memory and swap before anything runs.
2. Uses a database of its own, ``<DATABASE_URL name>_locust`` on the same
   server (created if missing, never dropped): migrated, then seeded by
   ``seed_load_test`` with the V-F2 course and simulated learners only (D13).
   The development database is opened only to create that one.
3. Starts the API with ``DEBUG=False`` — on gunicorn with ``--workers`` sync
   workers (D68a; the main result) or on Django's threaded ``runserver``
   (``--noreload``; the first runs, kept as a supplement) — with Redis cache
   index 3 and the login throttle raised so fifty logins from one address are
   not refused. ``--probe`` starts one gunicorn worker, warms it with one
   learner's requests and prints its resident memory: the number D68a's
   worker count is computed from.
4. Runs ``benchmarks/locustfile.py`` headless and samples memory every 5 s.
5. Writes ``experiments/results/locust/<ts>/``: ``metrics.json``, ``tables.md``,
   ``env.txt`` and Locust's CSV files. The table goes through
   ``experiments.tables.write``, so every number it prints is rendered by
   ``fmt`` and verified against ``metrics.json`` before anything is written
   (D48). The learners' password is generated per run and written nowhere.

p50 and p95 are Locust's: it keeps response times in buckets rounded to two
significant digits above 100 ms, so they are that coarse.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from experiments import tables as result_tables
from experiments.tables import fmt

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
LOCUST = str(Path(PYTHON).with_name("locust"))
GUNICORN = str(Path(PYTHON).with_name("gunicorn"))
ENDPOINTS = ("login", "next_question", "submit_answer", "trajectory")
V_F2_TARGET_MS = 300  # V-F2: local p95 below 300 ms (a soft target)
LOCUST_ROUNDING_ABOVE_MS = 100  # Locust keeps two significant digits above this
REDIS_URL = "redis://127.0.0.1:6380/3"


def meminfo() -> dict[str, int]:
    """MemTotal, MemAvailable, SwapTotal and SwapFree in MB."""
    out: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            out[key] = int(value.split()[0]) // 1024
    return out


class MemorySampler(threading.Thread):
    """MemAvailable and SwapFree every ``interval`` seconds while the load runs."""

    def __init__(self, interval: float = 5.0) -> None:
        super().__init__(daemon=True)
        self.interval = interval
        self.samples: list[dict[str, int]] = []
        self._halt = threading.Event()

    def run(self) -> None:
        while not self._halt.is_set():
            self.samples.append(meminfo())
            self._halt.wait(self.interval)

    def stop(self) -> dict:
        self._halt.set()
        self.join()
        if not self.samples:
            return {}
        return {
            "samples": len(self.samples),
            "min_mem_available_mb": min(s["MemAvailable"] for s in self.samples),
            "min_swap_free_mb": min(s["SwapFree"] for s in self.samples),
        }


def locust_database_url(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    name = parts.path.lstrip("/") + "_locust"
    return urlunsplit(parts._replace(path="/" + name)), name


def ensure_database(name: str) -> bool:
    """Create the load-test database on the same server if it is missing."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [name])
        if cursor.fetchone():
            return False
        cursor.execute(f'CREATE DATABASE "{name}"')
    return True


def run(args: list[str], env: dict) -> str:
    done = subprocess.run(args, env=env, cwd=ROOT, capture_output=True, text=True)
    if done.returncode != 0:
        raise SystemExit(f"{' '.join(args)} failed:\n{done.stdout}\n{done.stderr}")
    return done.stdout


def server_command(server: str, workers: int | None, port: int) -> list[str]:
    if server == "runserver":
        return [PYTHON, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"]
    return [
        GUNICORN, "config.wsgi:application", "--workers", str(workers),
        "--bind", f"127.0.0.1:{port}", "--timeout", "120",
        # The access log in the shape server_statuses() reads.
        "--access-logfile", "-", "--access-logformat", '"%(r)s" %(s)s %(B)s',
    ]


def server_label(server: str, workers: int | None) -> str:
    if server == "runserver":
        return "django runserver (threaded, one process, --noreload)"
    from importlib.metadata import version

    return f"gunicorn {version('gunicorn')}, {workers} sync workers"


# D68a: the machine the main result may be measured on.
QUIET_MIN_AVAILABLE_MB = 6 * 1024
QUIET_MAX_SWAP_USED_MB = 200
QUIET_MAX_PROCESS_CPU = 10.0  # % of one CPU over a 2 s sample


def busy_now(threshold: float = QUIET_MAX_PROCESS_CPU) -> list[dict]:
    """
    Processes above ``threshold`` % CPU over a 2-second sample — what is
    competing right now. ``ps``' %CPU is a lifetime average and called a
    just-started server 239 %; ``top``'s second frame is the interval itself.
    """
    try:
        output = subprocess.run(
            ["top", "-b", "-n", "2", "-d", "2", "-w", "200"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return []
    frame = output.split("\ntop - ")[-1].splitlines()
    header = next(i for i, line in enumerate(frame) if line.lstrip().startswith("PID"))
    columns = frame[header].split()
    cpu, command = columns.index("%CPU"), columns.index("COMMAND")
    out = []
    for line in frame[header + 1:]:
        parts = line.split(None, len(columns) - 1)
        if len(parts) < len(columns):
            continue
        try:
            value = float(parts[cpu].replace(",", "."))
        except ValueError:
            continue
        if value >= threshold:
            out.append({"cpu_percent": value, "command": parts[command]})
    return sorted(out, key=lambda row: -row["cpu_percent"])


def quiet_machine(memory: dict[str, int], busy: list[dict]) -> list[str]:
    """What keeps this machine from D68a's conditions; empty when it is quiet."""
    problems = []
    if memory["MemAvailable"] < QUIET_MIN_AVAILABLE_MB:
        problems.append(f"MemAvailable {memory['MemAvailable']} MB < {QUIET_MIN_AVAILABLE_MB} MB")
    swap_used = memory["SwapTotal"] - memory["SwapFree"]
    if swap_used >= QUIET_MAX_SWAP_USED_MB:
        problems.append(f"swap used {swap_used} MB >= {QUIET_MAX_SWAP_USED_MB} MB")
    if busy:
        problems.append("busy: " + ", ".join(f"{b['command']} {b['cpu_percent']}%" for b in busy))
    return problems


def rss_mb(pid: int) -> int:
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) // 1024
    return 0


def probe(base: str, server_pid: int, email: str, password: str, course: str) -> dict:
    """One learner's requests through a single worker, then its resident memory."""
    import requests

    session = requests.Session()
    csrf = session.get(f"{base}/api/accounts/csrf/", timeout=30)
    login = session.post(
        f"{base}/api/accounts/token/", json={"email": email, "password": password},
        headers={"X-CSRFToken": csrf.json()["csrfToken"]},
        cookies={"csrftoken": csrf.cookies.get("csrftoken", "")}, timeout=30,
    )
    session.headers["Authorization"] = f"Bearer {login.json()['access']}"
    for _ in range(20):
        head = session.get(f"{base}/api/learning/trajectory/?course={course}", timeout=60).json()["next"]
        question = session.get(f"{base}/api/assessments/next_question/?topic_id={head['topic_id']}", timeout=60)
        if question.status_code == 200:
            body = question.json()
            session.post(
                f"{base}/api/assessments/submit_answer/",
                json={"question_id": body["id"], "choice_id": body["choices"][0]["id"]}, timeout=60,
            )
    children = Path(f"/proc/{server_pid}/task/{server_pid}/children").read_text().split()
    return {
        "master_rss_mb": rss_mb(server_pid),
        "worker_rss_mb": [rss_mb(int(pid)) for pid in children],
        "requests": 1 + 1 + 20 * 3,
    }


def wait_until_up(base: str, seconds: float = 60.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base}/api/accounts/csrf/", timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    raise SystemExit(f"The server at {base} did not come up in {seconds:.0f} s.")


def read_stats(prefix: Path) -> dict[str, dict]:
    """Locust's ``<prefix>_stats.csv``, one row per endpoint plus ``Aggregated``."""
    out: dict[str, dict] = {}
    with open(f"{prefix}_stats.csv", newline="") as handle:
        for row in csv.DictReader(handle):
            requests = int(row["Request Count"])
            failures = int(row["Failure Count"])
            out[row["Name"]] = {
                "requests": requests,
                "failures": failures,
                "error_share": failures / requests if requests else 0.0,
                "p50_ms": float(row["50%"]) if row["50%"] != "N/A" else None,
                "p95_ms": float(row["95%"]) if row["95%"] != "N/A" else None,
                "mean_ms": float(row["Average Response Time"]),
                "max_ms": float(row["Max Response Time"]),
                "rps": float(row["Requests/s"]),
            }
    return out


def server_statuses(log: Path) -> list[dict[str, int]]:
    """
    Status codes the server logged, as a check on Locust's own counts. A list
    of records rather than a {code: count} mapping: every number tables.md
    shows has to be a value in metrics.json (D48), and keys are not values.
    """
    pattern = re.compile(r'" (\d{3}) \d+$')
    counts: Counter[int] = Counter()
    for line in log.read_text(errors="replace").splitlines():
        match = pattern.search(line)
        if match:
            counts[int(match.group(1))] += 1
    return [{"status": code, "count": n} for code, n in sorted(counts.items())]


def render(metrics: dict) -> str:
    """tables.md; every number through ``fmt``, as ``tables.verify`` expects."""
    run_ = metrics["run"]
    lines: list[str] = []
    warnings = metrics["provenance"]["tree_warnings"]
    if warnings:
        lines += ["> **Ogohlantirish (D54):** " + "; ".join(warnings), ""]
    lines += [
        f"# Locust: {fmt(run_['users'])} foydalanuvchi, {fmt(run_['duration_s'])} s",
        "",
        "| Endpoint | So‘rovlar | Xatolar | Xato ulushi | p50, ms | p95, ms | RPS |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in (*ENDPOINTS, "Aggregated"):
        row = metrics["endpoints"].get(name)
        if row is None:
            continue
        lines.append(
            f"| {name} | {fmt(row['requests'])} | {fmt(row['failures'])} | {fmt(row['error_share'])} "
            f"| {fmt(row['p50_ms'])} | {fmt(row['p95_ms'])} | {fmt(row['rps'])} |"
        )
    lines += ["", f"V-F2 mo‘ljali (p95 < {fmt(metrics['v_f2_target_ms'])} ms, yumshoq):"]
    for name, verdict in metrics["v_f2"].items():
        lines.append(f"- `{name}`: {verdict}")
    env = metrics["environment"]
    during = env["memory_during"]
    lines += [
        "",
        "## Muhit",
        "",
        f"- Server: {run_['server']}; **DEBUG={run_['debug']}**; kesh {run_['cache']}; "
        f"`DB_CONN_MAX_AGE`={fmt(run_['db_conn_max_age'])}",
        f"- Ma’lumotlar bazasi: `{run_['database']}` (alohida, faqat simulyatsiya — D13); "
        f"kurs: {fmt(run_['course']['topics'])} mavzu, "
        f"{fmt(run_['course']['prerequisites'])} prerekvizit",
        f"- CPU: {env['cpu']['model']}, {fmt(env['cpu']['logical_cores'])} mantiqiy yadro, "
        f"governor {', '.join(env['cpu']['governors'] or ['—'])}",
        f"- Xotira oldin: MemAvailable {fmt(env['memory_before']['MemAvailable'])} MB / "
        f"MemTotal {fmt(env['memory_before']['MemTotal'])} MB; swap bo‘sh "
        f"{fmt(env['memory_before']['SwapFree'])} / {fmt(env['memory_before']['SwapTotal'])} MB",
        f"- Yuk davomida: eng past MemAvailable {fmt(during['min_mem_available_mb'])} MB, "
        f"eng past SwapFree {fmt(during['min_swap_free_mb'])} MB "
        f"({fmt(during['samples'])} namuna)",
        "- Server logidagi status kodlari: "
        + ", ".join(f"{fmt(s['status'])} — {fmt(s['count'])}" for s in metrics["server_statuses"]),
        "",
        "## Manba",
        "",
        f"- commit `{metrics['provenance']['code_commit']}`, "
        f"dirty={metrics['provenance']['code_dirty']}",
        f"- buyruq: `{metrics['provenance']['command']}`",
        f"- p50/p95 — Locust'ning o‘zi: {fmt(metrics['locust_rounding_above_ms'])} ms dan yuqorida "
        "vaqtlar ikki muhim raqamgacha yaxlitlangan.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--minutes", type=float, default=2.0)
    parser.add_argument("--spawn-rate", type=float, default=5.0)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--quick", action="store_true", help="5 users for 20 s, under locust-quick/.")
    parser.add_argument("--server", choices=("gunicorn", "runserver"), default="gunicorn")
    parser.add_argument("--workers", type=int, default=None, help="gunicorn sync workers (D68a).")
    parser.add_argument("--allow-busy", action="store_true",
                        help="Run although D68a's quiet-machine conditions fail (recorded).")
    parser.add_argument("--probe", action="store_true",
                        help="One warm gunicorn worker's RSS; writes no result.")
    args = parser.parse_args(argv)
    if args.quick:
        args.users, args.minutes = 5, 1 / 3
    if args.probe:
        args.server, args.workers, args.users = "gunicorn", 1, 1
    if args.server == "gunicorn" and not args.workers:
        parser.error("--workers is required with gunicorn (D68a computes it)")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, str(ROOT))
    import django

    django.setup()
    from benchmarks import environment
    from experiments.provenance import GitState, Provenance, Source, results_dir

    git_start = GitState.capture()
    memory_before = meminfo()
    busy_before = busy_now()
    print(f"MemAvailable {memory_before['MemAvailable']} MB, "
          f"swap free {memory_before['SwapFree']} / {memory_before['SwapTotal']} MB, "
          f"busy {busy_before}", flush=True)
    problems = quiet_machine(memory_before, busy_before)
    if problems and not (args.quick or args.probe or args.allow_busy):
        raise SystemExit("load_test: the machine is not quiet (D68a): " + "; ".join(problems))

    url, database = locust_database_url(os.environ["DATABASE_URL"])
    created = ensure_database(database)
    password = secrets.token_urlsafe(16)
    child = {
        **os.environ,
        "DATABASE_URL": url,
        "DJANGO_ENV_FILE": "",
        "DEBUG": "False",
        "ALLOWED_HOSTS": "127.0.0.1,localhost",
        "SECURE_SSL_REDIRECT": "False",
        "LOGIN_THROTTLE_RATE": "100000/minute",
        "REDIS_URL": REDIS_URL,
        "LOAD_TEST_PASSWORD": password,
        "LOAD_TEST_LEARNERS": str(args.users),
    }
    run([PYTHON, "manage.py", "migrate", "--noinput"], child)
    out = results_dir("locust-quick" if args.quick or args.probe else "locust")
    child["LOAD_TEST_TAG"] = out.name  # fresh learners for every run
    seeded = run([
        PYTHON, "manage.py", "seed_load_test",
        "--learners", str(args.users), "--tag", child["LOAD_TEST_TAG"],
    ], child)
    summary = dict(re.findall(r"(\w+)=(\d+)", seeded.strip().splitlines()[-1]))
    child["LOAD_TEST_COURSE"] = summary["course"]

    base = f"http://127.0.0.1:{args.port}"
    if not args.probe:
        out.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False) as log:
        server_log = Path(log.name)
    with open(server_log, "w") as log:
        server = subprocess.Popen(
            server_command(args.server, args.workers, args.port),
            env=child, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
        )
    try:
        wait_until_up(base)
        if args.probe:
            measured = probe(
                base, server.pid, f"load-{out.name}-00@simulated.invalid", password, summary["course"],
            )
            print(measured)
            server_log.unlink(missing_ok=True)
            return out
        environment_start = environment.capture("default")
        memory_at_start = meminfo()
        sampler = MemorySampler()
        sampler.start()
        duration = round(args.minutes * 60)
        started = time.monotonic()
        locust = subprocess.run(
            [
                LOCUST, "-f", str(ROOT / "benchmarks" / "locustfile.py"), "--headless",
                "-u", str(args.users), "-r", str(args.spawn_rate), "-t", f"{duration}s",
                "--host", base, "--csv", str(out / "locust"), "--only-summary",
                "--loglevel", "WARNING",
            ],
            env=child, cwd=ROOT, capture_output=True, text=True,
        )
        wall = time.monotonic() - started
        memory_during = sampler.stop()
    finally:
        server.terminate()
        server.wait(timeout=30)

    endpoints = read_stats(out / "locust")
    statuses = server_statuses(server_log)
    server_log.unlink(missing_ok=True)
    # No input data file: the workload is defined by these two, so their
    # hashes are the sources D48 asks for.
    provenance = Provenance.capture(
        argv=[Path(sys.argv[0]).name, *sys.argv[1:]],
        git_start=git_start,
        seeds={"seed_load_test": 20261020},
        sources=(
            Source.of("locustfile", ROOT / "benchmarks" / "locustfile.py"),
            Source.of("seed_load_test", ROOT / "benchmarks" / "management" / "commands" / "seed_load_test.py"),
        ),
    )
    v_f2 = {}
    for name in ("submit_answer", "trajectory", "next_question"):
        p95 = endpoints.get(name, {}).get("p95_ms")
        v_f2[name] = (
            "o‘lchanmadi" if p95 is None
            else f"p95 {p95:.0f} ms — {'mo‘ljal ichida' if p95 < V_F2_TARGET_MS else 'mo‘ljaldan yuqori'}"
        )
    metrics = {
        "run": {
            "users": args.users,
            "spawn_rate": args.spawn_rate,
            "duration_s": duration,
            "wall_s": round(wall, 1),
            "locust_exit_code": locust.returncode,
            "server": server_label(args.server, args.workers),
            "server_kind": args.server,
            "workers": args.workers if args.server == "gunicorn" else 1,
            "debug": False,
            "cache": f"Redis ({REDIS_URL})",
            "db_conn_max_age": int(child.get("DB_CONN_MAX_AGE", "0")),
            "login_throttle": child["LOGIN_THROTTLE_RATE"],
            "database": database,
            "database_created_now": created,
            "course": {k: int(v) for k, v in summary.items()},
            "flow": "login → next_question → submit_answer → trajectory (benchmarks/locustfile.py)",
            "correct_rate": 0.75,
        },
        "endpoints": endpoints,
        "v_f2_target_ms": V_F2_TARGET_MS,
        "locust_rounding_above_ms": LOCUST_ROUNDING_ABOVE_MS,
        "v_f2": v_f2,
        "server_statuses": statuses,
        "environment": {
            **environment_start,
            "memory_before": memory_before,
            "busy_before": busy_before,
            "quiet_machine_problems": problems,
            "memory_at_load_start": memory_at_start,
            "memory_during": memory_during,
            "at_end": environment.at_end(),
        },
        "provenance": provenance.payload(),
    }
    # Locust's own end-of-run summary (it prints it to stderr).
    if locust.stderr.strip():
        (out / "locust-stderr.txt").write_text(locust.stderr)
    result_tables.write(out, metrics, provenance.env_txt(), renderer=render)
    print(render(metrics))
    print(f"Written to {out}")
    return out


if __name__ == "__main__":
    main()
