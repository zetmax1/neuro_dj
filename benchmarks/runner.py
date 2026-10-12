"""
benchmarks/runner.py — the measurement loop of H4 (D63).

One cell is a (shape, size, operation) pair of methods. For each cell:

1. both tables are built from the same parent list (``generator.build_all``);
2. the targets are drawn once, with a seed, and used for the **same repeat
   number** of both methods — that pairing is what makes the ratio's interval
   a paired bootstrap rather than two independent samples;
3. 5 warm-ups, then 30 repeats per method, each timed with
   ``perf_counter`` and counted with ``CaptureQueriesContext``;
4. a mutating operation runs inside ``atomic`` with ``set_rollback(True)``, so
   every repeat starts from the same tree and both methods see the same state.
   The cost of the commit is therefore outside the measurement, equally for
   both methods (D63);
5. the ratio ρ = median(mptt) / median(cte) with a percentile interval from
   1 000 paired resamples of the repeat indices, and the verdict of D63's
   reading rule.

A repeat that runs longer than the timeout ends the cell: it is recorded as
``timeout`` with the time it had reached, and no number is reported for it
(D63). Finished cells are checkpointed, so an interrupted run resumes instead
of starting the 100 000-node trees again.

The parallel phase is separate: a fixed duration rather than repeats, three
worker counts, and the integrity checks of :mod:`benchmarks.integrity`
afterwards.
"""

from __future__ import annotations

import hashlib
import json
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

from django.db import connections, transaction
from django.test.utils import CaptureQueriesContext

from benchmarks import generator, integrity, operations, parallel
from benchmarks.models import CTE, METHODS, MODELS, MPTT, Shape

REPLICATES = 1000
CONFIDENCE = 0.95

# D63's reading rule: a read cell is "comparable" while CTE is not more than
# this many times slower than MPTT.
READ_TOLERANCE = 1.5

CTE_FASTER = "CTE tezroq"
MPTT_FASTER = "MPTT tezroq"
COMPARABLE = "taqqoslanadigan"
TIMEOUT = "timeout"

SUPPORTED = "qo‘llab-quvvatlandi"
NOT_SUPPORTED = "qo‘llab-quvvatlanmadi"
NOT_COMPUTED = "hisoblanmadi"

DEFAULT_SHAPES: tuple[str, ...] = (Shape.COURSE_LIKE, Shape.DEEP_CHAIN, Shape.RANDOM)
DEFAULT_SIZES: tuple[int, ...] = (1_000, 10_000, 100_000)
DEFAULT_WORKERS: tuple[int, ...] = (2, 4, 8)
QUICK_SIZES: tuple[int, ...] = (1_000,)
QUICK_WORKERS: tuple[int, ...] = (2, 4)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def quantile(values: list[float], share: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = share * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summarise(values: list[float]) -> dict:
    """What one method's repeats of one operation come to."""
    if not values:
        return {"repeats": 0}
    median = statistics.median(values)
    p95 = quantile(values, 0.95) or 0.0
    return {
        "repeats": len(values),
        "median": round(median, 6),
        "p95": round(p95, 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "mean": round(statistics.fmean(values), 6),
        # Milliseconds as their own scalars: the table prints these, and a
        # table may only print numbers that are in metrics.json (D48). At
        # three decimals a read of a small tree would otherwise round to zero.
        "median_ms": round(median * 1000, 3),
        "p95_ms": round(p95 * 1000, 3),
    }


def ratio_interval(
    mptt: list[float], cte: list[float], *, seed: int, replicates: int = REPLICATES,
) -> dict:
    """
    ρ = median(mptt) / median(cte), with a paired percentile interval.

    Paired: one resample draws repeat **indices** and takes both methods'
    timings at those indices, because repeat *i* of both methods ran on the
    same target node (D63). An unpaired interval would be wider for no reason
    and would ignore that the targets vary from repeat to repeat.
    """
    if not mptt or not cte or len(mptt) != len(cte):
        return {"ratio": None, "ci_low": None, "ci_high": None, "replicates": 0}
    point = statistics.median(mptt) / statistics.median(cte)
    rng = random.Random(seed)
    size = len(mptt)
    draws: list[float] = []
    for _ in range(replicates):
        indices = [rng.randrange(size) for _ in range(size)]
        left = statistics.median([mptt[index] for index in indices])
        right = statistics.median([cte[index] for index in indices])
        if right > 0:
            draws.append(left / right)
    if not draws:
        return {"ratio": round(point, 6), "ci_low": None, "ci_high": None, "replicates": 0}
    alpha = (1.0 - CONFIDENCE) / 2.0
    return {
        "ratio": round(point, 6),
        "ci_low": round(quantile(draws, alpha) or 0.0, 6),
        "ci_high": round(quantile(draws, 1.0 - alpha) or 0.0, 6),
        "replicates": len(draws),
        "paired": True,
    }


def verdict_of(entry: dict) -> str:
    """D63's three outcomes, from the interval alone."""
    low, high = entry.get("ci_low"), entry.get("ci_high")
    if entry.get("ratio") is None or low is None or high is None:
        return NOT_COMPUTED
    if low > 1.0:
        return CTE_FASTER
    if high < 1.0:
        return MPTT_FASTER
    return COMPARABLE


# ---------------------------------------------------------------------------
# One cell
# ---------------------------------------------------------------------------

@dataclass
class Budget:
    """How long one repeat may take, and what to do when it does not finish."""

    timeout: float

    def exceeded(self, seconds: float) -> bool:
        return seconds > self.timeout


def measure(
    operation: operations.Operation,
    method: str,
    targets: list[dict],
    *,
    using: str,
    warmups: int,
    repeats: int,
    budget: Budget,
) -> dict:
    """
    One (operation, method): warm-ups, then timed repeats with their query
    counts. Returns the timings and, when a repeat exceeds the budget, the
    ``timeout`` status instead of numbers.
    """
    connection = connections[using]
    timings: list[float] = []
    queries: list[int] = []
    rows: list[int] = []

    for index in range(warmups + repeats):
        target = targets[index % len(targets)]
        timed = index >= warmups
        try:
            with CaptureQueriesContext(connection) as captured:
                started = time.perf_counter()
                if operation.mutates:
                    with transaction.atomic(using=using):
                        touched = operation.run(method, target, using)
                        # Every repeat starts from the same tree (D63).
                        transaction.set_rollback(True, using=using)
                else:
                    touched = operation.run(method, target, using)
                seconds = time.perf_counter() - started
        except Exception as error:  # noqa: BLE001 - reported, never silently skipped
            return {
                "status": "error",
                "error": f"{type(error).__name__}: {error}",
                "completed_repeats": len(timings),
            }
        if budget.exceeded(seconds):
            # Warm-ups are checked as well: a cell that cannot finish one
            # repeat inside the budget has no numbers to report, and waiting
            # out five of them first would only delay saying so.
            return {
                "status": TIMEOUT,
                "timeout": budget.timeout,
                "reached": round(seconds, 6),
                "completed_repeats": len(timings),
                "during_warmup": not timed,
            }
        if not timed:
            continue
        timings.append(seconds)
        queries.append(len(captured.captured_queries))
        rows.append(touched)

    return {
        "status": "ok",
        "timings": [round(value, 6) for value in timings],
        "seconds": summarise(timings),
        "queries_median": statistics.median(queries) if queries else None,
        "queries_min": min(queries) if queries else None,
        "queries_max": max(queries) if queries else None,
        "rows_touched_median": statistics.median(rows) if rows else None,
    }


def changed_rows(
    operation: operations.Operation, method: str, target: dict, *, using: str,
) -> dict:
    """
    How many rows the operation actually writes, on one extra **untimed**
    repeat (D63).

    For MPTT this is the number that explains the timings: a move rewrites
    every ``lft``/``rght`` to the right of the subtree, which is most of the
    table. Measured by snapshotting the interval columns before and after;
    for CTE the snapshot is the parent and position columns.
    """
    model = MODELS[method]
    fields = ("pk", "parent_id", "position")
    if method == MPTT:
        fields = ("pk", "parent_id", "position", "tree_id", "lft", "rght", "level")

    def snapshot() -> dict:
        return {
            row[0]: row[1:]
            for row in model.objects.using(using).values_list(*fields)
        }

    before = snapshot()
    with transaction.atomic(using=using):
        operation.run(method, target, using)
        after = snapshot()
        transaction.set_rollback(True, using=using)

    changed = sum(1 for pk, values in after.items() if before.get(pk) != values)
    return {
        "rows_before": len(before),
        "rows_after": len(after),
        "rows_changed": changed,
        "rows_inserted": max(0, len(after) - len(before)),
        "rows_deleted": max(0, len(before) - len(after)),
        "columns": list(fields[1:]),
    }


def run_cell(
    spec: generator.TreeSpec,
    operation: operations.Operation,
    *,
    using: str,
    warmups: int,
    repeats: int,
    budget: Budget,
    seed: int,
    target_list: list[dict],
    log=print,
) -> dict:
    """Both methods on one (shape, size, operation), and the ratio between them."""
    entry: dict = {
        "shape": spec.shape,
        "size": spec.size,
        "operation": operation.name,
        "kind": operation.kind,
        "label": operation.label,
        "targets": len(target_list),
        "methods": {},
    }
    for method in METHODS:
        entry["methods"][method] = measure(
            operation, method, target_list,
            using=using, warmups=warmups, repeats=repeats, budget=budget,
        )
        if entry["methods"][method]["status"] == "ok" and target_list and operation.mutates:
            entry["methods"][method]["changed"] = changed_rows(
                operation, method, target_list[0], using=using,
            )

    left, right = entry["methods"][MPTT], entry["methods"][CTE]
    if left["status"] == "ok" and right["status"] == "ok":
        entry["ratio"] = ratio_interval(left["timings"], right["timings"], seed=seed)
    else:
        entry["ratio"] = {"ratio": None, "ci_low": None, "ci_high": None, "replicates": 0}
        entry["ratio"]["reason"] = ", ".join(
            f"{method}: {entry['methods'][method]['status']}"
            for method in METHODS if entry["methods"][method]["status"] != "ok"
        )
    entry["verdict"] = (
        TIMEOUT if TIMEOUT in (left["status"], right["status"]) else verdict_of(entry["ratio"])
    )
    log(f"    {operation.name:16s} mptt={_ms(left)} cte={_ms(right)} "
        f"ρ={_value(entry['ratio'].get('ratio'))} → {entry['verdict']}")
    return entry


def _ms(entry: dict) -> str:
    if entry.get("status") != "ok":
        return entry.get("status", "—")
    return f"{entry['seconds']['median'] * 1000:.2f}ms"


def _value(value) -> str:
    return "—" if value is None else f"{value:.3f}"


# ---------------------------------------------------------------------------
# The parallel phase
# ---------------------------------------------------------------------------

def run_parallel(
    spec: generator.TreeSpec,
    *,
    using: str,
    workers: tuple[int, ...],
    seconds: float,
    repeats: int,
    seed: int,
    allow_rebuild: bool = True,
    log=print,
) -> list[dict]:
    """
    The parallel writes of D63, in the two variants of D63a, with the tree
    rebuilt between repeats and the integrity checks run after each one.

    - **unlocked**, at every worker count: each method's own write path, which
      is what the storage method alone guarantees;
    - **locked**, at the highest worker count only: the platform's path, with
      ``pg_advisory_xact_lock`` around the check and the write. D63's
      integrity condition is read from this variant.

    The tree is rebuilt from the generator rather than repaired, so every
    repeat starts from the documented tree; the integrity result is read from
    the tree the writers left behind, before that rebuild.
    """
    out: list[dict] = []
    combinations = [(count, False) for count in workers]
    if workers:
        combinations += [(max(workers), True)]
    for count, locked in combinations:
        for method in METHODS:
            phases: list[dict] = []
            checks: list[dict] = []
            for repeat in range(repeats):
                generator.build(spec, method=method, using=using)
                phase = parallel.run_phase(
                    method=method, using=using, workers=count, seconds=seconds,
                    seed=seed + repeat, node_count=spec.size, locked=locked,
                )
                phase["repeat"] = repeat
                phases.append(phase)
                checks.append(integrity.check(
                    method, using=using, allow_rebuild=allow_rebuild,
                ))
            throughput = [phase["throughput"] for phase in phases if phase["throughput"]]
            out.append({
                "shape": spec.shape,
                "size": spec.size,
                "method": method,
                "workers": count,
                "variant": parallel.LOCKED if locked else parallel.UNLOCKED,
                "seconds": seconds,
                "repeats": repeats,
                "throughput_median": round(statistics.median(throughput), 3) if throughput else None,
                "throughput_min": round(min(throughput), 3) if throughput else None,
                "throughput_max": round(max(throughput), 3) if throughput else None,
                "latency_median": quantile(
                    [phase["latency_median"] for phase in phases if phase["latency_median"]], 0.5,
                ),
                "latency_p95": max(
                    (phase["latency_p95"] for phase in phases if phase["latency_p95"]),
                    default=None,
                ),
                "errors": _merge_errors(phases),
                "integrity": checks,
                "integrity_passed": all(entry["passed"] for entry in checks),
                "phases": phases,
            })
            last = out[-1]
            log(f"    parallel {method:4s} ×{count} {last['variant']:8s}: "
                f"{_value(last['throughput_median'])} op/s, "
                f"errors {sum(last['errors'].values())}, "
                f"integrity {'ok' if last['integrity_passed'] else 'BUZILDI'}")
    return out


def _merge_errors(phases: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for phase in phases:
        for name, count in phase["errors"].items():
            out[name] = out.get(name, 0) + count
    return out


def parallel_ratios(entries: list[dict], *, seed: int) -> list[dict]:
    """
    CTE's throughput against MPTT's, per (shape, size, workers).

    Oriented like the operation ratios — "how many times CTE's throughput is
    MPTT's" — so that above 1 means CTE is ahead in both tables.
    """
    out: list[dict] = []
    grouped: dict[tuple, dict[str, dict]] = {}
    for entry in entries:
        grouped.setdefault(
            (entry["shape"], entry["size"], entry["workers"], entry["variant"]), {},
        )[entry["method"]] = entry
    for (shape, size, workers, variant), pair in grouped.items():
        mptt, cte = pair.get(MPTT), pair.get(CTE)
        if not mptt or not cte:
            continue
        left = [phase["throughput"] for phase in cte["phases"] if phase["throughput"]]
        right = [phase["throughput"] for phase in mptt["phases"] if phase["throughput"]]
        entry = ratio_interval(left, right, seed=seed) if len(left) == len(right) else {
            "ratio": None, "ci_low": None, "ci_high": None, "replicates": 0,
        }
        out.append({
            "shape": shape,
            "size": size,
            "workers": workers,
            "variant": variant,
            "throughput_cte": cte["throughput_median"],
            "throughput_mptt": mptt["throughput_median"],
            "ratio": entry.get("ratio"),
            "ci_low": entry.get("ci_low"),
            "ci_high": entry.get("ci_high"),
            "verdict": verdict_of(entry),
            "integrity_mptt": mptt["integrity_passed"],
            "integrity_cte": cte["integrity_passed"],
            "errors_mptt": sum(mptt["errors"].values()),
            "errors_cte": sum(cte["errors"].values()),
        })
    return out


# ---------------------------------------------------------------------------
# The reading rule
# ---------------------------------------------------------------------------

def reading(cells: list[dict], parallel_rows: list[dict]) -> dict:
    """
    D63's reading rule, applied: writes must be faster everywhere, reads must
    not be more than ``READ_TOLERANCE`` times slower anywhere, and CTE's
    integrity must hold after every parallel phase.
    """
    writes = [cell for cell in cells if cell["kind"] == operations.WRITE]
    reads = [cell for cell in cells if cell["kind"] == operations.READ]

    # A timed-out cell has no number, so it cannot refute the claim either; it
    # lands in not_computed below and makes the whole reading "hisoblanmadi".
    write_failures = [
        _where(cell) for cell in writes
        if cell["verdict"] in (MPTT_FASTER, COMPARABLE)
    ]
    read_failures = [
        _where(cell) for cell in reads
        if cell["verdict"] == MPTT_FASTER
        and (cell["ratio"].get("ratio") or 1.0) < 1.0 / READ_TOLERANCE
    ]
    # D63a: the integrity condition is read from the locked variant, because
    # that is the path the platform takes. The unlocked rows stay in the table
    # and are read descriptively.
    integrity_failures = [
        f"{row['shape']}/{row['size']}/×{row['workers']}"
        for row in parallel_rows
        if row.get("variant") == parallel.LOCKED and not row["integrity_cte"]
    ]
    not_computed = [
        _where(cell) for cell in cells if cell["verdict"] in (TIMEOUT, NOT_COMPUTED)
    ]

    if not writes or not reads:
        status = NOT_COMPUTED
    elif write_failures or read_failures or integrity_failures:
        status = NOT_SUPPORTED
    elif not_computed:
        # Every claim that was measured held, but not every cell produced a
        # number, so the rule of D61/D63 says "hisoblanmadi", not "supported".
        status = NOT_COMPUTED
    else:
        status = SUPPORTED

    return {
        "status": status,
        "rule": (
            "H4 qo‘llab-quvvatlandi: to‘rtta yozish amalining har birida, har bir "
            "shakl va hajmda “CTE tezroq”; o‘qishda hech bir katakda CTE 1,5 "
            "barobardan ko‘proq sekin emas; parallel yozishdan keyin CTE da "
            "yaxlitlik buzilishi yo‘q (D63)"
        ),
        "read_tolerance": READ_TOLERANCE,
        "write_cells": len(writes),
        "read_cells": len(reads),
        "write_failures": write_failures,
        "read_failures": read_failures,
        "integrity_failures": integrity_failures,
        "not_computed": not_computed,
    }


def _where(cell: dict) -> str:
    return f"{cell['operation']}@{cell['shape']}/{cell['size']}"


# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------

class Checkpoint:
    """
    Finished (shape, size) blocks, so an interrupted run resumes.

    Keyed by the digest of commit, seed, sizes, repeats, warm-ups, timeout and
    the parallel settings; the key is stored and compared, so anything that
    would change a number starts afresh. Nothing here is a result (D48):
    ``results/`` is written only at the end.
    """

    def __init__(self, root: str | Path, key: dict, *, enabled: bool, log=print) -> None:
        self.key = key
        self.enabled = enabled
        self.digest = hashlib.sha256(
            json.dumps(key, sort_keys=True).encode()
        ).hexdigest()[:16]
        self.directory = Path(root) / f"tree-bench-{self.digest}"
        self.resumed = 0
        self.log = log

    def _matches(self) -> bool:
        stored = self.directory / "key.json"
        if not stored.exists():
            return False
        return json.loads(stored.read_text(encoding="utf-8")) == self.key

    def load(self, name: str):
        if not self.enabled or not self._matches():
            return None
        path = self.directory / f"{name}.json"
        if not path.exists():
            return None
        self.resumed += 1
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, name: str, payload) -> None:
        if not self.enabled:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        stored = self.directory / "key.json"
        if not stored.exists():
            stored.write_text(json.dumps(self.key, sort_keys=True), encoding="utf-8")
        temporary = self.directory / f"{name}.tmp"
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        temporary.replace(self.directory / f"{name}.json")

    def payload(self) -> dict:
        return {"enabled": self.enabled, "key_digest": self.digest, "resumed_items": self.resumed}


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def run(
    *,
    using: str,
    shapes: tuple[str, ...],
    sizes: tuple[int, ...],
    workers: tuple[int, ...],
    warmups: int,
    repeats: int,
    timeout: float,
    parallel_seconds: float,
    parallel_repeats: int,
    seed: int,
    checkpoint: Checkpoint,
    quick: bool,
    log=print,
) -> dict:
    """Every cell, the parallel phase, and the verdict."""
    budget = Budget(timeout=timeout)
    cells: list[dict] = []
    trees: list[dict] = []
    parallel_rows: list[dict] = []

    for shape in shapes:
        for size in sizes:
            spec = generator.TreeSpec(shape=shape, size=size, seed=seed)
            stored = checkpoint.load(f"block-{spec.key()}")
            if stored is not None:
                log(f"  {shape}/{size}: resumed from the checkpoint")
                cells.extend(stored["cells"])
                trees.extend(stored["trees"])
                parallel_rows.extend(stored["parallel"])
                continue

            log(f"  {shape}/{size}: building both tables")
            built = generator.build_all(spec, using=using)
            trees.extend(built.values())
            target_list = operations.targets(spec, count=warmups + repeats)
            if not target_list:
                log(f"  {shape}/{size}: no usable target, skipped")
                continue

            block_cells = [
                run_cell(
                    spec, operation, using=using, warmups=warmups, repeats=repeats,
                    budget=budget, seed=seed, target_list=target_list, log=log,
                )
                for operation in operations.OPERATIONS
            ]
            block_parallel = run_parallel(
                spec, using=using, workers=workers, seconds=parallel_seconds,
                repeats=parallel_repeats, seed=seed,
                allow_rebuild=size <= integrity.REBUILD_LIMIT, log=log,
            )
            cells.extend(block_cells)
            parallel_rows.extend(block_parallel)
            checkpoint.save(f"block-{spec.key()}", {
                "cells": block_cells,
                "trees": list(built.values()),
                "parallel": block_parallel,
            })

    ratios = parallel_ratios(parallel_rows, seed=seed)
    return {
        "cells": cells,
        "trees": trees,
        "parallel": parallel_rows,
        "parallel_ratios": ratios,
        "reading": reading(cells, ratios),
        "settings": {
            "shapes": list(shapes),
            "sizes": list(sizes),
            "parallel_workers": list(workers),
            "warmups": warmups,
            "repeats": repeats,
            "timeout": timeout,
            "parallel_seconds": parallel_seconds,
            "parallel_repeats": parallel_repeats,
            "replicates": REPLICATES,
            "confidence_percent": int(round(CONFIDENCE * 100)),
            "seed": seed,
            "read_tolerance": READ_TOLERANCE,
            "quick": quick,
            "rebuild_limit": integrity.REBUILD_LIMIT,
            "deep_recursion_limit": operations.DEEP_RECURSION_LIMIT,
        },
    }


def csv_rows(document: dict) -> list[list]:
    """Every repeat's raw timing, for ``measurements.csv``."""
    rows: list[list] = [[
        "shape", "size", "operation", "kind", "method", "repeat", "seconds", "status",
    ]]
    for cell in document["cells"]:
        for method, entry in cell["methods"].items():
            if entry.get("status") != "ok":
                rows.append([
                    cell["shape"], cell["size"], cell["operation"], cell["kind"],
                    method, "", "", entry.get("status", "error"),
                ])
                continue
            for index, value in enumerate(entry["timings"]):
                rows.append([
                    cell["shape"], cell["size"], cell["operation"], cell["kind"],
                    method, index, value, "ok",
                ])
    for row in document["parallel"]:
        for phase in row["phases"]:
            rows.append([
                row["shape"], row["size"], f"parallel_{row['workers']}", "write",
                row["method"], phase["repeat"], phase["throughput"], "ops_per_second",
            ])
    return rows


__all__ = [
    "run", "run_cell", "run_parallel", "measure", "changed_rows", "reading",
    "ratio_interval", "verdict_of", "summarise", "quantile", "csv_rows",
    "Budget", "Checkpoint", "DEFAULT_SHAPES", "DEFAULT_SIZES", "DEFAULT_WORKERS",
    "QUICK_SIZES", "QUICK_WORKERS", "CTE_FASTER", "MPTT_FASTER", "COMPARABLE",
    "TIMEOUT", "SUPPORTED", "NOT_SUPPORTED", "NOT_COMPUTED", "READ_TOLERANCE",
]
