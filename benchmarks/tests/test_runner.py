"""
benchmarks/tests/test_runner.py — the measurement loop and the reading rule (D63).

The statistics and the reading rule are pure functions and are tested as such:
a known pair of timings has a known ratio, one seed gives one interval, and
each of D63's three outcomes comes out of the interval it is defined by. The
database tests cover the two properties that make the numbers comparable at
all — a mutating repeat leaves the tree exactly as it found it, and a cell
that cannot finish inside its budget reports ``timeout`` and no number.
"""

from __future__ import annotations

import pytest

from benchmarks import generator, integrity, operations, runner
from benchmarks.models import CTE, MPTT, CteNode, MpttNode, Shape

ALIAS = "benchmark"


# ---------------------------------------------------------------------------
# Statistics (no database)
# ---------------------------------------------------------------------------

def test_the_ratio_is_above_one_when_mptt_is_slower():
    entry = runner.ratio_interval([2.0] * 10, [1.0] * 10, seed=1)

    assert entry["ratio"] == 2.0
    assert entry["ci_low"] == entry["ci_high"] == 2.0
    assert entry["paired"] is True
    assert runner.verdict_of(entry) == runner.CTE_FASTER


def test_the_ratio_is_below_one_when_cte_is_slower():
    entry = runner.ratio_interval([1.0] * 10, [4.0] * 10, seed=1)

    assert entry["ratio"] == 0.25
    assert runner.verdict_of(entry) == runner.MPTT_FASTER


def test_an_interval_that_spans_one_is_comparable():
    mptt = [1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0]
    cte = [2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0]

    entry = runner.ratio_interval(mptt, cte, seed=3)

    assert entry["ci_low"] < 1.0 < entry["ci_high"]
    assert runner.verdict_of(entry) == runner.COMPARABLE


def test_one_seed_gives_one_interval():
    """
    The interval is reproducible from the seed. Two seeds are *not* asserted
    to differ: a resampled median comes from the handful of values in the
    sample, so two seeds often land on the same quantile — which is a
    property of the median, not of the seeding.
    """
    mptt = [1.0, 1.4, 0.9, 1.2, 1.1, 1.3, 0.8, 1.5]
    cte = [0.5, 0.7, 0.4, 0.6, 0.5, 0.7, 0.4, 0.8]

    first = runner.ratio_interval(mptt, cte, seed=7, replicates=200)
    again = runner.ratio_interval(mptt, cte, seed=7, replicates=200)

    assert first == again
    assert first["ci_low"] <= first["ratio"] <= first["ci_high"]
    assert first["replicates"] == 200


def test_an_unmeasured_method_has_no_ratio():
    entry = runner.ratio_interval([], [1.0], seed=1)

    assert entry["ratio"] is None
    assert runner.verdict_of(entry) == runner.NOT_COMPUTED


def test_the_summary_carries_milliseconds_so_a_table_can_print_them():
    summary = runner.summarise([0.001, 0.002, 0.003])

    assert summary["median"] == 0.002
    assert summary["median_ms"] == 2.0
    assert summary["p95_ms"] > summary["median_ms"]
    assert summary["repeats"] == 3


# ---------------------------------------------------------------------------
# The reading rule (no database)
# ---------------------------------------------------------------------------

def cell(operation: str, kind: str, verdict: str, ratio: float | None = 2.0) -> dict:
    return {
        "shape": Shape.COURSE_LIKE, "size": 1000, "operation": operation, "kind": kind,
        "verdict": verdict, "ratio": {"ratio": ratio, "ci_low": ratio, "ci_high": ratio},
    }


def parallel_row(locked: bool, *, integrity_cte: bool = True) -> dict:
    return {
        "shape": Shape.COURSE_LIKE, "size": 1000, "workers": 8,
        "variant": "locked" if locked else "unlocked",
        "integrity_cte": integrity_cte, "integrity_mptt": True,
    }


def test_h4_holds_when_every_write_is_faster_and_the_reads_are_comparable():
    cells = [
        cell(name, "write", runner.CTE_FASTER) for name in operations.WRITE_OPERATIONS
    ] + [
        cell(name, "read", runner.COMPARABLE, ratio=0.9) for name in operations.READ_OPERATIONS
    ]

    result = runner.reading(cells, [parallel_row(True)])

    assert result["status"] == runner.SUPPORTED
    assert result["write_failures"] == []
    assert result["read_tolerance"] == 1.5


def test_a_write_that_is_only_comparable_refutes_h4():
    cells = [cell("move_branch", "write", runner.COMPARABLE, ratio=1.0),
             cell("read_branch", "read", runner.COMPARABLE, ratio=1.0)]

    result = runner.reading(cells, [parallel_row(True)])

    assert result["status"] == runner.NOT_SUPPORTED
    assert result["write_failures"] == ["move_branch@course_like/1000"]


def test_a_read_within_the_tolerance_does_not_refute_h4():
    """MPTT faster on a read is allowed while CTE stays inside 1.5×."""
    cells = [cell("append_leaf", "write", runner.CTE_FASTER),
             cell("read_branch", "read", runner.MPTT_FASTER, ratio=0.8)]

    result = runner.reading(cells, [parallel_row(True)])

    assert result["read_failures"] == []
    assert result["status"] == runner.SUPPORTED


def test_a_read_outside_the_tolerance_refutes_h4():
    cells = [cell("append_leaf", "write", runner.CTE_FASTER),
             cell("read_branch", "read", runner.MPTT_FASTER, ratio=0.3)]

    result = runner.reading(cells, [parallel_row(True)])

    assert result["read_failures"] == ["read_branch@course_like/1000"]
    assert result["status"] == runner.NOT_SUPPORTED


def test_the_integrity_condition_is_read_from_the_locked_variant():
    """D63a: the unlocked rows are descriptive, the locked one is the claim."""
    cells = [cell("append_leaf", "write", runner.CTE_FASTER),
             cell("read_branch", "read", runner.COMPARABLE, ratio=1.0)]

    unlocked_broken = runner.reading(
        cells, [parallel_row(False, integrity_cte=False), parallel_row(True)],
    )
    locked_broken = runner.reading(cells, [parallel_row(True, integrity_cte=False)])

    assert unlocked_broken["status"] == runner.SUPPORTED
    assert unlocked_broken["integrity_failures"] == []
    assert locked_broken["status"] == runner.NOT_SUPPORTED
    assert locked_broken["integrity_failures"] == ["course_like/1000/×8"]


def test_a_timeout_is_a_missing_number_not_a_refutation():
    cells = [cell("append_leaf", "write", runner.TIMEOUT, ratio=None),
             cell("read_branch", "read", runner.COMPARABLE, ratio=1.0)]

    result = runner.reading(cells, [parallel_row(True)])

    assert result["status"] == runner.NOT_COMPUTED
    assert result["not_computed"] == ["append_leaf@course_like/1000"]
    assert result["write_failures"] == []


# ---------------------------------------------------------------------------
# Measurement (database)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=["default", ALIAS])
def test_a_mutating_repeat_leaves_the_tree_as_it_found_it():
    """
    The rollback of D63: without it, repeat 30 would be measured on a tree 29
    inserts larger than repeat 1, and the two methods would diverge.
    """
    spec = generator.TreeSpec(shape=Shape.COURSE_LIKE, size=80, seed=20261006)
    generator.build_all(spec, using=ALIAS)
    targets = operations.targets(spec, count=4)
    before = integrity.parent_map(CTE, using=ALIAS)

    result = runner.measure(
        operations.BY_NAME["move_branch"], CTE, targets,
        using=ALIAS, warmups=1, repeats=3, budget=runner.Budget(timeout=60.0),
    )

    assert result["status"] == "ok"
    assert len(result["timings"]) == 3
    assert integrity.parent_map(CTE, using=ALIAS) == before
    assert CteNode.objects.using(ALIAS).count() == 80


@pytest.mark.django_db(databases=["default", ALIAS])
def test_a_cell_that_cannot_finish_in_its_budget_reports_no_number():
    spec = generator.TreeSpec(shape=Shape.COURSE_LIKE, size=60, seed=20261006)
    generator.build_all(spec, using=ALIAS)
    targets = operations.targets(spec, count=2)

    result = runner.measure(
        operations.BY_NAME["read_branch"], MPTT, targets,
        using=ALIAS, warmups=0, repeats=3, budget=runner.Budget(timeout=0.0),
    )

    assert result["status"] == runner.TIMEOUT
    assert "timings" not in result
    assert result["timeout"] == 0.0


@pytest.mark.django_db(databases=["default", ALIAS])
def test_an_operation_that_raises_is_reported_with_its_error():
    spec = generator.TreeSpec(shape=Shape.DEEP_CHAIN, size=20, seed=20261006)
    generator.build_all(spec, using=ALIAS)

    result = runner.measure(
        operations.BY_NAME["move_branch"], CTE, [{"node": 2, "destination": 5}],
        using=ALIAS, warmups=0, repeats=1, budget=runner.Budget(timeout=60.0),
    )

    assert result["status"] == "error"
    assert "Y1Violation" in result["error"]


@pytest.mark.django_db(databases=["default", ALIAS])
def test_the_changed_rows_show_mptts_interval_shift():
    """
    The column that explains the timings: a move rewrites most of an MPTT
    table and two rows of an adjacency list.
    """
    spec = generator.TreeSpec(shape=Shape.COURSE_LIKE, size=200, seed=20261006)
    generator.build_all(spec, using=ALIAS)
    target = operations.targets(spec, count=1)[0]
    operation = operations.BY_NAME["move_branch"]

    mptt = runner.changed_rows(operation, MPTT, target, using=ALIAS)
    cte = runner.changed_rows(operation, CTE, target, using=ALIAS)

    assert mptt["rows_changed"] > cte["rows_changed"]
    assert cte["rows_changed"] == 1
    assert mptt["rows_before"] == mptt["rows_after"] == 200


@pytest.mark.django_db(databases=["default", ALIAS])
def test_a_cell_runs_both_methods_and_compares_them():
    spec = generator.TreeSpec(shape=Shape.COURSE_LIKE, size=120, seed=20261006)
    generator.build_all(spec, using=ALIAS)
    targets = operations.targets(spec, count=4)

    entry = runner.run_cell(
        spec, operations.BY_NAME["read_ancestors"],
        using=ALIAS, warmups=1, repeats=3, budget=runner.Budget(timeout=60.0),
        seed=1, target_list=targets, log=lambda *a, **k: None,
    )

    assert set(entry["methods"]) == {MPTT, CTE}
    assert entry["ratio"]["ratio"] > 0
    assert entry["verdict"] in (
        runner.CTE_FASTER, runner.MPTT_FASTER, runner.COMPARABLE,
    )
    assert entry["kind"] == "read"
    # Reads do not get a changed-rows column: there is nothing to change.
    assert "changed" not in entry["methods"][MPTT]


# ---------------------------------------------------------------------------
# Checkpoints and the CSV (no database)
# ---------------------------------------------------------------------------

def test_the_checkpoint_resumes_only_its_own_key(tmp_path):
    first = runner.Checkpoint(tmp_path, {"commit": "a"}, enabled=True)
    first.save("block-x", {"cells": [1]})

    same = runner.Checkpoint(tmp_path, {"commit": "a"}, enabled=True)
    other = runner.Checkpoint(tmp_path, {"commit": "b"}, enabled=True)

    assert same.load("block-x") == {"cells": [1]}
    assert same.resumed == 1
    assert other.load("block-x") is None
    assert first.payload()["enabled"] is True


def test_a_disabled_checkpoint_writes_nothing(tmp_path):
    checkpoint = runner.Checkpoint(tmp_path, {"commit": "a"}, enabled=False)
    checkpoint.save("block-x", {"cells": [1]})

    assert checkpoint.load("block-x") is None
    assert not list(tmp_path.iterdir())


def test_the_csv_has_one_row_per_repeat():
    document = {
        "cells": [{
            "shape": "deep_chain", "size": 1000, "operation": "read_branch", "kind": "read",
            "methods": {
                MPTT: {"status": "ok", "timings": [0.1, 0.2]},
                CTE: {"status": runner.TIMEOUT},
            },
        }],
        "parallel": [{
            "shape": "deep_chain", "size": 1000, "workers": 2, "method": CTE,
            "phases": [{"repeat": 0, "throughput": 12.5}],
        }],
    }

    rows = runner.csv_rows(document)

    assert rows[0] == [
        "shape", "size", "operation", "kind", "method", "repeat", "seconds", "status",
    ]
    assert rows[1][4:] == [MPTT, 0, 0.1, "ok"]
    assert rows[2][4:] == [MPTT, 1, 0.2, "ok"]
    assert rows[3][4:] == [CTE, "", "", runner.TIMEOUT]
    assert rows[4][2] == "parallel_2"
