"""
benchmarks/generator.py — the seeded trees of H4 (D63).

Three shapes, three sizes, one parent list. Both storage methods are built
from the **same** parent list, so what the benchmark compares is the storage
method and not two different trees; the list's sha256 is the identity of the
input, which is what a benchmark has instead of a data file (D48's rule,
applied to generated input).

- **course-like** — four levels (course → section → subsection → topic),
  filled breadth-first with the smallest branching factor that fits the size.
  This is the shape the platform actually holds, and it is wide: the last
  level carries almost every node.
- **deep chain** — one child per node, so the depth is the size. The shape a
  recursive CTE is supposed to be bad at and an interval encoding good at.
- **random** — each node's parent is drawn uniformly from the nodes already
  placed, which gives a broad depth distribution and no regularity to exploit.

The tree is written in **one** bulk insert per method, with the primary keys
assigned here (node *i* gets pk *i + 1*) so a parent is known before its
children are written. MPTT's interval fields are computed in Python by
:func:`intervals` rather than through ``rebuild()``: a 100 000-node rebuild
walks the tree one query at a time, and the build is not one of the measured
operations. ``test_generator.py`` pins that function against mptt's own
``rebuild()``, so the shortcut is checked rather than trusted.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from django.db import connections, transaction

from benchmarks.models import CTE, METHODS, MPTT, MODELS, Shape

COURSE_LIKE_LEVELS = 4


@dataclass(frozen=True)
class TreeSpec:
    """One cell's tree: shape, size and seed."""

    shape: str
    size: int
    seed: int

    def key(self) -> str:
        return f"{self.shape}-{self.size}-{self.seed}"


def parents(spec: TreeSpec) -> list[int | None]:
    """
    The parent index of every node, ``None`` for the root.

    Deterministic in (shape, size, seed): the same spec gives the same tree on
    any machine, which is what makes a checkpoint and a re-run comparable.
    """
    if spec.size < 1:
        raise ValueError(f"a tree needs at least one node, not {spec.size}")
    if spec.shape == Shape.DEEP_CHAIN:
        return [None, *range(spec.size - 1)]
    if spec.shape == Shape.COURSE_LIKE:
        return _course_like(spec.size)
    if spec.shape == Shape.RANDOM:
        rng = random.Random(spec.seed)
        return [None, *(rng.randrange(index) for index in range(1, spec.size))]
    raise ValueError(f"unknown shape {spec.shape!r}; choose from {[s.value for s in Shape]}")


def _course_like(size: int) -> list[int | None]:
    """Four levels, filled breadth-first with the smallest branching factor that fits."""
    branching = 2
    while _capacity(branching) < size:
        branching += 1

    out: list[int | None] = [None]
    level = [0]
    while len(out) < size and len(level) > 0:
        nxt: list[int] = []
        for parent in level:
            for _ in range(branching):
                if len(out) >= size:
                    break
                nxt.append(len(out))
                out.append(parent)
            if len(out) >= size:
                break
        level = nxt
    return out


def _capacity(branching: int) -> int:
    return sum(branching ** level for level in range(COURSE_LIKE_LEVELS))


def digest(parent_list: list[int | None]) -> str:
    """sha256 of the parent list — the generated input's identity (D48)."""
    text = ",".join("" if parent is None else str(parent) for parent in parent_list)
    return hashlib.sha256(text.encode()).hexdigest()


def depth_of(parent_list: list[int | None]) -> list[int]:
    """Depth of every node (0 for the root); the parent always precedes it."""
    out = [0] * len(parent_list)
    for index, parent in enumerate(parent_list):
        if parent is not None:
            out[index] = out[parent] + 1
    return out


def children_of(parent_list: list[int | None]) -> list[list[int]]:
    out: list[list[int]] = [[] for _ in parent_list]
    for index, parent in enumerate(parent_list):
        if parent is not None:
            out[parent].append(index)
    return out


def intervals(parent_list: list[int | None]) -> list[tuple[int, int, int, int]]:
    """
    MPTT's ``(tree_id, lft, rght, level)`` for every node, iteratively.

    One tree, so ``tree_id`` is 1 throughout; ``lft``/``rght`` are the preorder
    interval of the subtree, with children visited in index order — which is
    the insertion order the tables are written in and therefore the sibling
    order both methods see.
    """
    children = children_of(parent_list)
    depth = depth_of(parent_list)
    out: list[tuple[int, int, int, int]] = [(1, 0, 0, 0)] * len(parent_list)
    counter = 0
    # (node, False) = enter, (node, True) = leave.
    stack: list[tuple[int, bool]] = [(0, False)] if parent_list else []
    left: dict[int, int] = {}
    while stack:
        node, leaving = stack.pop()
        if not leaving:
            counter += 1
            left[node] = counter
            stack.append((node, True))
            for child in reversed(children[node]):
                stack.append((child, False))
            continue
        counter += 1
        out[node] = (1, left[node], counter, depth[node])
    return out


def build(spec: TreeSpec, *, method: str, using: str) -> dict:
    """
    Write the tree into one method's table, replacing whatever was there.

    Only this app's two tables are ever touched, and only in the benchmark
    alias (D63). The returned metadata is recorded with the results: the build
    is not a measured operation, but how long it took and how many rows it
    wrote belong in the record.
    """
    import time

    parent_list = parents(spec)
    model = MODELS[method]
    started = time.perf_counter()
    truncate(method, using=using)

    rows = []
    if method == MPTT:
        fields = intervals(parent_list)
        for index, parent in enumerate(parent_list):
            tree_id, lft, rght, level = fields[index]
            rows.append(model(
                id=index + 1, name=f"n{index}", position=index,
                parent_id=None if parent is None else parent + 1,
                tree_id=tree_id, lft=lft, rght=rght, level=level,
            ))
    else:
        for index, parent in enumerate(parent_list):
            rows.append(model(
                id=index + 1, name=f"n{index}", position=index,
                parent_id=None if parent is None else parent + 1,
            ))

    with transaction.atomic(using=using):
        model.objects.using(using).bulk_create(rows, batch_size=5000)
    _restart_sequence(model, using=using, next_value=len(parent_list) + 1)
    seconds = time.perf_counter() - started

    return {
        "method": method,
        "shape": spec.shape,
        "size": spec.size,
        "seed": spec.seed,
        "nodes": len(parent_list),
        "sha256": digest(parent_list),
        "max_depth": max(depth_of(parent_list)),
        "build_seconds": round(seconds, 3),
    }


def truncate(method: str, *, using: str) -> None:
    """Empty one benchmark table. Nothing outside this app is named here (D63)."""
    model = MODELS[method]
    with connections[using].cursor() as cursor:
        cursor.execute(f'TRUNCATE TABLE "{model._meta.db_table}" RESTART IDENTITY')


def _restart_sequence(model, *, using: str, next_value: int) -> None:
    """
    Put the table's identity sequence past the keys the build assigned.

    The build sets primary keys explicitly, so the sequence still points at 1
    and the first measured insert would collide with the root.
    """
    with connections[using].cursor() as cursor:
        cursor.execute(
            "SELECT pg_get_serial_sequence(%s, %s)", [model._meta.db_table, "id"],
        )
        sequence = cursor.fetchone()[0]
        if sequence:
            cursor.execute(f"ALTER SEQUENCE {sequence} RESTART WITH {next_value}")


def build_all(spec: TreeSpec, *, using: str) -> dict[str, dict]:
    """Both methods' tables from one parent list, so they hold the same tree."""
    return {method: build(spec, method=method, using=using) for method in METHODS}


__all__ = [
    "TreeSpec", "parents", "digest", "depth_of", "children_of", "intervals",
    "build", "build_all", "truncate", "COURSE_LIKE_LEVELS", "CTE", "MPTT",
]
