"""
benchmarks/rooted.py — the third reading method of H4 (D74).

D63 compared two *storage* methods. This module adds a third *reading* method
on the storage D63 already measured: ``cte_rooted``, a recursive CTE whose
anchor is the requested node.

Why it is worth a separate measurement. ``django-tree-queries`` builds one CTE
over the whole table — the recursion starts at every root and the branch is
selected afterwards — so a read of one subtree pays for a walk of the forest.
The dissertation recommends starting the recursion at the requested node
instead, and D63 never measured that, so the recommendation stood on an
argument rather than on a number.

What is and is not compared:

- the table is ``benchmarks.CteNode``, unchanged. ``cte`` and ``cte_rooted``
  are the same rows, the same indexes and the same encoding; only the SQL of
  the two read operations differs. So the measurement isolates query shape,
  which is the thing the recommendation is about;
- the write operations are not measured. They are the same code as ``cte``'s,
  and measuring identical code twice would only add noise to the table;
- both operations fetch the node first and then its branch, exactly as
  ``operations._read_branch`` and ``_read_ancestors`` do for the other two
  methods: D63's rule that no method is handed its target for free;
- both return model instances through ``Model.objects.raw``, because the other
  two methods return model instances. A method that returned bare tuples would
  be measuring the ORM's absence, not the query.

Correctness is a precondition, not a result: :func:`check_equivalence` compares
the id sets with what the library returns, and the command refuses to write a
measurement that disagrees.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from django.db import connections

from benchmarks import generator, operations
from benchmarks.models import CTE, CteNode, MPTT

#: The name this method carries through the results.
CTE_ROOTED = "cte_rooted"

#: The three reading methods, in table order.
READING_METHODS: tuple[str, ...] = (MPTT, CTE, CTE_ROOTED)

_TABLE = CteNode._meta.db_table
_COLUMNS = "id, name, position, parent_id"

# The recursion's anchor is the requested row, not every root. The node itself
# is dropped at the end so the result is the strict descendant set, which is
# what ``descendants()`` returns by default.
DESCENDANTS_SQL = f"""
WITH RECURSIVE branch AS (
    SELECT {_COLUMNS} FROM {_TABLE} WHERE id = %s
    UNION ALL
    SELECT child.id, child.name, child.position, child.parent_id
      FROM {_TABLE} AS child
      JOIN branch ON child.parent_id = branch.id
)
SELECT {_COLUMNS} FROM branch WHERE id <> %s
"""

# Upwards from the node by parent_id. Strict ancestors, as ``ancestors()``.
ANCESTORS_SQL = f"""
WITH RECURSIVE chain AS (
    SELECT {_COLUMNS} FROM {_TABLE} WHERE id = %s
    UNION ALL
    SELECT parent.id, parent.name, parent.position, parent.parent_id
      FROM {_TABLE} AS parent
      JOIN chain ON chain.parent_id = parent.id
)
SELECT {_COLUMNS} FROM chain WHERE id <> %s
"""


def _node(pk: int, *, using: str) -> CteNode:
    return CteNode.objects.using(using).get(pk=pk)


def read_branch(method: str, target: dict, using: str) -> int:
    """The requested node, then its subtree from a CTE anchored on it."""
    node = _node(target["node"], using=using)
    rows = CteNode.objects.using(using).raw(DESCENDANTS_SQL, [node.pk, node.pk])
    return len(list(rows))


def read_ancestors(method: str, target: dict, using: str) -> int:
    """The requested node, then its ancestor chain from a CTE anchored on it."""
    node = _node(target["node"], using=using)
    rows = CteNode.objects.using(using).raw(ANCESTORS_SQL, [node.pk, node.pk])
    return len(list(rows))


#: The two measured operations, named as in D63's table so the three methods
#: line up row by row.
OPERATIONS: tuple[operations.Operation, ...] = (
    operations.Operation("read_branch", operations.READ, "shoxni o‘qish", read_branch),
    operations.Operation(
        "read_ancestors", operations.READ, "ajdodlarni o‘qish", read_ancestors,
    ),
)
BY_NAME = {operation.name: operation for operation in OPERATIONS}


# ---------------------------------------------------------------------------
# Correctness: the same nodes as the library, or no measurement
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Equivalence:
    """One correctness check: the two id sets and whether they agree."""

    operation: str
    node: int
    library_count: int
    rooted_count: int
    equal: bool

    def payload(self) -> dict:
        return {
            "operation": self.operation,
            "node": self.node,
            "library_nodes": self.library_count,
            "rooted_nodes": self.rooted_count,
            "equal": self.equal,
        }


def check_equivalence(targets: list[dict], *, using: str) -> list[Equivalence]:
    """
    Compare the id **sets** with ``descendants()`` / ``ancestors()`` (D74).

    Sets, not sequences: ordering is the library's contract and the hand-written
    CTE does not promise it. What has to hold is that the rooted query sees
    exactly the same nodes — anything else makes the timings meaningless.
    """
    out: list[Equivalence] = []
    for target in targets:
        node = _node(target["node"], using=using)

        library = {row.pk for row in node.descendants()}
        rooted = {
            row.pk for row in CteNode.objects.using(using).raw(
                DESCENDANTS_SQL, [node.pk, node.pk],
            )
        }
        out.append(Equivalence(
            "read_branch", node.pk, len(library), len(rooted), library == rooted,
        ))

        library = {row.pk for row in node.ancestors()}
        rooted = {
            row.pk for row in CteNode.objects.using(using).raw(
                ANCESTORS_SQL, [node.pk, node.pk],
            )
        }
        out.append(Equivalence(
            "read_ancestors", node.pk, len(library), len(rooted), library == rooted,
        ))
    return out


# ---------------------------------------------------------------------------
# One cell: three methods on the same tree and the same targets
# ---------------------------------------------------------------------------

def run_cell(
    spec: generator.TreeSpec,
    operation_name: str,
    *,
    using: str,
    warmups: int,
    repeats: int,
    budget,
    seed: int,
    target_list: list[dict],
    log=print,
) -> dict:
    """
    One (shape, size, read operation) across all three reading methods.

    The pairing of D63 is kept: repeat *i* of every method runs on the same
    target node, so the ratios can use the paired bootstrap of
    ``runner.ratio_interval`` rather than a wider interval that pretends the
    targets were independent.
    """
    from benchmarks import runner

    entry: dict = {
        "shape": spec.shape,
        "size": spec.size,
        "operation": operation_name,
        "kind": operations.READ,
        "label": operations.BY_NAME[operation_name].label,
        "targets": len(target_list),
        "methods": {},
    }

    for method in READING_METHODS:
        chosen = (
            BY_NAME[operation_name] if method == CTE_ROOTED
            else operations.BY_NAME[operation_name]
        )
        entry["methods"][method] = runner.measure(
            chosen, method, target_list,
            using=using, warmups=warmups, repeats=repeats, budget=budget,
        )
        # D63f: a read of a deep chain can hold gigabytes of rows; the next
        # method must not start on top of them.
        import gc

        gc.collect()

    entry["ratios"] = {}
    rooted = entry["methods"][CTE_ROOTED]
    for other in (MPTT, CTE):
        against = entry["methods"][other]
        if rooted["status"] == "ok" and against["status"] == "ok":
            entry["ratios"][f"{CTE_ROOTED}_over_{other}"] = runner.ratio_interval(
                rooted["timings"], against["timings"], seed=seed,
            )
        else:
            entry["ratios"][f"{CTE_ROOTED}_over_{other}"] = {
                "ratio": None, "ci_low": None, "ci_high": None, "replicates": 0,
                "reason": f"{CTE_ROOTED}: {rooted['status']}, {other}: {against['status']}",
            }

    statuses = {method: entry["methods"][method]["status"] for method in READING_METHODS}
    entry["status"] = "ok" if set(statuses.values()) == {"ok"} else "not_measured"
    entry["statuses"] = statuses

    log(
        f"    {operation_name:16s} "
        + " ".join(f"{m}={_ms(entry['methods'][m])}" for m in READING_METHODS)
        + f" ρ(rooted/mptt)={_value(entry['ratios'][f'{CTE_ROOTED}_over_{MPTT}'].get('ratio'))}"
    )
    return entry


def _ms(measured: dict) -> str:
    if measured.get("status") != "ok":
        return str(measured.get("status"))
    return f"{measured['seconds']['median_ms']}ms"


def _value(number) -> str:
    return "—" if number is None else f"{number:.3f}"


# ---------------------------------------------------------------------------
# The reading rule (D74), applied to the finished cells
# ---------------------------------------------------------------------------

#: D74: the recommendation holds if rooted reads are at most this many times
#: slower than the nested set in every measured cell.
SLOWDOWN_LIMIT = 1.5

CONFIRMED = "tavsiya tasdiqlandi"
PARTLY = "tavsiya qisman tasdiqlandi"
NOT_COMPUTED = "o‘qish qoidasi qo‘llanmadi — o‘lchanmagan katak"


def reading(cells: list[dict]) -> dict:
    """
    D74's rule, written before the numbers: ``cte_rooted`` is at most 1.5×
    the nested set in **every** measured read cell, or the cells where it is
    not are named.
    """
    measured = [cell for cell in cells if cell["status"] == "ok"]
    unmeasured = [
        {
            "shape": cell["shape"], "size": cell["size"],
            "operation": cell["operation"], "statuses": cell["statuses"],
        }
        for cell in cells if cell["status"] != "ok"
    ]
    over_limit = []
    for cell in measured:
        ratio = cell["ratios"][f"{CTE_ROOTED}_over_{MPTT}"].get("ratio")
        if ratio is None:
            unmeasured.append({
                "shape": cell["shape"], "size": cell["size"],
                "operation": cell["operation"], "statuses": cell["statuses"],
            })
        elif ratio > SLOWDOWN_LIMIT:
            over_limit.append({
                "shape": cell["shape"], "size": cell["size"],
                "operation": cell["operation"], "ratio": ratio,
            })

    if not measured:
        status = NOT_COMPUTED
    elif over_limit:
        status = PARTLY
    else:
        status = CONFIRMED

    return {
        "rule": (
            "D74: har bir o‘lchangan o‘qish katagida cte_rooted / mptt nuqtaviy "
            "bahosi SLOWDOWN_LIMIT dan oshmasa — tavsiya tasdiqlandi"
        ),
        # Counted here rather than in the renderer: D48 allows a table only
        # numbers metrics.json already holds.
        "cells_over_limit_count": len(over_limit),
        "limit": SLOWDOWN_LIMIT,
        "status": status,
        "cells_measured": len(measured),
        "cells_not_measured": len(unmeasured),
        "cells_over_limit": over_limit,
        "not_measured": unmeasured,
    }


def csv_rows(cells: list[dict]) -> list[list]:
    """Per-repeat measurements, one row per (cell, method, repeat) — V-H1."""
    rows: list[list] = [[
        "shape", "size", "operation", "method", "repeat",
        "seconds", "queries", "rows_touched",
    ]]
    for cell in cells:
        for method in READING_METHODS:
            measured = cell["methods"][method]
            if measured.get("status") != "ok":
                continue
            per_query = measured.get("queries_per_repeat") or []
            per_rows = measured.get("rows_per_repeat") or []
            for index, seconds in enumerate(measured["timings"]):
                rows.append([
                    cell["shape"], cell["size"], cell["operation"], method, index,
                    seconds,
                    per_query[index] if index < len(per_query) else "",
                    per_rows[index] if index < len(per_rows) else "",
                ])
    return rows


def run(
    *,
    using: str,
    shapes: tuple[str, ...],
    sizes: tuple[int, ...],
    warmups: int,
    repeats: int,
    timeout: float,
    seed: int,
    statement_timeout: int = 0,
    log=print,
) -> dict:
    """Every (shape, size, read operation) cell, the checks and the reading."""
    from benchmarks import runner

    budget = runner.Budget(timeout=timeout)
    runner.apply_statement_timeout(using, statement_timeout)

    cells: list[dict] = []
    trees: list[dict] = []
    checks: list[dict] = []
    started = time.perf_counter()

    for shape in shapes:
        for size in sizes:
            spec = generator.TreeSpec(shape=shape, size=size, seed=seed)
            log(f"  {shape}/{size}: building both tables")
            built = generator.build_all(spec, using=using)
            trees.extend(built.values())

            target_list = operations.targets(spec, count=warmups + repeats)
            if not target_list:
                log(f"  {shape}/{size}: no usable target, skipped")
                continue

            # Correctness before timing: a wrong query is not a fast one.
            equivalence = check_equivalence(target_list[:5], using=using)
            checks.extend(
                {**item.payload(), "shape": shape, "size": size}
                for item in equivalence
            )
            disagreeing = [item for item in equivalence if not item.equal]
            if disagreeing:
                raise RuntimeError(
                    f"{shape}/{size}: the rooted CTE returned a different node set "
                    f"than the library for {len(disagreeing)} check(s) (D74)"
                )

            for operation in OPERATIONS:
                cells.append(run_cell(
                    spec, operation.name, using=using, warmups=warmups,
                    repeats=repeats, budget=budget, seed=seed,
                    target_list=target_list, log=log,
                ))

    return {
        "methods": list(READING_METHODS),
        "cells": cells,
        "trees": trees,
        "equivalence": checks,
        "equivalence_checks": len(checks),
        "equivalence_failures": sum(1 for item in checks if not item["equal"]),
        "reading": reading(cells),
        "total_seconds": round(time.perf_counter() - started, 3),
    }


__all__ = [
    "CTE_ROOTED", "READING_METHODS", "DESCENDANTS_SQL", "ANCESTORS_SQL",
    "OPERATIONS", "BY_NAME", "read_branch", "read_ancestors",
    "Equivalence", "check_equivalence", "run_cell", "reading", "csv_rows", "run",
    "SLOWDOWN_LIMIT", "CONFIRMED", "PARTLY", "NOT_COMPUTED",
]
