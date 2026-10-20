"""
benchmarks/load_test.py — the Locust load test, end to end (stage 10, SN3, V-F2).

    scripts/dj5433.sh venv/bin/python -m benchmarks.load_test            # 50 users, 2 minutes
    scripts/dj5433.sh venv/bin/python -m benchmarks.load_test --quick    # 5 users, 20 s; a smoke test

1. Records the checkout (D54) and the machine's memory and swap before anything runs.
2. Uses a database of its own, ``<DATABASE_URL name>_locust`` on the same
   server (created if missing, never dropped): migrated, then seeded by
   ``seed_load_test`` with the V-F2 course and simulated learners only (D13).
   The development database is opened only to create that one.
3. Starts the API with ``DEBUG=False`` on Django's threaded ``runserver``
   (``--noreload``; no WSGI server is pinned in requirements.lock), Redis
   cache index 3, the login throttle raised so fifty logins from one address
   are not refused.
4. Runs ``benchmarks/locustfile.py`` headless and samples memory every 5 s.
5. Writes ``experiments/results/locust/<ts>/``: ``metrics.json``, ``tables.md``,
   ``env.txt`` and Locust's CSV files. The learners' password is generated per
   run and written nowhere.

p50 and p95 are Locust's: it keeps response times in buckets rounded to two
significant digits above 100 ms, so they are that coarse.
"""

from __future__ import annotations

import argparse
import csv
import json
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

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
LOCUST = str(Path(PYTHON).with_name("locust"))
ENDPOINTS = ("login", "next_question", "submit_answer", "trajectory")
V_F2_TARGET_MS = 300  # V-F2: local p95 below 300 ms (a soft target)
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


def server_statuses(log: Path) -> dict[str, int]:
    """Status codes the server logged, as a check on Locust's own counts."""
    pattern = re.compile(r'" (\d{3}) \d+$')
    counts: Counter[str] = Counter()
    for line in log.read_text(errors="replace").splitlines():
        match = pattern.search(line)
        if match:
            counts[match.group(1)] += 1
    return dict(sorted(counts.items()))


def tables(metrics: dict) -> str:
    run_ = metrics["run"]
    lines: list[str] = []
    warnings = metrics["provenance"]["tree_warnings"]
    if warnings:
        lines += ["> **Ogohlantirish (D54):** " + "; ".join(warnings), ""]
    lines += [
        f"# Locust: {run_['users']} foydalanuvchi, {run_['duration_s']} s",
        "",
        "| Endpoint | So‘rovlar | Xatolar | Xato ulushi | p50, ms | p95, ms | RPS |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in (*ENDPOINTS, "Aggregated"):
        row = metrics["endpoints"].get(name)
        if row is None:
            continue
        lines.append(
            f"| {name} | {row['requests']} | {row['failures']} | {row['error_share']:.2%} "
            f"| {row['p50_ms']:.0f} | {row['p95_ms']:.0f} | {row['rps']:.2f} |"
        )
    lines += ["", f"V-F2 mo‘ljali (p95 < {V_F2_TARGET_MS} ms, yumshoq):"]
    for name, verdict in metrics["v_f2"].items():
        lines.append(f"- `{name}`: {verdict}")
    env = metrics["environment"]
    lines += [
        "",
        "## Muhit",
        "",
        f"- Server: {run_['server']}; **DEBUG={run_['debug']}**; kesh {run_['cache']}; "
        f"`DB_CONN_MAX_AGE`={run_['db_conn_max_age']}",
        f"- Ma’lumotlar bazasi: `{run_['database']}` (alohida, faqat simulyatsiya — D13); "
        f"kurs: {run_['course']['topics']} mavzu, {run_['course']['prerequisites']} prerekvizit",
        f"- CPU: {env['cpu']['model']}, {env['cpu']['logical_cores']} mantiqiy yadro, "
        f"governor {env['cpu']['governors']}",
        f"- Xotira oldin: MemAvailable {env['memory_before']['MemAvailable']} MB / "
        f"MemTotal {env['memory_before']['MemTotal']} MB; swap bo‘sh "
        f"{env['memory_before']['SwapFree']} / {env['memory_before']['SwapTotal']} MB",
        f"- Yuk davomida: eng past MemAvailable {env['memory_during'].get('min_mem_available_mb')} MB, "
        f"eng past SwapFree {env['memory_during'].get('min_swap_free_mb')} MB "
        f"({env['memory_during'].get('samples')} namuna)",
        f"- Server logidagi status kodlari: {metrics['server_statuses']}",
        "",
        "## Manba",
        "",
        f"- commit `{metrics['provenance']['code_commit']}`, "
        f"dirty={metrics['provenance']['code_dirty']}",
        f"- buyruq: `{metrics['provenance']['command']}`",
        "- p50/p95 — Locust'ning o‘zi: 100 ms dan yuqorida vaqtlar ikki muhim raqamgacha yaxlitlangan.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--minutes", type=float, default=2.0)
    parser.add_argument("--spawn-rate", type=float, default=5.0)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--quick", action="store_true", help="5 users for 20 s, under locust-quick/.")
    args = parser.parse_args(argv)
    if args.quick:
        args.users, args.minutes = 5, 1 / 3

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, str(ROOT))
    import django

    django.setup()
    from benchmarks import environment
    from experiments.provenance import GitState, Provenance, Source, results_dir

    git_start = GitState.capture()
    memory_before = meminfo()
    print(f"MemAvailable {memory_before['MemAvailable']} MB, "
          f"swap free {memory_before['SwapFree']} / {memory_before['SwapTotal']} MB", flush=True)

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
    out = results_dir("locust-quick" if args.quick else "locust")
    child["LOAD_TEST_TAG"] = out.name  # fresh learners for every run
    seeded = run([
        PYTHON, "manage.py", "seed_load_test",
        "--learners", str(args.users), "--tag", child["LOAD_TEST_TAG"],
    ], child)
    summary = dict(re.findall(r"(\w+)=(\d+)", seeded.strip().splitlines()[-1]))
    child["LOAD_TEST_COURSE"] = summary["course"]

    out.mkdir(parents=True, exist_ok=True)
    base = f"http://127.0.0.1:{args.port}"
    with tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False) as log:
        server_log = Path(log.name)
    with open(server_log, "w") as log:
        server = subprocess.Popen(
            [PYTHON, "manage.py", "runserver", f"127.0.0.1:{args.port}", "--noreload"],
            env=child, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
        )
    try:
        wait_until_up(base)
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
            "server": "django runserver (threaded, one process, --noreload)",
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
        "v_f2": v_f2,
        "server_statuses": statuses,
        "environment": {
            **environment_start,
            "memory_before": memory_before,
            "memory_at_load_start": memory_at_start,
            "memory_during": memory_during,
            "at_end": environment.at_end(),
        },
        "provenance": provenance.payload(),
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    (out / "tables.md").write_text(tables(metrics))
    (out / "env.txt").write_text(provenance.env_txt())
    if locust.stderr.strip():
        (out / "locust-stderr.txt").write_text(locust.stderr)
    print(tables(metrics))
    print(f"Written to {out}")
    return out


if __name__ == "__main__":
    main()
