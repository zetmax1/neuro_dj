"""
H3 — the graph controls (D61, D62).

What has to hold for the comparison to mean anything: the reversed graph is
the original turned around, the random graphs keep every node's degree (so
they are a null model and not just a sparser graph), a graph too constrained
to rewire is left out rather than silently becoming the original, λ is chosen
on validation, the graph-free arm is BKT+IRT (λ=0) exactly, and the contrast
against the random family is the mean over its arms. The last test runs the
module on the synthetic log and checks the table cell by cell (D48).
"""

from __future__ import annotations

import json

import pytest

from experiments import h3, tables
from experiments.datasets import junyi
from experiments.models import Unavailable
from experiments.models.classical import BKTFamily

CHAIN = {"a": (), "b": ("a",), "c": ("a", "b"), "d": ("c",)}


# ---------------------------------------------------------------------------
# The four graphs
# ---------------------------------------------------------------------------

def test_reversing_turns_every_edge_around():
    assert h3.reverse(CHAIN) == {"a": ("b", "c"), "b": ("c",), "c": ("d",), "d": ()}
    assert h3.reverse(h3.reverse(CHAIN)) == CHAIN


def test_the_random_graph_keeps_every_degree(real_junyi_table):
    """
    The null model's point: same degree sequence, different relations. Run on
    the published graph, because a swap chain needs room to move.
    """
    graph = junyi.load_graph(real_junyi_table)

    rewired, info = h3.randomise(graph.prerequisites, seed=1)

    assert info["degree_preserved"] is True
    assert info["distinct_from_original"] is True
    assert info["swaps_made"] == info["swaps_requested"]
    assert info["edges"] == sum(len(pre) for pre in graph.prerequisites.values())
    assert h3._degrees(rewired) == h3._degrees(graph.prerequisites)


def test_the_same_seed_rewires_the_same_way(real_junyi_table):
    graph = junyi.load_graph(real_junyi_table)

    first, _ = h3.randomise(graph.prerequisites, seed=5)
    again, _ = h3.randomise(graph.prerequisites, seed=5)
    other, _ = h3.randomise(graph.prerequisites, seed=6)

    assert first == again
    assert first != other


def test_a_graph_too_sparse_to_rewire_is_left_out_rather_than_being_the_original():
    """
    An arm called "random" that is the real graph would read as "no
    difference" when it means "no randomisation", so it does not run (D48).
    """
    tiny = {"a": (), "b": ("a",)}

    rewired, info = h3.randomise(tiny, seed=1)

    assert info["swaps_made"] == 0
    assert info["distinct_from_original"] is False
    assert rewired == tiny


def test_the_arms_are_original_reversed_random_and_none(real_junyi_table):
    graph = junyi.load_graph(real_junyi_table)

    arms, skipped = h3.arms(graph, seeds=2)

    assert [arm["name"] for arm in arms] == [
        h3.ORIGINAL, h3.REVERSED, "tasodifiy-1", "tasodifiy-2", h3.NO_GRAPH,
    ]
    assert skipped == []
    # The merged cycle appears under its representative only (D61).
    assert "simplifying_radicals" not in arms[0]["graph"]
    assert "adding_and_subtracting_radicals" in arms[0]["graph"]
    assert arms[-1]["graph"] is None
    # Only the first random arm picks its own λ; the rest reuse it (D62).
    assert [arm["choose_lambda"] for arm in arms] == [True, True, True, False, False]


def test_a_skipped_rewiring_is_recorded_and_not_an_arm():
    class Sparse:
        WEIGHT = 1.0
        prerequisites = {"a": (), "b": ("a",)}
        skills = ("a", "b")

    arms, skipped = h3.arms(Sparse(), seeds=3)

    assert [arm["family"] for arm in arms] == [h3.ORIGINAL, h3.REVERSED, h3.NO_GRAPH]
    assert len(skipped) == 3
    assert all(entry["distinct_from_original"] is False for entry in skipped)


# ---------------------------------------------------------------------------
# The model under the arms
# ---------------------------------------------------------------------------

def test_the_graph_free_arm_is_bkt_irt_lambda_zero():
    model = h3.model_for({"graph": None}, {}, lam=0.0)

    assert model.name == "BKT+IRT (λ=0)"
    assert model.flags.use_prereq_init is False


def test_bkt_irt_pre_runs_with_a_graph_and_says_so_without_one():
    rows = [
        junyi.Answer("1", 0, "a:p0", "a", 1, "a", 1, False, False, 1),
        junyi.Answer("1", 1, "b:p0", "b", 1, "b", 1, False, False, 2),
    ]
    graph = {"a": (), "b": (("a", 1.0),)}

    with_graph = h3.model_for({"graph": graph}, {}, lam=0.5)
    info = with_graph.fit(rows)

    assert with_graph.name == "BKT+IRT+Pre"
    assert info["graph"] == {"skills": 2, "edges": 1, "lambda": 0.5}
    assert len(with_graph.predict(rows)) == 2

    without = BKTFamily("BKT+IRT+Pre", use_irt=True, use_prereq_init=True)
    with pytest.raises(Unavailable) as caught:
        without.fit(rows)
    assert "graf" in caught.value.reason


def test_the_prior_reads_the_prerequisites_mastery():
    """P(L0) differs from P0 only when the graph is read (3.3's λ)."""
    rows = [
        junyi.Answer("1", 0, "a:p0", "a", 1, "a", 1, False, False, 1),
        junyi.Answer("1", 1, "a:p0", "a", 1, "a", 2, False, False, 2),
        junyi.Answer("1", 2, "b:p0", "b", 1, "b", 1, False, False, 3),
    ]
    graph = {"a": (), "b": (("a", 1.0),)}

    with_graph = h3.model_for({"graph": graph}, {}, lam=0.75)
    with_graph.fit(rows)
    without = h3.model_for({"graph": None}, {}, lam=0.0)
    without.fit(rows)

    assert with_graph.predict(rows)[2] != without.predict(rows)[2]


def test_lambda_is_chosen_on_validation_and_the_test_fold_is_not_touched(
    junyi_small, monkeypatch,
):
    graph = junyi.load_graph(junyi_small / junyi.EXERCISE_TABLE, verify=False, sha256=False)
    log = junyi.load_log(
        junyi_small / junyi.PROBLEM_LOG, graph=graph,
        learners=tuple(str(index) for index in range(1, 31)), sha256=False,
    )
    rows = list(log.rows)
    sets = {
        "train": rows[:600], "validation": rows[600:800], "test": rows[800:],
        "fitting": rows[:800],
    }
    arm = {"graph": graph.weighted_prerequisites(), "choose_lambda": True}

    # Every row any model is asked to fit or predict during the search.
    seen: set[int] = set()
    for method in ("fit", "predict"):
        inner = getattr(BKTFamily, method)

        def spy(self, given, *rest, _inner=inner, **kwargs):
            seen.update(id(row) for row in given)
            return _inner(self, given, *rest, **kwargs)

        monkeypatch.setattr(BKTFamily, method, spy)

    chosen = h3.choose_lambda(
        arm, {}, sets, keys=h3.skill_keys(sets["validation"]), k=3, log=lambda *a, **k: None,
    )

    assert seen and not any(id(row) in seen for row in sets["test"])
    assert chosen["lambda"] in h3.LAMBDA_GRID
    assert [item["lambda"] for item in chosen["candidates"]] == list(h3.LAMBDA_GRID)
    best = max(chosen["candidates"], key=lambda item: item["auc"])
    assert chosen["lambda"] == best["lambda"]


def test_an_arm_that_does_not_choose_lambda_reports_none():
    assert h3.choose_lambda({"choose_lambda": False}, {}, {}, keys=[], k=3) == {
        "lambda": None, "candidates": [],
    }


# ---------------------------------------------------------------------------
# Pooling, contrasts, reading
# ---------------------------------------------------------------------------

def test_the_first_k_window_is_per_learner_and_topic():
    keys = ["1|a", "1|a", "1|a", "1|a", "1|b", "2|a"]

    assert h3.first_k_indices(keys, 3) == [0, 1, 2, 4, 5]


def test_pooling_refuses_a_fold_with_a_missing_arm():
    first = {"predictions": {"asl": [0.1], "grafsiz": [0.2]}, "labels": [1],
             "learners": ["1"], "keys": ["1|a"]}
    second = {"predictions": {"asl": [0.3]}, "labels": [0],
              "learners": ["2"], "keys": ["2|a"]}

    with pytest.raises(RuntimeError) as caught:
        h3.pool([first, second])
    assert "grafsiz" in str(caught.value)


def test_the_contrast_against_the_random_family_is_the_mean_of_its_arms():
    labels = [0, 1, 0, 1, 0, 1]
    scores = {
        "asl": [0.1, 0.9, 0.2, 0.8, 0.3, 0.7],
        "tasodifiy-1": [0.9, 0.1, 0.8, 0.2, 0.7, 0.3],
        "tasodifiy-2": [0.1, 0.9, 0.2, 0.8, 0.3, 0.7],
    }
    statistic = h3._mean_auc_difference(labels, scores, ["asl"], ["tasodifiy-1", "tasodifiy-2"])

    import numpy as np

    # AUC(asl) = 1, AUC(random-1) = 0, AUC(random-2) = 1 → 1 − 0.5.
    assert statistic(np.arange(6)) == pytest.approx(0.5)


def test_the_reading_rule_needs_all_three_intervals_above_zero():
    def entry(name, low, high):
        return {"a": h3.ORIGINAL, "b": name, "status": "ok",
                "difference": (low + high) / 2, "ci_low": low, "ci_high": high}

    assert h3.reading([
        entry(h3.REVERSED, 0.01, 0.03), entry(h3.RANDOM, 0.005, 0.02),
        entry(h3.NO_GRAPH, 0.02, 0.04),
    ])["status"] == h3.SUPPORTED

    assert h3.reading([
        entry(h3.REVERSED, 0.01, 0.03), entry(h3.RANDOM, -0.01, 0.02),
    ])["status"] == h3.UNDETERMINED

    assert h3.reading([
        entry(h3.REVERSED, -0.03, -0.01), entry(h3.RANDOM, 0.005, 0.02),
    ])["status"] == h3.NOT_SUPPORTED

    assert h3.reading([
        {"a": h3.ORIGINAL, "b": h3.RANDOM, "status": "unavailable", "reason": "x"},
    ])["status"] == h3.UNDETERMINED


def test_the_reading_rule_says_the_result_is_about_this_graph():
    verdict = h3.reading([])

    assert "shu graf" in verdict["scope"]


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------

def test_the_pipeline_writes_a_table_that_verifies_cell_by_cell(junyi_small, tmp_path):
    out = tmp_path / "h3"
    code = h3.main([
        "--quick", "--no-verify", "--data", str(junyi_small),
        "--learners", "30", "--random-graphs", "2", "--replicates", "20",
        "--workers", "1", "--out", str(out),
    ])

    assert code == 0
    document = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    markdown = (out / "tables.md").read_text(encoding="utf-8")

    assert document["report"] == "h3"
    assert document["thesis_result"] is False
    assert tables.verify(markdown, document) == []
    assert tables.verify_h3_positions(markdown, document) == []
    assert "dissertatsiya natijasi emas" in markdown

    pooled = document["pooled"][document["main_k"]]
    assert [entry["b"] for entry in pooled["reading"]["per_contrast"]] == [
        h3.REVERSED, h3.RANDOM, h3.NO_GRAPH,
    ]
    assert pooled["families"][h3.RANDOM]["arms"] == 2
    assert document["constants"]["lambda_chapter_two"] == 0.5

    # A cell holding another key's number is caught (the positional check).
    row = next(line for line in markdown.splitlines() if line.startswith("| asl |"))
    cells = row.split("|")
    cells[-2] = " 0 "
    broken = markdown.replace(row, "|".join(cells))
    assert tables.verify_h3_positions(broken, document) != []
    assert tables.verify(broken, document) != []


def test_a_missing_dataset_is_a_sentence_not_a_crash(tmp_path):
    assert h3.main(["--quick", "--data", str(tmp_path / "nowhere")]) == 2
