"""
benchmarks/tests/test_rooted.py — the third reading method (D74).

The measurement is only worth reading if the rooted CTE answers the same
question as the library, so most of this file is equivalence: on every shape,
for every target, ``read_branch`` and ``read_ancestors`` must return exactly
the nodes ``descendants()`` and ``ancestors()` return. The rest pin what D74
decided before any number existed — the reading rule's three outcomes, and
that the cell measures all three methods on one target list.

Timings are never asserted: they belong to the machine, not to the code.
"""

from __future__ import annotations

import pytest

from benchmarks import generator, operations, rooted, runner
from benchmarks.models import CTE, CteNode, MPTT, Shape

ALIAS = "benchmark"
pytestmark = pytest.mark.django_db(databases=["default", ALIAS])

SHAPES = [Shape.COURSE_LIKE, Shape.DEEP_CHAIN, Shape.RANDOM]


def build(shape: str = Shape.COURSE_LIKE, size: int = 120) -> generator.TreeSpec:
    spec = generator.TreeSpec(shape=shape, size=size, seed=20261006)
    generator.build_all(spec, using=ALIAS)
    return spec


# ---------------------------------------------------------------------------
# Equivalence with the library — D74's precondition
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("shape", SHAPES)
def test_the_rooted_branch_read_returns_the_librarys_node_set(shape):
    spec = build(shape)

    for target in operations.targets(spec, count=15):
        node = CteNode.objects.using(ALIAS).get(pk=target["node"])
        library = {row.pk for row in node.descendants()}
        got = {
            row.pk for row in CteNode.objects.using(ALIAS).raw(
                rooted.DESCENDANTS_SQL, [node.pk, node.pk],
            )
        }
        assert got == library


@pytest.mark.parametrize("shape", SHAPES)
def test_the_rooted_ancestor_read_returns_the_librarys_node_set(shape):
    spec = build(shape)

    for target in operations.targets(spec, count=15):
        node = CteNode.objects.using(ALIAS).get(pk=target["node"])
        library = {row.pk for row in node.ancestors()}
        got = {
            row.pk for row in CteNode.objects.using(ALIAS).raw(
                rooted.ANCESTORS_SQL, [node.pk, node.pk],
            )
        }
        assert got == library


@pytest.mark.parametrize("shape", SHAPES)
def test_check_equivalence_reports_agreement_on_every_shape(shape):
    spec = build(shape)
    targets = operations.targets(spec, count=5)

    checks = rooted.check_equivalence(targets, using=ALIAS)

    assert checks
    assert all(item.equal for item in checks)
    assert {item.operation for item in checks} == {"read_branch", "read_ancestors"}


def test_the_reads_return_model_instances_not_tuples():
    """The other two methods return model instances; a bare row is not a fair race."""
    spec = build()
    target = operations.targets(spec, count=1)[0]
    node = CteNode.objects.using(ALIAS).get(pk=target["node"])

    rows = list(CteNode.objects.using(ALIAS).raw(rooted.DESCENDANTS_SQL, [node.pk, node.pk]))

    assert rows
    assert all(isinstance(row, CteNode) for row in rows)
    assert all(row.name for row in rows)


def test_the_counted_rows_match_the_library_count():
    spec = build()
    target = operations.targets(spec, count=1)[0]
    node = CteNode.objects.using(ALIAS).get(pk=target["node"])

    assert rooted.read_branch(rooted.CTE_ROOTED, target, ALIAS) == len(
        list(node.descendants())
    )
    assert rooted.read_ancestors(rooted.CTE_ROOTED, target, ALIAS) == len(
        list(node.ancestors())
    )


def test_an_equivalence_failure_stops_the_run_before_any_timing(monkeypatch):
    """A wrong query is not a fast one: ``run`` raises instead of writing."""
    broken = rooted.DESCENDANTS_SQL.replace("WHERE id <> %s", "WHERE id <> %s LIMIT 1")
    monkeypatch.setattr(rooted, "DESCENDANTS_SQL", broken)

    with pytest.raises(RuntimeError, match="different node set"):
        rooted.run(
            using=ALIAS, shapes=(Shape.COURSE_LIKE,), sizes=(120,),
            warmups=1, repeats=1, timeout=120.0, seed=20261006, log=lambda *_: None,
        )


# ---------------------------------------------------------------------------
# One cell: three methods, one target list
# ---------------------------------------------------------------------------

def test_a_cell_measures_all_three_methods_on_the_same_targets():
    spec = build()
    targets = operations.targets(spec, count=4)

    cell = rooted.run_cell(
        spec, "read_branch", using=ALIAS, warmups=1, repeats=3,
        budget=runner.Budget(timeout=120.0), seed=20261006,
        target_list=targets, log=lambda *_: None,
    )

    assert set(cell["methods"]) == set(rooted.READING_METHODS)
    assert cell["status"] == "ok"
    for method in rooted.READING_METHODS:
        assert cell["methods"][method]["status"] == "ok"
        assert len(cell["methods"][method]["timings"]) == 3
    assert set(cell["ratios"]) == {
        f"{rooted.CTE_ROOTED}_over_{MPTT}", f"{rooted.CTE_ROOTED}_over_{CTE}",
    }
    for ratio in cell["ratios"].values():
        assert ratio["ratio"] is not None
        assert ratio["paired"] is True


def test_the_three_methods_report_the_same_row_counts():
    """Same tree, same targets: the methods must see the same branch sizes."""
    spec = build()
    targets = operations.targets(spec, count=4)

    cell = rooted.run_cell(
        spec, "read_branch", using=ALIAS, warmups=1, repeats=3,
        budget=runner.Budget(timeout=120.0), seed=20261006,
        target_list=targets, log=lambda *_: None,
    )

    counts = {
        method: cell["methods"][method]["rows_touched_median"]
        for method in rooted.READING_METHODS
    }
    assert len(set(counts.values())) == 1, counts


# ---------------------------------------------------------------------------
# The reading rule, decided before the numbers
# ---------------------------------------------------------------------------

def _cell(ratio, *, status="ok"):
    return {
        "shape": Shape.COURSE_LIKE, "size": 1000, "operation": "read_branch",
        "status": status, "statuses": {method: status for method in rooted.READING_METHODS},
        "ratios": {
            f"{rooted.CTE_ROOTED}_over_{MPTT}": {"ratio": ratio},
            f"{rooted.CTE_ROOTED}_over_{CTE}": {"ratio": ratio},
        },
    }


def test_the_rule_confirms_when_every_cell_is_within_the_limit():
    reading = rooted.reading([_cell(0.4), _cell(1.0), _cell(rooted.SLOWDOWN_LIMIT)])

    assert reading["status"] == rooted.CONFIRMED
    assert reading["cells_measured"] == 3
    assert reading["cells_over_limit"] == []


def test_the_rule_names_the_cells_that_exceed_the_limit():
    reading = rooted.reading([_cell(0.4), _cell(2.0)])

    assert reading["status"] == rooted.PARTLY
    assert len(reading["cells_over_limit"]) == 1
    assert reading["cells_over_limit"][0]["ratio"] == 2.0


def test_an_unmeasured_cell_is_counted_not_treated_as_a_failure():
    reading = rooted.reading([_cell(0.4), _cell(None, status=runner.TIMEOUT)])

    assert reading["status"] == rooted.CONFIRMED
    assert reading["cells_not_measured"] == 1
    assert reading["cells_over_limit"] == []


def test_with_no_measured_cell_the_rule_says_so_instead_of_confirming():
    reading = rooted.reading([_cell(None, status=runner.TIMEOUT)])

    assert reading["status"] == rooted.NOT_COMPUTED


# ---------------------------------------------------------------------------
# The generated table obeys D48
# ---------------------------------------------------------------------------

def test_the_table_contains_no_number_that_is_not_in_the_metrics(tmp_path):
    from benchmarks.rooted_tables import render
    from experiments import tables
    from experiments.provenance import GitState, Provenance

    document = rooted.run(
        using=ALIAS, shapes=(Shape.COURSE_LIKE,), sizes=(120,),
        warmups=1, repeats=3, timeout=120.0, seed=20261006, log=lambda *_: None,
    )
    provenance = Provenance.capture(
        seeds={"trees": 20261006}, argv=["pytest"], packages={},
        git_start=GitState.capture(),
    )
    metrics = {
        "report": "tree_benchmark_rooted",
        "spec": "D74",
        "quick": True,
        "thesis_result": False,
        "provenance": provenance.payload(),
        "database": {"alias": ALIAS, "name": "test", "vendor": "postgresql"},
        "settings": {
            "warmups": 1, "repeats": 3, "timeout": 120.0,
            "replicates": runner.REPLICATES,
            "confidence_percent": int(runner.CONFIDENCE * 100),
        },
        **document,
    }

    markdown = render(metrics)

    assert tables.verify(markdown, metrics) == []
    paths = tables.write(tmp_path, metrics, provenance.env_txt(), renderer=render)
    assert paths["tables"].exists()
    assert rooted.CONFIRMED in markdown or rooted.PARTLY in markdown


def test_the_csv_has_one_row_per_method_and_repeat():
    spec = build()
    targets = operations.targets(spec, count=4)
    cell = rooted.run_cell(
        spec, "read_branch", using=ALIAS, warmups=1, repeats=3,
        budget=runner.Budget(timeout=120.0), seed=20261006,
        target_list=targets, log=lambda *_: None,
    )

    rows = rooted.csv_rows([cell])

    assert rows[0] == [
        "shape", "size", "operation", "method", "repeat",
        "seconds", "queries", "rows_touched",
    ]
    assert len(rows) == 1 + 3 * len(rooted.READING_METHODS)
