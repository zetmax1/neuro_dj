"""
``manage.py run_tree_benchmark`` — H4's storage benchmark (stage 9, D63).

    venv/bin/python manage.py run_tree_benchmark --quick
    venv/bin/python manage.py run_tree_benchmark

Replaces the old ``curriculum/management/commands/benchmark_tree.py``, which
measured one read on whatever happened to be in the development database, on
SQLite, and reported a mean (the audit's EX5 finding).

Two guards before anything is measured, both of them stage 9's rules:

- the ``benchmark`` alias must not be the development database. Its name is
  compared with ``default``'s and the command stops if they match, because
  every cell truncates its own two tables and a misconfigured alias would
  truncate them in the wrong place;
- the alias must be PostgreSQL. The claim is about recursive CTEs against an
  interval encoding under concurrent writes, and neither the concurrency nor
  the CTE plan transfers from SQLite (D1).

The result goes to ``experiments/results/tree-benchmark/<timestamp>/`` through
``experiments.tables``, so the same D48 rule applies as to every other result
in this thesis: every number in ``tables.md`` is a scalar that is already in
``metrics.json``, and the file is not written at all if one is not.
"""

from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from benchmarks import environment, runner
from benchmarks.routers import BENCHMARK_ALIAS

CHECKPOINTS = "experiments/.runs/checkpoints"


class Command(BaseCommand):
    help = "Benchmark the two tree storage methods (H4, D63). PostgreSQL only."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--quick", action="store_true",
                            help="10³ nodes, 5 repeats, short parallel phase (CI).")
        parser.add_argument("--database", default=BENCHMARK_ALIAS,
                            help=f"Database alias to measure (default {BENCHMARK_ALIAS}).")
        parser.add_argument("--shapes", default=",".join(runner.DEFAULT_SHAPES))
        parser.add_argument("--sizes", default=None,
                            help="Comma-separated node counts (default 1000,10000,100000).")
        parser.add_argument("--parallel-workers", default=None,
                            help="Comma-separated process counts (default 2,4,8).")
        parser.add_argument("--warmups", type=int, default=5)
        parser.add_argument("--repeats", type=int, default=30)
        parser.add_argument("--timeout", type=float, default=120.0,
                            help="Seconds one repeat may take before the cell is a timeout.")
        parser.add_argument("--parallel-seconds", type=float, default=None)
        parser.add_argument("--parallel-repeats", type=int, default=3)
        parser.add_argument("--seed", type=int, default=20261006)
        parser.add_argument("--checkpoint-dir", default=CHECKPOINTS)
        parser.add_argument("--no-checkpoint", action="store_true")
        parser.add_argument("--out", default=None)

    def handle(self, *args, **options):
        from experiments import tables
        from experiments.provenance import GitState, Provenance, results_dir

        using = options["database"]
        quick = options["quick"]
        self._guard(using)

        shapes = tuple(part.strip() for part in options["shapes"].split(",") if part.strip())
        sizes = _numbers(options["sizes"]) or (
            runner.QUICK_SIZES if quick else runner.DEFAULT_SIZES
        )
        workers = _numbers(options["parallel_workers"]) or (
            runner.QUICK_WORKERS if quick else runner.DEFAULT_WORKERS
        )
        repeats = 5 if quick and options["repeats"] == 30 else options["repeats"]
        warmups = 2 if quick and options["warmups"] == 5 else options["warmups"]
        parallel_seconds = options["parallel_seconds"] or (5.0 if quick else 20.0)
        parallel_repeats = 2 if quick and options["parallel_repeats"] == 3 else options["parallel_repeats"]

        git_start = GitState.capture()
        self.stdout.write(
            f"run_tree_benchmark (H4, D63) — {'quick' if quick else 'full'}, "
            f"database alias {using}"
        )
        start_environment = environment.capture(using)

        checkpoint = runner.Checkpoint(
            options["checkpoint_dir"],
            {
                "commit": git_start.commit,
                "seed": options["seed"],
                "shapes": list(shapes),
                "sizes": list(sizes),
                "workers": list(workers),
                "warmups": warmups,
                "repeats": repeats,
                "timeout": options["timeout"],
                "parallel_seconds": parallel_seconds,
                "parallel_repeats": parallel_repeats,
                "quick": bool(quick),
            },
            enabled=bool(git_start.dirty is False and not options["no_checkpoint"]),
            log=self.stdout.write,
        )
        self.stdout.write(
            f"  checkpoint: {checkpoint.directory if checkpoint.enabled else 'off (tree not clean or --no-checkpoint)'}"
        )

        document = runner.run(
            using=using,
            shapes=shapes,
            sizes=sizes,
            workers=workers,
            warmups=warmups,
            repeats=repeats,
            timeout=options["timeout"],
            parallel_seconds=parallel_seconds,
            parallel_repeats=parallel_repeats,
            seed=options["seed"],
            checkpoint=checkpoint,
            quick=bool(quick),
            log=self.stdout.write,
        )

        provenance = Provenance.capture(
            seeds={"trees": options["seed"], "targets": options["seed"],
                   "bootstrap": options["seed"]},
            argv=["python", "manage.py", "run_tree_benchmark", *_argv(options)],
            packages=_packages(),
            git_start=git_start,
        )
        metrics = {
            "report": "tree_benchmark",
            "spec": "D63",
            "quick": bool(quick),
            "thesis_result": not quick,
            "hypothesis": "H4",
            "provenance": provenance.payload(),
            "environment": start_environment,
            "environment_at_end": environment.at_end(),
            "database": {
                "alias": using,
                "name": connections[using].settings_dict.get("NAME"),
                "vendor": connections[using].vendor,
            },
            "checkpoint": checkpoint.payload(),
            **document,
        }

        directory = (
            Path(options["out"]).expanduser() if options["out"]
            else results_dir("tree-benchmark-quick" if quick else "tree-benchmark")
        )
        written = tables.write(
            directory, metrics, provenance.env_txt(),
            renderer=tables.render_tree_benchmark_report,
        )
        _write_csv(directory / "measurements.csv", runner.csv_rows(document))

        self.stdout.write(f"\nwritten to {directory}")
        for path in written.values():
            self.stdout.write(f"  {path.name}")
        self.stdout.write("  measurements.csv")
        self.stdout.write(f"H4: {document['reading']['status']}")

    def _guard(self, using: str) -> None:
        if using not in connections:
            raise CommandError(f"unknown database alias {using!r}")
        settings = connections[using].settings_dict
        default = connections["default"].settings_dict
        if settings.get("NAME") == default.get("NAME") and settings.get(
            "HOST"
        ) == default.get("HOST") and settings.get("PORT") == default.get("PORT"):
            raise CommandError(
                "the benchmark alias resolves to the development database. Stage 9's "
                "rule is that nothing here touches it: set BENCHMARK_DATABASE_URL, or "
                "create the '<name>_bench' database on the same server."
            )
        if connections[using].vendor != "postgresql":
            raise CommandError(
                f"the benchmark needs PostgreSQL (D1); alias {using!r} is "
                f"{connections[using].vendor}"
            )
        try:
            connections[using].ensure_connection()
        except Exception as error:  # noqa: BLE001 - a missing database is a message, not a traceback
            raise CommandError(
                f"cannot connect to the benchmark database: {type(error).__name__}: {error}\n"
                "Create it once, on the same server as the development database, e.g.\n"
                "  docker exec <postgres container> bash -c "
                "'createdb -U \"$POSTGRES_USER\" \"${POSTGRES_DB}_bench\"'"
            ) from error


def _numbers(text: str | None) -> tuple[int, ...]:
    if not text:
        return ()
    return tuple(int(part.strip()) for part in text.split(",") if part.strip())


def _argv(options: dict) -> list[str]:
    """The flags that change a number, for the provenance record."""
    out: list[str] = []
    if options["quick"]:
        out.append("--quick")
    for name in ("database", "shapes", "sizes", "parallel_workers", "warmups",
                 "repeats", "timeout", "parallel_seconds", "parallel_repeats", "seed"):
        value = options.get(name)
        if value not in (None, ""):
            out += [f"--{name.replace('_', '-')}", str(value)]
    return out


def _packages() -> dict[str, str]:
    from importlib.metadata import PackageNotFoundError, version

    out: dict[str, str] = {}
    for name in ("django", "django-mptt", "django-tree-queries", "psycopg"):
        try:
            out[name] = version(name)
        except PackageNotFoundError:  # pragma: no cover - both are pinned in the lock
            continue
    return out


def _write_csv(path: Path, rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
