"""
benchmarks/routers.py — keep the benchmark out of the platform's database (D63).

One rule in both directions. The benchmark's two tables live only in the
``benchmark`` alias, and nothing else is allowed in there: a stray migration
or a mistyped ``--database`` would otherwise write a 100 000-row tree into the
development database, which stage 9's rules forbid.

``allow_relation`` stays permissive between two benchmark objects and refuses
across the boundary, which is the shape of the data anyway — the benchmark's
nodes point only at each other.
"""

from __future__ import annotations

BENCHMARK_APP = "benchmarks"
BENCHMARK_ALIAS = "benchmark"


class BenchmarkRouter:
    """Routes ``benchmarks`` to the benchmark alias and everything else away."""

    @staticmethod
    def _is_benchmark(model_or_label) -> bool:
        label = getattr(model_or_label, "_meta", None)
        return (label.app_label if label else model_or_label) == BENCHMARK_APP

    def db_for_read(self, model, **hints):
        return BENCHMARK_ALIAS if self._is_benchmark(model) else None

    def db_for_write(self, model, **hints):
        return BENCHMARK_ALIAS if self._is_benchmark(model) else None

    def allow_relation(self, obj1, obj2, **hints):
        first, second = self._is_benchmark(obj1), self._is_benchmark(obj2)
        if first and second:
            return True
        if first or second:
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == BENCHMARK_APP:
            return db == BENCHMARK_ALIAS
        if db == BENCHMARK_ALIAS:
            return False
        return None
