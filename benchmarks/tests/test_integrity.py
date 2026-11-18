"""
benchmarks/tests/test_integrity.py — the checks that read the tree afterwards (D63).

A check that never fails proves nothing, so every one of them is run twice:
once on a tree the generator built, where it must pass, and once on a tree
broken on purpose, where it must say what broke and how much of it. The
breakage is done with raw SQL, because that is the only way to produce the
state a race produces — the ORM would refuse it.
"""

from __future__ import annotations

import pytest
from django.db import connections

from benchmarks import generator, integrity
from benchmarks.models import CTE, MPTT, CteNode, MpttNode, Shape

ALIAS = "benchmark"
pytestmark = pytest.mark.django_db(databases=["default", ALIAS])


def build(shape: str = Shape.COURSE_LIKE, size: int = 60) -> generator.TreeSpec:
    spec = generator.TreeSpec(shape=shape, size=size, seed=20261006)
    generator.build_all(spec, using=ALIAS)
    return spec


def sql(statement: str, params: list | None = None) -> None:
    with connections[ALIAS].cursor() as cursor:
        cursor.execute(statement, params or [])


# ---------------------------------------------------------------------------
# Y1
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method", [MPTT, CTE])
def test_y1_passes_on_a_generated_tree(method):
    build()

    result = integrity.check_y1(method, using=ALIAS)

    assert result["passed"] is True
    assert result["roots"] == 1
    assert result["cycles"] == 0
    assert result["dangling_parents"] == 0
    assert result["nodes"] == 60


@pytest.mark.parametrize("method,table", [(MPTT, "benchmarks_mptt_node"), (CTE, "benchmarks_cte_node")])
def test_a_cycle_is_caught(method, table):
    """Two nodes as each other's parent — what an unlocked concurrent move does."""
    build()
    sql(f'UPDATE "{table}" SET parent_id = 3 WHERE id = 2')
    sql(f'UPDATE "{table}" SET parent_id = 2 WHERE id = 3')

    result = integrity.check_y1(method, using=ALIAS)

    assert result["passed"] is False
    assert result["cycles"] > 0
    assert result["cycle_nodes"]


@pytest.mark.parametrize("method,table", [(MPTT, "benchmarks_mptt_node"), (CTE, "benchmarks_cte_node")])
def test_a_second_root_is_caught(method, table):
    build()
    sql(f'UPDATE "{table}" SET parent_id = NULL WHERE id = 5')

    result = integrity.check_y1(method, using=ALIAS)

    assert result["passed"] is False
    assert result["roots"] == 2


# ---------------------------------------------------------------------------
# The intervals
# ---------------------------------------------------------------------------

def test_the_intervals_pass_on_a_generated_tree():
    build()

    result = integrity.check_mptt_intervals(using=ALIAS)

    assert result["passed"] is True
    assert result["differs_from_rebuild"] == 0
    assert result["rebuild_source"] == "mptt rebuild()"


def test_an_inverted_interval_is_caught():
    build()
    sql('UPDATE "benchmarks_mptt_node" SET lft = rght, rght = lft WHERE id = 4')

    result = integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=False)

    assert result["passed"] is False
    assert result["lft_not_less_than_rght"] >= 1
    assert 4 in result["examples"]["inverted"]


def test_a_child_outside_its_parents_interval_is_caught():
    build()
    # Reparent one node without touching its intervals: exactly what a stale
    # read leaves behind.
    sql('UPDATE "benchmarks_mptt_node" SET parent_id = 2 WHERE id = 30')

    result = integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=False)

    assert result["passed"] is False
    assert result["outside_parent_interval"] >= 1 or result["wrong_level"] >= 1


def test_a_wrong_level_is_caught():
    build()
    sql('UPDATE "benchmarks_mptt_node" SET level = level + 1 WHERE id = 7')

    result = integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=False)

    assert result["passed"] is False
    assert 7 in result["examples"]["wrong_level"]


def test_duplicate_boundaries_are_caught():
    build()
    sql('UPDATE "benchmarks_mptt_node" SET lft = 2, rght = 3 WHERE id = 9')

    result = integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=False)

    assert result["passed"] is False
    assert result["duplicate_boundaries"] > 0


def test_the_recomputation_is_what_rebuild_would_have_written():
    """
    The large-tree branch of the check, against the small-tree branch: the
    recomputation and mptt's ``rebuild()`` must agree, or the check would mean
    something different above 20 000 nodes.
    """
    build(size=120)
    stored = integrity.parent_map(MPTT, using=ALIAS)
    order = dict(MpttNode.objects.using(ALIAS).values_list("pk", "lft"))
    recomputed = integrity.recompute_intervals(stored, order)

    MpttNode.objects.db_manager(ALIAS).rebuild()
    after = {
        pk: (lft, rght, level)
        for pk, lft, rght, level in MpttNode.objects.using(ALIAS).values_list(
            "pk", "lft", "rght", "level",
        )
    }

    assert recomputed == after
    assert integrity.REBUILD_LIMIT == 20_000


def test_the_large_tree_branch_says_which_source_it_used():
    build()

    result = integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=False)

    assert "recomputed" in result["rebuild_source"]
    assert result["passed"] is True


# ---------------------------------------------------------------------------
# check()
# ---------------------------------------------------------------------------

def test_the_cte_method_is_checked_for_y1_only():
    build()

    result = integrity.check(CTE, using=ALIAS)

    assert [entry["check"] for entry in result["checks"]] == ["y1"]
    assert result["passed"] is True


def test_the_mptt_method_is_checked_for_both():
    build()

    result = integrity.check(MPTT, using=ALIAS)

    assert [entry["check"] for entry in result["checks"]] == ["y1", "mptt_intervals"]
    assert result["passed"] is True
    assert result["failures"] == []


def test_a_failure_is_named_rather_than_hidden():
    build()
    sql('UPDATE "benchmarks_mptt_node" SET lft = rght, rght = lft WHERE id = 4')

    result = integrity.check(MPTT, using=ALIAS, allow_rebuild=False)

    assert result["passed"] is False
    assert result["failures"] == ["mptt_intervals"]


@pytest.mark.django_db(databases=["default", ALIAS])
def test_a_deep_tree_is_checked_without_mptts_recursive_rebuild():
    """
    D63d: ``mptt.managers._rebuild_helper`` calls itself once per level, so a
    tree deeper than the frame budget cannot be checked that way — this is
    what ended the full pass of 2026-10-14 at the 10 000-deep chain. Above
    ``REBUILD_DEPTH_LIMIT`` the iterative recomputation is used instead, and
    the check still passes on a clean tree and still catches a broken one.
    """
    build(Shape.DEEP_CHAIN, size=1200)

    result = integrity.check_mptt_intervals(using=ALIAS)

    assert result["passed"] is True
    assert "too deep" in result["rebuild_source"]
    assert integrity.REBUILD_DEPTH_LIMIT == 500

    sql('UPDATE "benchmarks_mptt_node" SET lft = rght, rght = lft WHERE id = 600')
    broken = integrity.check_mptt_intervals(using=ALIAS)
    assert broken["passed"] is False
    assert 600 in broken["examples"]["inverted"]


@pytest.mark.django_db(databases=["default", ALIAS])
def test_a_shallow_tree_still_goes_through_rebuild():
    build(Shape.COURSE_LIKE, size=200)

    result = integrity.check_mptt_intervals(using=ALIAS)

    assert result["rebuild_source"] == "mptt rebuild()"
    assert result["passed"] is True


@pytest.mark.django_db(databases=["default", ALIAS])
def test_a_legitimate_move_is_not_reported_as_broken_intervals():
    """
    D63g: ``move_to(target, "last-child")`` separates the sibling order from
    the primary-key order. mptt's own ``rebuild()`` sees nothing wrong there,
    so neither may the recomputation the large-tree branch uses.
    """
    build(Shape.COURSE_LIKE, size=200)
    node = MpttNode.objects.using(ALIAS).get(pk=5)
    node.move_to(MpttNode.objects.using(ALIAS).get(pk=3), position="last-child")

    assert integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=False)["passed"] is True
    assert integrity.check_mptt_intervals(using=ALIAS)["passed"] is True


@pytest.mark.django_db(databases=["default", ALIAS])
def test_broken_intervals_are_still_caught_after_a_move():
    """The other half of D63g: the comparison must still catch real damage."""
    build(Shape.COURSE_LIKE, size=200)
    node = MpttNode.objects.using(ALIAS).get(pk=5)
    node.move_to(MpttNode.objects.using(ALIAS).get(pk=3), position="last-child")
    sql('UPDATE "benchmarks_mptt_node" SET rght = rght + 2 WHERE id = 40')

    result = integrity.check_mptt_intervals(using=ALIAS, allow_rebuild=False)

    assert result["passed"] is False
    assert result["differs_from_rebuild"] >= 1
