"""
benchmarks/tests/test_generator.py — the seeded trees of H4 (D63).

Two things have to hold or nothing downstream means anything: the three shapes
are the shapes D63 describes, and both tables hold the **same** tree. The third
test is the one that lets the generator skip mptt's ``rebuild()`` on a 100 000
node tree — it pins ``generator.intervals`` against that rebuild, so the
shortcut is checked rather than trusted.
"""

from __future__ import annotations

import pytest

from benchmarks import generator
from benchmarks.models import CTE, MPTT, CteNode, MpttNode, Shape

ALIAS = "benchmark"
# Both aliases: the benchmark's test database is created after the default one
# (Django orders them by TEST[DEPENDENCIES]), so asking for this one alone
# leaves that dependency unresolvable.
pytestmark = pytest.mark.django_db(databases=["default", ALIAS])


def spec(shape: str, size: int = 200, seed: int = 20261006) -> generator.TreeSpec:
    return generator.TreeSpec(shape=shape, size=size, seed=seed)


# ---------------------------------------------------------------------------
# The shapes (no database)
# ---------------------------------------------------------------------------

def test_the_course_like_shape_has_the_four_levels_d63_describes():
    parents = generator.parents(spec(Shape.COURSE_LIKE, size=1000))
    depth = generator.depth_of(parents)

    assert len(parents) == 1000
    assert parents[0] is None
    assert max(depth) == generator.COURSE_LIKE_LEVELS - 1
    # Wide: most of the tree is in the last level.
    assert depth.count(max(depth)) > len(parents) / 2


def test_the_deep_chain_is_one_child_per_node():
    parents = generator.parents(spec(Shape.DEEP_CHAIN, size=500))

    assert parents == [None, *range(499)]
    assert max(generator.depth_of(parents)) == 499


def test_the_random_shape_draws_a_parent_from_the_nodes_already_placed():
    parents = generator.parents(spec(Shape.RANDOM, size=500))

    assert parents[0] is None
    assert all(0 <= parent < index for index, parent in enumerate(parents) if parent is not None)
    assert max(generator.depth_of(parents)) < 499


def test_the_same_spec_gives_the_same_tree_and_a_different_seed_does_not():
    first = generator.parents(spec(Shape.RANDOM, seed=1))
    again = generator.parents(spec(Shape.RANDOM, seed=1))
    other = generator.parents(spec(Shape.RANDOM, seed=2))

    assert first == again
    assert first != other
    assert generator.digest(first) == generator.digest(again) != generator.digest(other)


def test_an_unknown_shape_is_refused():
    with pytest.raises(ValueError) as caught:
        generator.parents(generator.TreeSpec(shape="spiral", size=10, seed=1))
    assert "spiral" in str(caught.value)


def test_the_intervals_are_a_preorder_numbering():
    parents = generator.parents(spec(Shape.COURSE_LIKE, size=40))
    fields = generator.intervals(parents)
    children = generator.children_of(parents)

    for index, (_tree, lft, rght, level) in enumerate(fields):
        assert lft < rght
        assert level == generator.depth_of(parents)[index]
        for child in children[index]:
            _t, child_lft, child_rght, _l = fields[child]
            assert lft < child_lft < child_rght < rght
    assert sorted(value for _t, lft, rght, _l in fields for value in (lft, rght)) == list(
        range(1, 2 * len(parents) + 1)
    )


# ---------------------------------------------------------------------------
# The build (database)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("shape", [Shape.COURSE_LIKE, Shape.DEEP_CHAIN, Shape.RANDOM])
def test_the_intervals_agree_with_mptts_own_rebuild(shape):
    """
    The shortcut the generator takes on a 100 000-node tree, checked against
    the thing it replaces (D63).
    """
    built = generator.build(spec(shape, size=200), method=MPTT, using=ALIAS)
    before = dict(
        (pk, (tree, lft, rght, level))
        for pk, tree, lft, rght, level in MpttNode.objects.using(ALIAS).values_list(
            "pk", "tree_id", "lft", "rght", "level",
        )
    )

    MpttNode.objects.db_manager(ALIAS).rebuild()
    after = dict(
        (pk, (tree, lft, rght, level))
        for pk, tree, lft, rght, level in MpttNode.objects.using(ALIAS).values_list(
            "pk", "tree_id", "lft", "rght", "level",
        )
    )

    assert before == after
    assert built["nodes"] == 200


def test_both_methods_hold_the_same_tree():
    built = generator.build_all(spec(Shape.RANDOM, size=150), using=ALIAS)

    mptt = dict(MpttNode.objects.using(ALIAS).values_list("pk", "parent_id"))
    cte = dict(CteNode.objects.using(ALIAS).values_list("pk", "parent_id"))

    assert mptt == cte
    assert built[MPTT]["sha256"] == built[CTE]["sha256"]
    assert len(mptt) == 150


@pytest.mark.django_db(transaction=True, databases=["default", ALIAS])
def test_the_build_replaces_what_was_there():
    """
    A second build truncates the first. ``transaction=True``: TRUNCATE cannot
    run while the inserts of the same transaction still have pending
    self-referencing trigger events, and the benchmark's builds each commit.
    """
    generator.build(spec(Shape.DEEP_CHAIN, size=120), method=CTE, using=ALIAS)
    generator.build(spec(Shape.DEEP_CHAIN, size=40), method=CTE, using=ALIAS)

    assert CteNode.objects.using(ALIAS).count() == 40


def test_a_measured_insert_does_not_collide_with_the_assigned_keys():
    """
    The build assigns primary keys, so the table's sequence has to be moved
    past them or the first insert the benchmark measures would fail.
    """
    generator.build_all(spec(Shape.COURSE_LIKE, size=60), using=ALIAS)

    for model in (MpttNode, CteNode):
        node = model.objects.using(ALIAS).create(name="after", parent_id=1)
        assert node.pk > 60


@pytest.mark.django_db(transaction=True, databases=["default", ALIAS])
def test_truncating_one_method_leaves_the_other_alone():
    generator.build_all(spec(Shape.COURSE_LIKE, size=60), using=ALIAS)

    generator.truncate(MPTT, using=ALIAS)

    assert MpttNode.objects.using(ALIAS).count() == 0
    assert CteNode.objects.using(ALIAS).count() == 60
