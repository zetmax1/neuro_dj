"""
benchmarks/parallel.py — concurrent writes against both methods (D63).

2, 4 and 8 processes, each with **its own** connection, writing for a fixed
duration: a mix of appending a leaf and moving a branch, which is the pair of
operations that makes MPTT shift intervals. What comes out is throughput and
latency, and — the part that matters more — a tree that the integrity checks
of :mod:`benchmarks.integrity` then read.

Processes rather than threads, because a connection is per process in Django
and because the GIL would otherwise serialise exactly what is being measured.
``fork`` plus ``connections.close_all()`` in the child: a forked child that
inherits its parent's socket and uses it corrupts both sides, so the first
thing a worker does is drop the inherited connections and let Django open its
own.

Errors are expected here and are part of the result, not a crash: MPTT raises
``InvalidMove`` when a move would put a node inside its own subtree (two
workers can arrange that between a read and a write), and Postgres raises on
deadlock. Each is counted by type.
"""

from __future__ import annotations

import multiprocessing
import os
import random
import time
from dataclasses import dataclass, field

from benchmarks.models import MODELS, MPTT

# What a worker does, in turn: half the operations are inserts, half moves.
APPEND = "append_leaf"
MOVE = "move_branch"

# The two variants of D63a.
UNLOCKED = "unlocked"
LOCKED = "locked"

# curriculum.services.kb.KB_LOCK_KEY — the platform's single-key lock space,
# restated here so the benchmark does not import the curriculum app (its
# models are guarded and irrelevant to this measurement).
LOCK_KEY = 0x4E4C5F4B42


@dataclass
class WorkerResult:
    """One worker's share of the phase."""

    worker: int
    operations: int = 0
    appended: int = 0
    moved: int = 0
    latencies: list[float] = field(default_factory=list)
    errors: dict[str, int] = field(default_factory=dict)


def _worker(payload: tuple) -> dict:
    """One process: write until the deadline, then report what it managed."""
    method, using, worker, deadline, seed, node_count, locked, statement_timeout = payload

    from django.db import connections, transaction

    from benchmarks import operations, runner

    connections.close_all()
    runner.apply_statement_timeout(using, statement_timeout)
    model = MODELS[method]
    rng = random.Random(seed + worker)
    result = WorkerResult(worker=worker)

    while time.monotonic() < deadline:
        action = APPEND if result.operations % 2 == 0 else MOVE
        started = time.perf_counter()
        try:
            with transaction.atomic(using=using):
                if locked:
                    # The platform's path: structural writes are serialised by
                    # one advisory lock (BB9/D30, curriculum.services.kb) and
                    # the lock is released when the transaction ends.
                    with connections[using].cursor() as cursor:
                        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [LOCK_KEY])
                if action == APPEND:
                    parent = rng.randrange(1, node_count + 1)
                    model.objects.using(using).create(
                        name=f"w{worker}", parent_id=parent, position=rng.randrange(1_000_000),
                    )
                    result.appended += 1
                else:
                    node_pk = rng.randrange(2, node_count + 1)
                    target_pk = rng.randrange(1, node_count + 1)
                    node = model.objects.using(using).filter(pk=node_pk).first()
                    target = model.objects.using(using).filter(pk=target_pk).first()
                    if node is None or target is None or node.pk == target.pk:
                        result.errors["Skipped"] = result.errors.get("Skipped", 0) + 1
                        continue
                    if method == MPTT:
                        node.move_to(target, position="last-child")
                    else:
                        # D63a: the CTE path checks Y1, as the platform does.
                        operations.check_y1(model, node.pk, target.pk, using=using)
                        node.parent_id = target.pk
                        node.position = rng.randrange(1_000_000)
                        node.save(update_fields=["parent", "position"], using=using)
                    result.moved += 1
        except Exception as error:  # noqa: BLE001 - every failure is a counted result
            name = type(error).__name__
            result.errors[name] = result.errors.get(name, 0) + 1
            continue
        # Latency covers the operations that went through: a deadlock's
        # latency is the time until it was refused, which belongs with the
        # error count rather than in the latency distribution.
        result.latencies.append(time.perf_counter() - started)
        result.operations += 1

    connections.close_all()
    return {
        "worker": result.worker,
        "pid": os.getpid(),
        "operations": result.operations,
        "appended": result.appended,
        "moved": result.moved,
        "latencies": result.latencies,
        "errors": result.errors,
    }


def run_phase(
    *,
    method: str,
    using: str,
    workers: int,
    seconds: float,
    seed: int,
    node_count: int,
    locked: bool = False,
    statement_timeout: int = 0,
) -> dict:
    """
    One (method, worker count) phase. The parent closes its own connections
    before forking so no child inherits a live socket.
    """
    import gc

    from django.db import connections

    # D63f: the children copy the parent's heap as they write to it, so the
    # parent gives back what it can before forking.
    connections.close_all()
    gc.collect()
    deadline = time.monotonic() + seconds
    payloads = [
        (method, using, worker, deadline, seed, node_count, locked, statement_timeout)
        for worker in range(workers)
    ]
    started = time.perf_counter()
    context = multiprocessing.get_context("fork")
    with context.Pool(processes=workers) as pool:
        results = pool.map(_worker, payloads)
    elapsed = time.perf_counter() - started

    latencies = sorted(value for entry in results for value in entry["latencies"])
    operations = sum(entry["operations"] for entry in results)
    errors: dict[str, int] = {}
    for entry in results:
        for name, count in entry["errors"].items():
            errors[name] = errors.get(name, 0) + count

    return {
        "method": method,
        "workers": workers,
        "variant": LOCKED if locked else UNLOCKED,
        "seconds_requested": seconds,
        "seconds_elapsed": round(elapsed, 3),
        "operations": operations,
        "appended": sum(entry["appended"] for entry in results),
        "moved": sum(entry["moved"] for entry in results),
        "throughput": round(operations / elapsed, 3) if elapsed else None,
        "latency_median": _quantile(latencies, 0.5),
        "latency_p95": _quantile(latencies, 0.95),
        "errors": errors,
        "error_count": sum(errors.values()),
        "per_worker_operations": [entry["operations"] for entry in results],
    }


def _quantile(ordered: list[float], share: float) -> float | None:
    if not ordered:
        return None
    position = share * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    value = ordered[low] + (ordered[high] - ordered[low]) * (position - low)
    return round(value, 6)


__all__ = ["run_phase", "APPEND", "MOVE", "MPTT", "LOCKED", "UNLOCKED", "LOCK_KEY"]
