"""
benchmarks/integrity.py — what has to still be true after parallel writes (D63).

A write benchmark that only measures speed answers half the question. MPTT's
intervals are a denormalisation: two concurrent inserts can each shift
``lft``/``rght`` from a stale read and leave a tree whose intervals no longer
describe the parent links. The adjacency list has no such second copy, so the
only thing that can break there is Y1 itself.

So after every parallel phase both methods are checked:

- **Y1** (both): no cycle in the parent chain, exactly one parentless node per
  tree, every parent present.
- **Intervals** (MPTT only): ``lft < rght`` everywhere, siblings' intervals do
  not overlap and a child's interval sits strictly inside its parent's,
  ``level`` equals the parent-chain length, and the stored intervals equal the
  ones recomputed from the parent links. That last check is the "compare with
  ``rebuild()``" of D63: for small trees it runs mptt's own ``rebuild()`` and
  compares; for large ones it compares against
  ``generator.intervals``-style recomputation, which ``test_generator.py``
  pins against ``rebuild()`` — a 100 000-node rebuild walks the tree one query
  at a time and would dominate the run. A **deep** tree takes that same
  recomputation whatever its size: ``rebuild()`` calls itself once per level,
  and a 10 000-deep chain exhausts the interpreter's frames (D63d).

A violation is **a result**: it is counted, named and reported, and the run
carries on (D63). Nothing here repairs the tree except the ``rebuild()`` the
small-tree branch performs, which happens after its comparison.
"""

from __future__ import annotations

import sys

from benchmarks.models import MODELS, MPTT
from benchmarks.operations import DEEP_RECURSION_LIMIT

# Above this many nodes the stored intervals are compared against a Python
# recomputation instead of mptt's rebuild() (see the module docstring).
REBUILD_LIMIT = 20_000

# And above this depth as well, whatever the size: mptt's rebuild() calls
# itself once per tree level (``mptt.managers._rebuild_helper``), so a deep
# chain exhausts the interpreter's frames long before the node count matters
# (D63d — it ended a full pass at the 10 000-deep chain). The recomputation is
# iterative and ``test_generator`` pins it against rebuild() itself.
REBUILD_DEPTH_LIMIT = 500


def parent_map(method: str, *, using: str) -> dict[int, int | None]:
    model = MODELS[method]
    return dict(model.objects.using(using).values_list("pk", "parent_id"))


def check_y1(method: str, *, using: str) -> dict:
    """No cycles, one root per tree, no dangling parent (D63)."""
    parents = parent_map(method, using=using)
    roots = sorted(pk for pk, parent in parents.items() if parent is None)
    dangling = sorted(
        pk for pk, parent in parents.items() if parent is not None and parent not in parents
    )

    # Iterative walk with memoised "known good" nodes: O(n) overall.
    safe: set[int] = set()
    cycles: list[int] = []
    for start in parents:
        path: list[int] = []
        seen: set[int] = set()
        node: int | None = start
        while node is not None and node in parents and node not in safe:
            if node in seen:
                cycles.append(node)
                break
            seen.add(node)
            path.append(node)
            node = parents[node]
        else:
            safe.update(path)
    return {
        "check": "y1",
        "nodes": len(parents),
        "roots": len(roots),
        "parentless": len(roots),
        "dangling_parents": len(dangling),
        "cycles": len(cycles),
        "cycle_nodes": sorted(set(cycles))[:10],
        "passed": len(cycles) == 0 and len(dangling) == 0 and len(roots) == 1,
    }


def recompute_intervals(parents: dict[int, int | None]) -> dict[int, tuple[int, int, int]]:
    """
    ``(lft, rght, level)`` per node from the parent links alone, children in
    primary-key order — the order both tables were built in.
    """
    children: dict[int | None, list[int]] = {}
    for pk, parent in parents.items():
        children.setdefault(parent, []).append(pk)
    for group in children.values():
        group.sort()

    out: dict[int, tuple[int, int, int]] = {}
    counter = 0
    for root in children.get(None, []):
        stack: list[tuple[int, int, bool]] = [(root, 0, False)]
        left: dict[int, int] = {}
        while stack:
            node, level, leaving = stack.pop()
            if not leaving:
                counter += 1
                left[node] = counter
                stack.append((node, level, True))
                for child in reversed(children.get(node, [])):
                    stack.append((child, level + 1, False))
                continue
            counter += 1
            out[node] = (left[node], counter, level)
    return out


def check_mptt_intervals(*, using: str, allow_rebuild: bool = True) -> dict:
    """The interval invariants, and the stored intervals against a recomputation."""
    model = MODELS[MPTT]
    rows = list(
        model.objects.using(using).values_list("pk", "parent_id", "tree_id", "lft", "rght", "level")
    )
    parents = {pk: parent for pk, parent, *_ in rows}
    stored = {pk: (lft, rght, level) for pk, _parent, _tree, lft, rght, level in rows}
    trees = {pk: tree for pk, _parent, tree, *_ in rows}

    depth = _depths(parents)
    inverted = sorted(pk for pk, (lft, rght, _level) in stored.items() if lft >= rght)

    # A child's interval must sit strictly inside its parent's, and that alone
    # rules out sibling overlap: siblings are both inside the parent and the
    # preorder numbering is unique, so an overlap shows up as a containment
    # failure or as a duplicate boundary.
    outside: list[int] = []
    for pk, parent in parents.items():
        if parent is None or parent not in stored:
            continue
        child_lft, child_rght, _ = stored[pk]
        parent_lft, parent_rght, _ = stored[parent]
        if not (parent_lft < child_lft and child_rght < parent_rght) or trees[pk] != trees[parent]:
            outside.append(pk)

    boundaries: dict[int, list[int]] = {}
    for pk, (lft, rght, _level) in stored.items():
        boundaries.setdefault(trees[pk], []).extend((lft, rght))
    duplicates = sum(
        len(values) - len(set(values)) for values in boundaries.values()
    )

    wrong_level = sorted(
        pk for pk, (_lft, _rght, level) in stored.items()
        if depth.get(pk) is not None and level != depth[pk]
    )

    deepest = max((value for value in depth.values() if value is not None), default=0)
    too_big = len(rows) > REBUILD_LIMIT
    too_deep = deepest > REBUILD_DEPTH_LIMIT
    if allow_rebuild and not too_big and not too_deep:
        # rebuild() lives on mptt's manager, not on the queryset, so the alias
        # is bound with db_manager rather than using(). The recursion limit is
        # raised around it as insurance (D63b, D63d): the helper recurses per
        # level and the depth check above is a bound, not a guarantee.
        previous = sys.getrecursionlimit()
        sys.setrecursionlimit(max(previous, DEEP_RECURSION_LIMIT))
        try:
            model.objects.db_manager(using).rebuild()
        finally:
            sys.setrecursionlimit(previous)
        after = dict(
            (pk, (lft, rght, level))
            for pk, lft, rght, level in model.objects.using(using).values_list(
                "pk", "lft", "rght", "level",
            )
        )
        source = "mptt rebuild()"
    else:
        after = recompute_intervals(parents)
        why = "too many nodes" if too_big else ("too deep" if too_deep else "rebuild not allowed")
        source = (
            f"recomputed from the parent links ({why}; "
            "test_generator pins it against rebuild())"
        )

    differing = sorted(pk for pk in stored if stored.get(pk) != after.get(pk))

    return {
        "check": "mptt_intervals",
        "nodes": len(rows),
        "lft_not_less_than_rght": len(inverted),
        "outside_parent_interval": len(outside),
        "duplicate_boundaries": duplicates,
        "wrong_level": len(wrong_level),
        "differs_from_rebuild": len(differing),
        "rebuild_source": source,
        "examples": {
            "inverted": inverted[:10],
            "outside": outside[:10],
            "wrong_level": wrong_level[:10],
            "differing": differing[:10],
        },
        "passed": not (inverted or outside or duplicates or wrong_level or differing),
    }


def _depths(parents: dict[int, int | None]) -> dict[int, int | None]:
    """
    Parent-chain length per node; ``None`` where the chain loops or dangles.

    Iterative: a deep chain is 100 000 nodes long, and a recursive walk of
    that would end the process rather than the function.
    """
    out: dict[int, int | None] = {}
    for first in parents:
        if first in out:
            continue
        path: list[int] = []          # path[0] = first, path[-1] = nearest the root
        seen: set[int] = set()
        node: int | None = first
        base: int | None = None       # depth of path[-1]'s parent, or None
        while True:
            if node is None:          # path[-1] is a root
                base = -1
                break
            if node in out:           # the rest of the chain is already known
                base = out[node]
                break
            if node in seen or node not in parents:
                base = None           # a loop, or a parent that is not a row
                break
            seen.add(node)
            path.append(node)
            node = parents[node]
        for offset, member in enumerate(reversed(path)):
            out[member] = None if base is None else base + 1 + offset
    return out


def check(method: str, *, using: str, allow_rebuild: bool = True) -> dict:
    """Every check that applies to one method."""
    checks = [check_y1(method, using=using)]
    if method == MPTT:
        checks.append(check_mptt_intervals(using=using, allow_rebuild=allow_rebuild))
    return {
        "method": method,
        "checks": checks,
        "passed": all(entry["passed"] for entry in checks),
        "failures": [entry["check"] for entry in checks if not entry["passed"]],
    }


__all__ = [
    "check", "check_y1", "check_mptt_intervals", "recompute_intervals",
    "parent_map", "REBUILD_LIMIT", "REBUILD_DEPTH_LIMIT",
]
