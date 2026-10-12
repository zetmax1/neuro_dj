"""
benchmarks/operations.py — the operations H4 is about (D63).

Six operations, each written the way the library documents it, because what
is being compared is what an application would actually write:

| operation | MPTT | CTE |
|---|---|---|
| read branch | ``get_descendants()`` | ``descendants()`` |
| read ancestors | ``get_ancestors()`` | ``ancestors()`` |
| append leaf | ``create(parent_id=…)`` | ``create(parent_id=…, position=max+1)`` |
| insert leftmost | ``insert_at(…, "first-child")`` | ``create(…, position=min−1)`` |
| move branch | ``move_to(target, "last-child")`` | ``parent_id = target; save()`` |
| delete branch | ``delete()`` | ``delete()`` |

Both read operations fetch the node first and then its branch, so neither
method is handed the node for free. Both insert operations give CTE an extra
aggregate query to find the sibling position — that is a real property of the
adjacency list (the order lives in a column, not in the encoding) and it shows
up in the SQL-count column rather than being hidden by pretending position
does not matter.

The targets come from :func:`targets`, which draws them from the generated
parent list with a seed, so **the same node is used for the same repeat of
both methods** (D63's pairing). A move needs a destination outside the moved
subtree or mptt refuses it (``InvalidMove``), so the pair is chosen here where
the tree shape is known, not by chance at run time.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from typing import Callable

from django.db.models import Max, Min

from benchmarks import generator
from benchmarks.models import CTE, MODELS, MPTT

READ = "read"
WRITE = "write"

# D63b: Django's CASCADE collector recurses once per tree level, so a deep
# chain needs more than the default 1 000 frames. CPython 3.11+ does not grow
# the C stack for Python-to-Python calls, so raising the limit is safe here;
# the value is well above the largest tree the benchmark builds.
DEEP_RECURSION_LIMIT = 400_000


@dataclass(frozen=True)
class Operation:
    """One measured operation, in table order."""

    name: str
    kind: str
    label: str
    run: Callable[[str, dict, str], int]

    @property
    def mutates(self) -> bool:
        return self.kind == WRITE


def _node(method: str, pk: int, *, using: str):
    return MODELS[method].objects.using(using).get(pk=pk)


def _read_branch(method: str, target: dict, using: str) -> int:
    node = _node(method, target["node"], using=using)
    branch = node.get_descendants() if method == MPTT else node.descendants()
    return len(list(branch))


def _read_ancestors(method: str, target: dict, using: str) -> int:
    node = _node(method, target["node"], using=using)
    chain = node.get_ancestors() if method == MPTT else node.ancestors()
    return len(list(chain))


def _append_leaf(method: str, target: dict, using: str) -> int:
    model = MODELS[method]
    parent = target["node"]
    if method == MPTT:
        model.objects.using(using).create(name="appended", parent_id=parent)
        return 1
    last = (
        model.objects.using(using).filter(parent_id=parent).aggregate(value=Max("position"))
    )["value"]
    model.objects.using(using).create(
        name="appended", parent_id=parent, position=0 if last is None else last + 1,
    )
    return 1


def _insert_leftmost(method: str, target: dict, using: str) -> int:
    model = MODELS[method]
    parent = target["node"]
    if method == MPTT:
        node = model(name="leftmost")
        node.insert_at(
            _node(method, parent, using=using), position="first-child", save=True,
            allow_existing_pk=False,
        )
        return 1
    first = (
        model.objects.using(using).filter(parent_id=parent).aggregate(value=Min("position"))
    )["value"]
    model.objects.using(using).create(
        name="leftmost", parent_id=parent, position=0 if first is None else first - 1,
    )
    return 1


class Y1Violation(RuntimeError):
    """A move would put a node inside its own subtree (the CTE path's check)."""


def check_y1(model, node_pk: int, destination_pk: int, *, using: str) -> None:
    """
    The platform's Y1 check, in the platform's words (D63a).

    ``curriculum/services/kb.py`` writes exactly this expression before a
    structural move, so the benchmark's CTE move does too: mptt's ``move_to``
    performs its own check and comparing a validated write against an
    unvalidated one would measure the missing check, not the storage method.
    One extra query, visible in the SQL column.
    """
    if model.objects.using(using).ancestors(destination_pk, include_self=True).filter(
        pk=node_pk,
    ).exists():
        raise Y1Violation(f"{node_pk} cannot be moved under {destination_pk} (Y1)")


def _move_branch(method: str, target: dict, using: str) -> int:
    model = MODELS[method]
    node = _node(method, target["node"], using=using)
    if method == MPTT:
        node.move_to(_node(method, target["destination"], using=using), position="last-child")
        return 1
    check_y1(model, node.pk, target["destination"], using=using)
    last = (
        model.objects.using(using)
        .filter(parent_id=target["destination"])
        .aggregate(value=Max("position"))
    )["value"]
    node.parent_id = target["destination"]
    node.position = 0 if last is None else last + 1
    node.save(update_fields=["parent", "position"], using=using)
    return 1


def _delete_branch(method: str, target: dict, using: str) -> int:
    """
    ``delete()``, with Python's recursion limit raised for the duration.

    Django's cascade collector walks a self-referencing tree one level per
    frame, so deleting a branch of the deep chain exceeds the default limit of
    1 000 — in **both** methods, because the collector belongs to Django and
    not to either storage method (measured: at 1 000 nodes both raised
    ``RecursionError``; with the limit raised, a 100 000-deep chain deletes in
    about 51 s, inside the per-repeat budget). The limit is restored
    afterwards and the change is recorded in the metrics (D63b).
    """
    node = _node(method, target["node"], using=using)
    previous = sys.getrecursionlimit()
    sys.setrecursionlimit(max(previous, DEEP_RECURSION_LIMIT))
    try:
        deleted, _per_model = node.delete(using=using)
    finally:
        sys.setrecursionlimit(previous)
    return deleted


OPERATIONS: tuple[Operation, ...] = (
    Operation("read_branch", READ, "shoxni o‘qish", _read_branch),
    Operation("read_ancestors", READ, "ajdodlarni o‘qish", _read_ancestors),
    Operation("append_leaf", WRITE, "oxiriga barg qo‘shish", _append_leaf),
    Operation("insert_leftmost", WRITE, "eng chapga barg qo‘shish", _insert_leftmost),
    Operation("move_branch", WRITE, "shoxni ko‘chirish", _move_branch),
    Operation("delete_branch", WRITE, "shoxni o‘chirish", _delete_branch),
)
BY_NAME = {operation.name: operation for operation in OPERATIONS}
READ_OPERATIONS = tuple(op.name for op in OPERATIONS if op.kind == READ)
WRITE_OPERATIONS = tuple(op.name for op in OPERATIONS if op.kind == WRITE)


def targets(spec: generator.TreeSpec, *, count: int) -> list[dict]:
    """
    ``count`` targets for the cell, identical for both methods (D63).

    Each target is a node that is not the root and has at least one child —
    "move this branch", not "move this leaf" — together with a destination
    outside its own subtree. On a deep chain almost every node is an ancestor
    of almost every other, so the destination search walks up from a node near
    the top; if no destination exists at all (a two-node tree), the target is
    dropped and the cell reports how many it had.
    """
    parent_list = generator.parents(spec)
    children = generator.children_of(parent_list)
    depth = generator.depth_of(parent_list)
    internal = [
        index for index in range(1, len(parent_list)) if children[index]
    ] or list(range(1, len(parent_list)))
    if not internal:
        return []

    rng = random.Random(spec.seed + 977)
    out: list[dict] = []
    for _ in range(count):
        node = internal[rng.randrange(len(internal))]
        destination = _destination(node, parent_list, depth, rng)
        if destination is None:
            continue
        out.append({
            "node": node + 1,              # pk = index + 1 (generator.build)
            "destination": destination + 1,
            "depth": depth[node],
            "children": len(children[node]),
        })
    return out


def _destination(node: int, parent_list: list[int | None], depth: list[int], rng) -> int | None:
    """A node that is neither ``node`` nor one of its descendants."""
    size = len(parent_list)
    for _ in range(32):
        candidate = rng.randrange(size)
        if candidate != node and not _is_descendant(candidate, node, parent_list):
            return candidate
    # A deep chain: everything below the node is a descendant, so go up.
    walk = parent_list[node]
    while walk is not None:
        if walk != node:
            return walk
        walk = parent_list[walk]
    return None


def _is_descendant(candidate: int, node: int, parent_list: list[int | None]) -> bool:
    walk: int | None = candidate
    while walk is not None:
        if walk == node:
            return True
        walk = parent_list[walk]
    return False


__all__ = [
    "Operation", "OPERATIONS", "BY_NAME", "READ", "WRITE", "Y1Violation", "check_y1",
    "READ_OPERATIONS", "WRITE_OPERATIONS", "targets", "CTE", "MPTT",
    "DEEP_RECURSION_LIMIT",
]
