"""
benchmarks/tests/test_operations.py — the operations, and that the two
methods are asked the same question (D63, D63a).

The comparison only means something if both methods run on the same target
node and return the same answer, so the first tests are equivalence tests:
the reads must agree on how many nodes they found, and the writes must leave
the same parent links behind. The rest pin the properties D63 fixed — paired
targets, a destination outside the moved subtree, and the Y1 check the CTE
move carries because mptt's does (D63a).
"""

from __future__ import annotations

import pytest
from mptt.exceptions import InvalidMove

from benchmarks import generator, operations
from benchmarks.models import CTE, METHODS, MPTT, CteNode, MpttNode, Shape

ALIAS = "benchmark"
pytestmark = pytest.mark.django_db(databases=["default", ALIAS])


def build(shape: str = Shape.COURSE_LIKE, size: int = 80) -> generator.TreeSpec:
    spec = generator.TreeSpec(shape=shape, size=size, seed=20261006)
    generator.build_all(spec, using=ALIAS)
    return spec


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

def test_the_targets_are_the_same_for_one_seed():
    spec = build()

    first = operations.targets(spec, count=10)
    again = operations.targets(spec, count=10)

    assert first == again
    assert len(first) == 10


@pytest.mark.parametrize("shape", [Shape.COURSE_LIKE, Shape.DEEP_CHAIN, Shape.RANDOM])
def test_a_destination_is_never_inside_the_moved_subtree(shape):
    """Otherwise mptt refuses the move and the cell would measure nothing."""
    spec = build(shape, size=120)
    parents = generator.parents(spec)

    for target in operations.targets(spec, count=25):
        node = target["node"] - 1
        walk = target["destination"] - 1
        while walk is not None:
            assert walk != node
            walk = parents[walk]


def test_a_target_has_children_so_a_branch_is_moved_not_a_leaf():
    spec = build(Shape.COURSE_LIKE, size=200)
    children = generator.children_of(generator.parents(spec))

    for target in operations.targets(spec, count=20):
        assert children[target["node"] - 1]
        assert target["children"] >= 1


# ---------------------------------------------------------------------------
# Equivalence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(operations.READ_OPERATIONS))
def test_the_reads_find_the_same_nodes_in_both_methods(name):
    spec = build(Shape.RANDOM, size=120)
    operation = operations.BY_NAME[name]
    target = operations.targets(spec, count=1)[0]

    counts = {
        method: operation.run(method, target, ALIAS) for method in METHODS
    }

    assert counts[MPTT] == counts[CTE] > 0


@pytest.mark.parametrize("name", list(operations.WRITE_OPERATIONS))
def test_the_writes_leave_the_same_tree_in_both_methods(name):
    spec = build(Shape.COURSE_LIKE, size=80)
    operation = operations.BY_NAME[name]
    target = operations.targets(spec, count=1)[0]

    for method in METHODS:
        operation.run(method, target, ALIAS)

    mptt = dict(MpttNode.objects.using(ALIAS).values_list("pk", "parent_id"))
    cte = dict(CteNode.objects.using(ALIAS).values_list("pk", "parent_id"))

    # The inserted node gets its own key from each table's sequence, so the
    # keys can differ; what has to match is the shape.
    assert sorted(mptt.values(), key=lambda value: (value is None, value)) == sorted(
        cte.values(), key=lambda value: (value is None, value)
    )
    assert len(mptt) == len(cte)


def test_appending_adds_a_child_at_the_end_and_leftmost_at_the_front():
    spec = build(Shape.COURSE_LIKE, size=80)
    target = operations.targets(spec, count=1)[0]
    parent = target["node"]

    operations.BY_NAME["append_leaf"].run(CTE, target, ALIAS)
    operations.BY_NAME["insert_leftmost"].run(CTE, target, ALIAS)

    children = list(
        CteNode.objects.using(ALIAS).filter(parent_id=parent).order_by("position", "id")
    )
    assert children[0].name == "leftmost"
    assert children[-1].name == "appended"


def test_deleting_a_branch_removes_its_whole_subtree():
    spec = build(Shape.COURSE_LIKE, size=80)
    target = operations.targets(spec, count=1)[0]
    before = CteNode.objects.using(ALIAS).count()

    removed = operations.BY_NAME["delete_branch"].run(CTE, target, ALIAS)

    assert removed > 1
    assert CteNode.objects.using(ALIAS).count() == before - removed


# ---------------------------------------------------------------------------
# Y1 (D63a)
# ---------------------------------------------------------------------------

def test_the_cte_move_refuses_a_move_into_its_own_subtree():
    """
    D63a: the CTE path carries the platform's Y1 check, because the mptt path
    it is compared with performs its own.
    """
    build(Shape.DEEP_CHAIN, size=20)
    inside = {"node": 2, "destination": 5}

    with pytest.raises(operations.Y1Violation):
        operations.BY_NAME["move_branch"].run(CTE, inside, ALIAS)

    with pytest.raises(InvalidMove):
        operations.BY_NAME["move_branch"].run(MPTT, inside, ALIAS)


def test_the_y1_check_is_the_expression_the_platform_uses():
    build(Shape.COURSE_LIKE, size=40)

    # No exception: the destination is not below the node.
    operations.check_y1(CteNode, 5, 1, using=ALIAS)
    with pytest.raises(operations.Y1Violation):
        operations.check_y1(CteNode, 1, 5, using=ALIAS)


def test_every_operation_is_either_a_read_or_a_write():
    assert len(operations.OPERATIONS) == 6
    assert len(operations.READ_OPERATIONS) == 2
    assert len(operations.WRITE_OPERATIONS) == 4
    assert all(operation.mutates == (operation.kind == "write")
               for operation in operations.OPERATIONS)
