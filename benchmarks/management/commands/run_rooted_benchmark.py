"""
``manage.py run_rooted_benchmark`` — H4's third reading method (D74).

    scripts/dj5433.sh venv/bin/python manage.py run_rooted_benchmark --quick
    scripts/dj5433.sh venv/bin/python manage.py run_rooted_benchmark

D63's benchmark compared two storage methods. This one keeps the storage
fixed and varies the *query*: ``cte_rooted`` anchors the recursion on the
requested node instead of walking every root. Only the two read operations
are measured; the writes are ``cte``'s own code.

Everything that decides a number is D63's: the same shapes, sizes, seed and
targets, the same 5 warm-ups and 30 repeats, the same per-repeat budget,
server-side ``statement_timeout`` and address-space cap (D63f), and the same
paired bootstrap for the ratios. The guards are D63's too — the alias must be
PostgreSQL and must not be the development database.

Results go to ``experiments/results/tree-benchmark-rooted/<timestamp>/``
(``-quick`` for a pipeline run). Nothing under ``tree-benchmark/`` is read or
written: D63's results stand as they are.
"""

from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from benchmarks import environment, rooted, runner
from benchmarks.routers import BENCHMARK_ALIAS


class Command(BaseCommand):
    help = "Measure the rooted-CTE read against MPTT and tree-queries (H4, D74)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--quick", action="store_true",
                            help="10³ nodes, 5 repeats (pipeline check, not a result).")
        parser.add_argument("--database", default=BENCHMARK_ALIAS)
        parser.add_argument("--shapes", default=",".join(runner.DEFAULT_SHAPES))
        parser.add_argument("--sizes", default=None,
                            help="Comma-separated node counts (default 1000,10000,100000).")
        parser.add_argument("--warmups", type=int, default=5)
        parser.add_argument("--repeats", type=int, default=30)
        parser.add_argument("--timeout", type=float, default=120.0)
        parser.add_argument("--memory-limit-gb", type=float, default=8.0)
        parser.add_argument("--statement-timeout", type=int, default=None)
        parser.add_argument("--seed", type=int, default=20261006)
        parser.add_argument("--out", default=None)

    def handle(self, *args, **options):
        from benchmarks.management.commands.run_tree_benchmark import (
            _memory_cap,
            _numbers,
            _packages,
        )
        from benchmarks.rooted_tables import render
        from experiments import tables
        from experiments.provenance import GitState, Provenance, results_dir

        using = options["database"]
        quick = options["quick"]
        self._guard(using)

        shapes = tuple(part.strip() for part in options["shapes"].split(",") if part.strip())
        sizes = _numbers(options["sizes"]) or (
            runner.QUICK_SIZES if quick else runner.DEFAULT_SIZES
        )
        repeats = 5 if quick and options["repeats"] == 30 else options["repeats"]
        warmups = 2 if quick and options["warmups"] == 5 else options["warmups"]
        statement_timeout = (
            int(options["timeout"] * 1000) if options["statement_timeout"] is None
            else options["statement_timeout"]
        )
        limit = _memory_cap(options["memory_limit_gb"])

        git_start = GitState.capture()
        self.stdout.write(
            f"run_rooted_benchmark (H4, D74) — {'quick' if quick else 'full'}, "
            f"database alias {using}"
        )
        self.stdout.write(
            f"  memory cap: {'off' if not limit else f'{limit / 2**30:.1f} GiB'}, "
            f"statement_timeout: {statement_timeout} ms"
        )
        start_environment = environment.capture(using)

        document = rooted.run(
            using=using,
            shapes=shapes,
            sizes=sizes,
            warmups=warmups,
            repeats=repeats,
            timeout=options["timeout"],
            seed=options["seed"],
            statement_timeout=statement_timeout,
            log=self.stdout.write,
        )

        provenance = Provenance.capture(
            seeds={"trees": options["seed"], "targets": options["seed"],
                   "bootstrap": options["seed"]},
            argv=["python", "manage.py", "run_rooted_benchmark", *_argv(options)],
            packages=_packages(),
            git_start=git_start,
        )
        metrics = {
            "report": "tree_benchmark_rooted",
            "spec": "D74",
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
            "settings": {
                "warmups": warmups,
                "repeats": repeats,
                "timeout": options["timeout"],
                "replicates": runner.REPLICATES,
                "confidence_percent": int(runner.CONFIDENCE * 100),
                "memory_cap_bytes": limit,
                "statement_timeout_ms": statement_timeout,
            },
            **document,
        }

        directory = (
            Path(options["out"]).expanduser() if options["out"]
            else results_dir(
                "tree-benchmark-rooted-quick" if quick else "tree-benchmark-rooted",
            )
        )
        written = tables.write(directory, metrics, provenance.env_txt(), renderer=render)
        _write_csv(directory / "measurements.csv", rooted.csv_rows(document["cells"]))

        self.stdout.write(f"\nwritten to {directory}")
        for path in written.values():
            self.stdout.write(f"  {path.name}")
        self.stdout.write("  measurements.csv")
        self.stdout.write(f"D74: {document['reading']['status']}")

    def _guard(self, using: str) -> None:
        """D63's guards, unchanged: not the development database, and PostgreSQL."""
        from benchmarks.management.commands.run_tree_benchmark import Command as TreeCommand

        TreeCommand._guard(self, using)


def _argv(options: dict) -> list[str]:
    out: list[str] = []
    if options["quick"]:
        out.append("--quick")
    for name in ("database", "shapes", "sizes", "warmups", "repeats", "timeout",
                 "seed", "memory_limit_gb", "statement_timeout"):
        value = options.get(name)
        if value not in (None, ""):
            out += [f"--{name.replace('_', '-')}", str(value)]
    return out


def _write_csv(path: Path, rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
