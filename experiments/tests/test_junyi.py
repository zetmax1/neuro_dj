"""
The Junyi loader (D61): the graph, the merge and the cleaning of the log.

Two kinds of test. The fixture ones pin every rule D61 writes down, each on a
row built to trigger it. The real-data ones assert the counts D61 fixes as the
specification — 979 edges, two self-loops, one merged cycle, 833 topics and a
longest path of 65 — and **skip** when the file is not on the machine (D49).
"""

from __future__ import annotations

import pytest

from experiments import orders
from experiments.datasets import DatasetMismatch, DatasetMissing, junyi


# ---------------------------------------------------------------------------
# The graph
# ---------------------------------------------------------------------------

def test_a_missing_file_says_so_and_does_not_download(tmp_path):
    with pytest.raises(DatasetMissing) as exercise:
        junyi.load_graph(tmp_path / "nope.csv")
    assert "D49" in str(exercise.value)

    with pytest.raises(DatasetMissing):
        junyi.inventory(tmp_path / "nope.csv")


def test_a_file_without_the_columns_is_a_mismatch(tmp_path):
    path = tmp_path / "table.csv"
    path.write_text("name,live\na,TRUE\n", encoding="utf-8")
    with pytest.raises(DatasetMismatch) as caught:
        junyi.load_graph(path, verify=False, sha256=False)
    assert "prerequisites" in str(caught.value)


def test_a_repeated_exercise_name_is_reported_not_merged(junyi_tiny_table):
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)

    assert graph.counts["rows"] == 9
    assert graph.counts["exercises"] == 8
    assert graph.duplicate_names == {"a": 1}


def test_the_edge_runs_from_the_prerequisite_to_the_dependent(junyi_tiny_table):
    """D61: a name in the prerequisites column is the knowledge map's parent."""
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)

    assert graph.prerequisites["b"] == ("a",)
    assert ("a", "b") in graph.graph.named_edges()
    assert ("b", "a") not in graph.graph.named_edges()
    assert graph.graph.edge_direction == "prereq_to_dependent"


def test_a_self_loop_is_removed_and_counted(junyi_tiny_table):
    """Y2: a node is never its own prerequisite."""
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)

    assert [graph.graph.name_of(node) for node in graph.graph.self_loops] == ["e"]
    assert "e" not in graph.prerequisites["e"]
    assert graph.prerequisites["e"] == ("b",)


def test_a_prerequisite_listed_twice_is_one_edge(junyi_tiny_table):
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)

    assert graph.counts["duplicate_edges"] == 1
    assert graph.prerequisites["c"] == ("b",)


def test_a_prerequisite_that_is_not_an_exercise_is_reported(junyi_tiny_table):
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)

    assert graph.unknown_prerequisites == ("ghost",)
    assert graph.prerequisites["z"] == ()


def test_a_cycle_is_merged_into_one_topic_named_after_its_first_member(junyi_tiny_table):
    """Y3 (D61): Tarjan's components become one topic each, and are recorded."""
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)

    assert graph.merged == (("x", "y"),)
    assert "y" not in graph.skills
    assert graph.skill_of["y"] == "x"
    assert graph.skill_of["x"] == "x"
    assert graph.counts["skills"] == graph.counts["exercises"] - 1
    assert graph.metadata()["merged_components"] == [["x", "y"]]


def test_the_tree_is_course_area_topic_exercise(junyi_tiny_table):
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)
    tree = graph.tree()

    assert list(tree) == ["Junyi Academy"]
    assert sorted(tree["Junyi Academy"]) == ["alpha", "beta"]
    assert tree["Junyi Academy"]["alpha"]["t1"] == ["a", "b"]


def test_the_weights_are_one_because_the_map_has_none(junyi_tiny_table):
    """D62, decision 3: ω = 1.0 for every edge of Junyi's knowledge map."""
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)

    assert graph.weighted_prerequisites()["b"] == (("a", 1.0),)


def test_the_licence_and_the_citation_travel_with_the_metadata(junyi_tiny_table):
    graph = junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)

    assert "commercial" in graph.metadata()["licence"]
    assert "EDM 2015" in graph.metadata()["citation"]


# ---------------------------------------------------------------------------
# The log
# ---------------------------------------------------------------------------

@pytest.fixture
def tiny(junyi_tiny_table):
    return junyi.load_graph(junyi_tiny_table, verify=False, sha256=False)


def test_the_log_keeps_only_exercises_the_table_knows(tiny, junyi_tiny_log):
    log = junyi.load_log(junyi_tiny_log, graph=tiny, learners=("1", "2", "3"), sha256=False)

    assert log.dropped["exercise_not_in_graph"] == 1
    assert all(row.skill_id in tiny.skills for row in log.rows)


def test_a_row_without_a_time_is_dropped_and_counted(tiny, junyi_tiny_log):
    log = junyi.load_log(junyi_tiny_log, graph=tiny, learners=("1", "2", "3"), sha256=False)

    assert log.dropped["no_time_done"] == 1
    assert [row.user_id for row in log.rows].count("3") == 1


def test_review_mode_answers_are_kept_and_topic_mode_is_metadata_only(tiny, junyi_tiny_log):
    """D61: a review answer is a real answer; topic_mode is not a filter."""
    log = junyi.load_log(junyi_tiny_log, graph=tiny, learners=("2",), sha256=False)

    assert log.flags["review_mode"] == 1
    assert log.flags["topic_mode"] == 1
    assert any(row.review_mode for row in log.rows)


def test_one_answer_is_one_order(tiny, junyi_tiny_log):
    """D57 on Junyi: a row is an order of its own, so the groups are singletons."""
    log = junyi.load_log(junyi_tiny_log, graph=tiny, learners=("1", "2", "3"), sha256=False)

    ids = [row.order_id for row in log.rows]
    assert ids == sorted(ids) == list(range(len(ids)))
    assert all(len(group) == 1 for group in orders.groups(log.rows))


def test_the_answers_are_ordered_by_learner_then_time(tiny, junyi_tiny_log):
    log = junyi.load_log(junyi_tiny_log, graph=tiny, learners=("1", "2", "3"), sha256=False)

    keys = [(float(row.user_id), row.time_done) for row in log.rows]
    assert keys == sorted(keys)


def test_a_merged_cycle_is_the_skill_the_models_see(tiny, junyi_tiny_log):
    log = junyi.load_log(junyi_tiny_log, graph=tiny, learners=("2",), sha256=False)
    answer = next(row for row in log.rows if row.exercise == "y")

    assert answer.skill_id == "x"
    assert answer.problem_id == "y:p0"


def test_the_published_correct_column_is_not_recomputed(tiny, junyi_tiny_log):
    """
    D61: ``correct`` already means "the first attempt was right, and no hint
    was asked for", so count_attempts and count_hints stay metadata.
    """
    log = junyi.load_log(junyi_tiny_log, graph=tiny, learners=("1",), sha256=False)
    hinted = [row for row in log.rows if row.skill_id == "c"]

    assert hinted and all(row.correct == 0 for row in hinted)


def test_the_inventory_counts_without_keeping_the_rows(tiny, junyi_tiny_log):
    found = junyi.inventory(junyi_tiny_log, graph=tiny, verify=False, sha256=False)

    assert found.rows == 11
    assert found.kept == 10
    assert found.learners == 3
    assert found.per_learner["1"] == 5
    assert found.dropped["exercise_not_in_graph"] == 1
    assert found.quantiles([1, 2, 3])["median"] == 2.0
    assert "answers_per_learner" in found.metadata()


def test_the_log_is_read_in_chunks(tiny, junyi_tiny_log):
    """A 2.6 GB pass has to show progress without holding the file (D61)."""
    seen: list[tuple[int, int]] = []
    junyi.inventory(
        junyi_tiny_log, graph=tiny, verify=False, sha256=False,
        chunk_rows=2, progress=lambda rows, kept: seen.append((rows, kept)),
    )

    assert seen and seen[0][0] == 2
    assert [rows for rows, _ in seen] == [2, 4, 6, 8, 10]


def test_the_documented_totals_stop_a_truncated_file(tiny, junyi_tiny_log):
    """
    The README's totals are the specification, so a file that does not produce
    them stops the pipeline — which is what half a download looks like (D61).
    """
    with pytest.raises(DatasetMismatch) as caught:
        junyi.inventory(junyi_tiny_log, graph=tiny, verify=True, sha256=False)
    message = str(caught.value)

    assert "rows" in message and str(junyi.DOCUMENTED_LOG["rows"]) in message
    assert "truncated" in message


def test_the_sample_is_the_same_for_one_seed_and_different_for_another():
    counts = {str(index): index for index in range(1, 50)}

    first = junyi.select_learners(counts, learners=10, seed=1)
    again = junyi.select_learners(counts, learners=10, seed=1)
    other = junyi.select_learners(counts, learners=10, seed=2)

    assert first == again
    assert first != other
    assert len(first) == 10
    assert junyi.select_learners(counts, learners=500, seed=1) == tuple(
        sorted(counts, key=lambda value: float(value))
    )


def test_the_sample_takes_a_learners_answers_whole(tiny, junyi_tiny_log):
    log = junyi.load_log(junyi_tiny_log, graph=tiny, learners=("1",), sha256=False)

    assert {row.user_id for row in log.rows} == {"1"}
    assert len(log.rows) == 5


# ---------------------------------------------------------------------------
# The published file (D61's counts)
# ---------------------------------------------------------------------------

def test_the_real_table_has_the_shape_d61_specifies(real_junyi_table):
    """Loads with ``verify=True``, so the counts are asserted by the loader."""
    graph = junyi.load_graph(real_junyi_table)

    for key, value in {**junyi.EXPECTED_EXERCISES, **junyi.EXPECTED_GRAPH}.items():
        assert graph.counts[key] == value, key
    assert graph.sha256 == junyi.KNOWN_SHA256[junyi.EXERCISE_TABLE]


def test_the_real_graph_is_a_dag_only_after_the_cycle_is_merged(real_junyi_table):
    from neuro_model import graph as model_graph

    graph = junyi.load_graph(real_junyi_table)

    assert graph.merged == (
        ("adding_and_subtracting_radicals",
         "radical_multiplication_and_division",
         "simplifying_radicals"),
    )
    with pytest.raises(model_graph.CycleError):
        model_graph.topological_order(
            list(graph.graph.nodes), list(graph.graph.edges), graph.graph.pos(),
        )
    assert graph.longest_path == 65


def test_the_real_graph_has_the_two_self_loops_d61_names(real_junyi_table):
    graph = junyi.load_graph(real_junyi_table)

    assert sorted(graph.graph.name_of(node) for node in graph.graph.self_loops) == [
        "number_sense_length_l1", "proportions_1",
    ]


def test_a_table_that_is_not_the_specified_one_stops_the_pipeline(real_junyi_table, tmp_path):
    """D61's counts are part of the specification (as D50's are, D48)."""
    copy = tmp_path / junyi.EXERCISE_TABLE
    lines = real_junyi_table.read_text(encoding="utf-8-sig").splitlines()
    copy.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    with pytest.raises(DatasetMismatch) as caught:
        junyi.load_graph(copy)
    assert "D61" in str(caught.value)
