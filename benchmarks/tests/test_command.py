"""
benchmarks/tests/test_command.py — ``manage.py run_tree_benchmark`` (D63).

Two guards and one end-to-end run. The guards are the reason stage 9 can be
run at all without risking the development database: the command stops when
its alias resolves there, and it stops when the alias is not PostgreSQL. The
end-to-end test is the ``--quick`` pass, and what it asserts is D48's
invariant — every number in ``tables.md`` is a scalar of ``metrics.json``, and
each cell holds the number under its own key.
"""

from __future__ import annotations

import csv
import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from benchmarks import runner
from benchmarks.models import Shape

ALIAS = "benchmark"


def test_the_command_refuses_the_development_database():
    """Stage 9's rule: nothing here may touch the platform's tables."""
    from django.db import connections

    original = connections.databases["benchmark"]
    connections.databases["benchmark"] = dict(connections.databases["default"])
    try:
        with pytest.raises(CommandError) as caught:
            call_command("run_tree_benchmark", "--quick")
    finally:
        # Restored rather than removed: the alias is part of the test
        # databases pytest-django tears down afterwards.
        connections.databases["benchmark"] = original
        connections.close_all()

    assert "development database" in str(caught.value)


def test_an_unknown_alias_is_refused():
    with pytest.raises(CommandError) as caught:
        call_command("run_tree_benchmark", "--quick", "--database", "nowhere")

    assert "nowhere" in str(caught.value)


@pytest.mark.django_db(transaction=True, databases=["default", ALIAS])
def test_the_quick_pass_writes_a_table_that_verifies_cell_by_cell(tmp_path):
    """
    The whole command on a small tree. ``transaction=True``: the parallel
    phase forks processes that commit, and they cannot see a tree that is
    still inside the test's transaction.
    """
    from experiments import tables

    out = tmp_path / "bench"
    call_command(
        "run_tree_benchmark",
        "--quick",
        "--no-checkpoint",
        "--shapes", Shape.COURSE_LIKE,
        "--sizes", "120",
        "--repeats", "3",
        "--warmups", "1",
        "--parallel-workers", "2",
        "--parallel-seconds", "1",
        "--parallel-repeats", "1",
        "--out", str(out),
    )

    document = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    markdown = (out / "tables.md").read_text(encoding="utf-8")

    assert document["report"] == "tree_benchmark"
    assert document["hypothesis"] == "H4"
    assert document["thesis_result"] is False
    assert tables.verify(markdown, document) == []
    assert tables.verify_tree_benchmark_positions(markdown, document) == []
    assert "dissertatsiya natijasi emas" in markdown

    # One cell per operation, both methods in each.
    assert len(document["cells"]) == 6
    assert all(set(cell["methods"]) == {"mptt", "cte"} for cell in document["cells"])
    # Both parallel variants of D63a, and the locked one at the top count.
    variants = {row["variant"] for row in document["parallel"]}
    assert variants == {"unlocked", "locked"}
    assert document["reading"]["status"] in (
        runner.SUPPORTED, runner.NOT_SUPPORTED, runner.NOT_COMPUTED,
    )

    rows = list(csv.reader((out / "measurements.csv").read_text(encoding="utf-8").splitlines()))
    assert rows[0][0] == "shape"
    assert len(rows) > 6 * 2 * 3
    assert document["environment"]["postgres"]["vendor"] == "postgresql"
    assert document["database"]["name"].endswith("_bench")


@pytest.mark.django_db(transaction=True, databases=["default", ALIAS])
def test_the_development_tables_are_untouched_by_a_run(tmp_path):
    """
    The router's other direction: a run writes 120 nodes and the platform's
    own tables see nothing.
    """
    from curriculum.models import Topic

    before = Topic.objects.count()
    call_command(
        "run_tree_benchmark", "--quick", "--no-checkpoint",
        "--shapes", Shape.DEEP_CHAIN, "--sizes", "60", "--repeats", "2", "--warmups", "1",
        "--parallel-workers", "2", "--parallel-seconds", "1", "--parallel-repeats", "1",
        "--out", str(tmp_path / "bench"),
    )

    assert Topic.objects.count() == before
