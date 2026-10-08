"""
experiments/orders.py — the order a row belongs to (D57).

An order is a run of consecutive rows of one learner with one ``order_id``:
ASSISTments 2009 keeps a multi-skill problem as one row per skill, next to
each other and with the same ``correct``. Under D57 every row of an order is
predicted from the state before the order, and the order's answers are
applied after all of its rows are predicted — so no row sees the answer it is
predicting through a sibling row.

A row without an ``order_id`` (or with ``None``) is an order of its own, which
is what every harness did before D57.
"""

from __future__ import annotations

from collections.abc import Sequence


class OrderSplit(ValueError):
    """An order's rows are not contiguous in the learner's sequence."""


def _key(row):
    order = getattr(row, "order_id", None)
    return None if order is None else (row.user_id, order)


def order_starts(rows: Sequence) -> list[int]:
    """
    For each row, the index of the first row of its order.

    Raises ``OrderSplit`` when an order's rows are interrupted by another
    order of the same learner: "strictly earlier orders" would then have no
    meaning, and the harness stops rather than guess.
    """
    starts: list[int] = []
    closed: set = set()
    current = None
    start = 0
    for index, row in enumerate(rows):
        key = _key(row)
        if key is None or key != current:
            if current is not None:
                closed.add(current)
            if key is not None and key in closed:
                raise OrderSplit(f"order {key[1]} of learner {key[0]} is not contiguous (row {index})")
            current, start = key, index
        starts.append(start)
    return starts


def groups(rows: Sequence) -> list[list[int]]:
    """Row indices grouped by order, in sequence order."""
    out: list[list[int]] = []
    for index, start in enumerate(order_starts(rows)):
        if start == index:
            out.append([index])
        else:
            out[-1].append(index)
    return out


def first_in_order(rows: Sequence) -> list[bool]:
    """True for the first row of each order — the rows D57's sensitivity AUC is taken on."""
    return [start == index for index, start in enumerate(order_starts(rows))]
