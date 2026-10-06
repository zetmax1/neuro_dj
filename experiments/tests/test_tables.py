"""
D48: a result exists only if it was produced.

This is the test the stage is built around. The failure it guards against is
not a typo — it is the quiet one, where a table gains a plausible figure for a
dataset that was never on the machine, or a number gets adjusted after the
run. So: every number in ``tables.md`` is a scalar that is already in
``metrics.json``; a dataset that is absent produces a row that says so and no
numbers; and a result whose input cannot be identified by sha256 is refused.
"""

from __future__ import annotations

import json

import pytest

from experiments import tables
from experiments.graph_report import build_parser, run
from experiments.provenance import Provenance, Source


def metrics_of(tiny_graphml, *extra_argv):
    argv = ["--graph", str(tiny_graphml), "--samples", "2", "--repeats", "2", *extra_argv]
    document, provenance = run(build_parser().parse_args(argv), argv)
    return document, provenance


# ---------------------------------------------------------------------------
# The invariant
# ---------------------------------------------------------------------------

def test_every_number_in_the_table_comes_from_the_metrics(tiny_graphml):
    document, _ = metrics_of(tiny_graphml)
    markdown = tables.render_graph_report(document)

    assert tables.verify(markdown, document) == []


def test_every_number_in_the_table_comes_from_the_metrics_for_a_cyclic_graph(
    cyclic_graphml,
):
    """The Y3 branch renders its own numbers, so it is checked on its own."""
    document, _ = metrics_of(cyclic_graphml)
    markdown = tables.render_graph_report(document)

    assert document["graphs"][0]["is_dag"] is False
    assert tables.verify(markdown, document) == []


def test_a_number_that_is_not_in_the_metrics_is_caught(tiny_graphml):
    """The check has to be able to fail, or it is not a check."""
    document, _ = metrics_of(tiny_graphml)
    markdown = tables.render_graph_report(document)

    tampered = markdown + "\n| DKT | 0.863 |\n"
    assert tables.verify(tampered, document) == ["0.863"]


def test_an_edited_result_is_caught(tiny_graphml):
    """A number rounded up after the run is exactly what this prevents."""
    document, _ = metrics_of(tiny_graphml)
    markdown = tables.render_graph_report(document)
    nodes = str(document["graphs"][0]["nodes"])

    assert tables.verify(markdown.replace(f"| {nodes} |", "| 999 |", 1), document) == ["999"]


def test_only_chapter_references_may_be_numbers_in_the_prose():
    """
    The allow-list is tiny and fixed. If it grows, this test fails, which is
    the point: a result number must never be able to enter the table by being
    added to it.
    """
    assert tables.CITATIONS == frozenset({"2.2", "2.3", "2.4", "3.3", "2016"})


def test_writing_is_refused_when_a_number_cannot_be_traced(tmp_path, tiny_graphml):
    """Nothing is written at all, so a bad run leaves no half-result behind."""
    document, provenance = metrics_of(tiny_graphml)

    class Liar:
        @staticmethod
        def render(_document):
            return "# x\n\n| a | 0.999 |\n"

    with pytest.raises(ValueError, match="not in metrics.json"):
        tables.write(tmp_path / "out", document, provenance.env_txt(), renderer=Liar.render)
    assert not (tmp_path / "out").exists()


# ---------------------------------------------------------------------------
# An absent dataset
# ---------------------------------------------------------------------------

def test_an_absent_dataset_gets_a_sentence_not_a_number(tmp_path):
    argv = ["--graph", str(tmp_path / "gone.graphml")]
    document, _ = run(build_parser().parse_args(argv), argv)
    markdown = tables.render_graph_report(document)

    assert tables.NOT_RUN in markdown
    assert tables.verify(markdown, document) == []
    # The row carries no size, no hash and no timing.
    row = [line for line in markdown.splitlines() if "gone" in line][0]
    assert tables.NOT_RUN in row
    assert "—" in row


def test_a_result_without_a_source_hash_is_refused():
    broken = {"graphs": [{"name": "X", "status": "ok", "nodes": 3}]}
    with pytest.raises(ValueError, match="no source sha256"):
        tables.require_sources(broken)

    # The row that says the dataset was absent needs no hash.
    tables.require_sources({"graphs": [{"name": "X", "status": "not_run"}]})


# ---------------------------------------------------------------------------
# The four facts of D48 reach the file
# ---------------------------------------------------------------------------

def test_the_table_carries_the_hash_the_commit_the_seed_and_the_command(tiny_graphml):
    document, _ = metrics_of(tiny_graphml)
    markdown = tables.render_graph_report(document)
    source = document["graphs"][0]["source"]

    assert source["sha256"] in markdown
    assert source["sha256"][: tables.SHA_PREFIX] in markdown
    assert "python -m experiments.graph_report" in markdown
    assert str(document["provenance"]["seeds"]["sample_order"]) in markdown
    commit = document["provenance"]["code_commit"]
    if commit:
        assert commit in markdown


def test_the_three_files_are_written_together(tmp_path, tiny_graphml):
    document, provenance = metrics_of(tiny_graphml)
    written = tables.write(tmp_path / "run", document, provenance.env_txt())

    assert sorted(path.name for path in written.values()) == [
        "env.txt", "metrics.json", "tables.md",
    ]
    reloaded = json.loads(written["metrics"].read_text(encoding="utf-8"))
    # The document on disk and the one in memory are the same, so verifying
    # the second is verifying the first.
    assert reloaded == json.loads(json.dumps(document))
    assert tables.verify(written["tables"].read_text(encoding="utf-8"), reloaded) == []
    assert "sha256" in written["env"].read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def test_a_number_is_formatted_one_way_only():
    assert tables.fmt(98) == "98"
    assert tables.fmt(0.7312) == "0.731"
    assert tables.fmt(37.0) == "37"
    assert tables.fmt(0.0) == "0"
    # Booleans are Uzbek words, not 1 and 0 — a DAG column reading "1" would
    # look like a count.
    assert tables.fmt(True) == "ha"
    assert tables.fmt(False) == "yo‘q"


def test_the_allowed_set_is_built_with_the_same_formatter():
    document = {"a": 0.7312, "b": 98, "c": "0.9999", "d": "Box and Whisker"}
    allowed = tables.allowed_numbers(document)

    assert "0.731" in allowed      # fmt
    assert "0.7312" in allowed     # raw
    assert "98" in allowed
    # A numeric string is a number of the metrics, not text: ids in this data
    # are strings, and stripping "47" as text would cut a hole in 47 037.
    assert "0.9999" in allowed
    assert "Box and Whisker" not in allowed


def test_a_numeric_id_is_not_stripped_out_of_a_longer_number():
    """
    The bug this guards: skill "47" is a string scalar, and removing every
    occurrence of it from the markdown turned the real count 47 037 into
    "037", which then looked like a number from nowhere.
    """
    document = {"skill": "47", "count": 47037}
    markdown = "| 47 | 47037 |"

    assert "47" not in tables.allowed_strings(document)
    assert tables.verify(markdown, document) == []


def test_the_simulated_tree_is_separate(tmp_path):
    """D13, D48: a pipeline test cannot be mistaken for a result."""
    plain = Provenance.capture(sources=(), seeds={})
    assert plain.code_commit is None or isinstance(plain.code_commit, str)

    from experiments.provenance import results_dir

    real = results_dir("assist09", root=tmp_path, timestamp="20261006-000000")
    fake = results_dir("assist09", root=tmp_path, timestamp="20261006-000000", simulated=True)

    # Compared below the root: the temporary directory's own name is not ours.
    assert real.relative_to(tmp_path).parts == ("assist09", "20261006-000000")
    assert fake.relative_to(tmp_path).parts == ("simulated", "assist09", "20261006-000000")


def test_a_source_records_the_bytes_it_hashed(tmp_path):
    path = tmp_path / "f.txt"
    path.write_bytes(b"abc")
    source = Source.of("f", path)

    assert source.bytes == 3
    assert source.sha256 == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


# ---------------------------------------------------------------------------
# The H2 table (D53)
# ---------------------------------------------------------------------------

def h2_metrics() -> dict:
    """
    A metrics document shaped like a real h2 run, small enough to read.

    Written out by hand rather than produced by a run, because the invariant
    being tested is about the renderer: no number may reach the table except
    through the metrics. It includes the cases that are easy to get wrong — an
    unavailable model, a numeric string id, a negative log-likelihood and a
    missing AUC.
    """
    return {
        "report": "h2",
        "quick": True,
        "epochs": 3,
        "provenance": {
            "command": "python -m experiments.h2 --quick",
            "code_commit": "abc1234",
            "code_dirty": False,
            "created_at": "2026-10-06T00:00:00+00:00",
            "python": "3.12.3",
            "platform": "Linux",
            "seeds": {"split": 20261006},
            "sources": [{
                "name": "assistments2009",
                "path": "/data/as.csv",
                "sha256": "f" * 64,
                "bytes": 83201940,
            }],
        },
        "dataset": {
            "status": "ok",
            "name": "assistments2009",
            "label": "ASSISTments 2009–2010 skill builder",
            "original_only": False,
            "source": {"sha256": "f" * 64},
            "raw": {"rows": 525534, "students": 4217, "blank_skill_id": 66326},
            "cleaned": {
                "rows": 338001, "students": 4163, "skills": 123,
                "multi_skill_orders": 47037,
            },
            "answers_used": 31647,
            "learners_used": 200,
            "cleaning_rules": ["drop rows with an empty skill_id"],
        },
        "split": {"folds": 5, "validation_fraction": 0.2, "seed": 20261006},
        "folds": [{
            "index": 0,
            "models": {
                "BKT": {"status": "ok", "scores": {"all": {"auc": 0.6647}}},
                "BKT+IRT+Pre": {"status": "unavailable", "reason": "graf yo‘q"},
            },
        }],
        "pooled": {
            "replicates": 200,
            "confidence_percent": 95,
            "models": {
                "BKT": {
                    "scores": {
                        "all": {"auc": 0.6703, "rmse": 0.4481, "accuracy": 0.7142, "n": 31647},
                        "first_3": {"auc": 0.6401},
                        "first_5": {"auc": 0.6502},
                    },
                    "auc_interval": {
                        "estimate": 0.6703, "ci_low": 0.6512, "ci_high": 0.6894,
                        "replicates": 200, "clustered_by_learner": True,
                    },
                },
                "DKT": {
                    "scores": {
                        "all": {"auc": 0.7312, "rmse": 0.4502, "accuracy": 0.7201, "n": 31647},
                        "first_3": {"auc": None},
                        "first_5": {"auc": 0.6902},
                    },
                    "auc_interval": {
                        "estimate": 0.7312, "ci_low": 0.7101, "ci_high": 0.7503,
                        "replicates": 200, "clustered_by_learner": True,
                    },
                },
            },
            "comparisons": [{
                "a": "DKT", "b": "BKT", "auc_a": 0.7312, "auc_b": 0.6703,
                "difference": 0.0609, "z": 12.4512, "p": 1.3e-05,
                "p_holm": 1.3e-05, "significant": True,
            }],
        },
        "sanity": {
            "model": "DKT", "auc": 0.7312,
            "expected_range": [0.7, 0.8], "literature_range": [0.73, 0.75],
            "within_range": True,
        },
        "pybkt_cross_check": {
            "skills_compared": 1,
            "seed": 20261006,
            "bounds": {"g_max": 0.3, "s_max": 0.1},
            "pybkt_outside_bounds_count": 1,
            "comparisons": [{
                "skill": "47",
                "status": "ok",
                "answers": 4210,
                "learners": 310,
                "grid": {"p0": 0.3, "pt": 0.05, "g0": 0.25, "s0": 0.09},
                "pybkt": {"p0": 0.5721, "pt": 0.0431, "g0": 0.3811, "s0": 0.1522},
                "pybkt_outside_bounds": {"g0": True, "s0": True},
                "log_likelihood": {"grid": -2612.4193, "pybkt": -2588.1072},
            }],
        },
        "unavailable": [{"model": "BKT+IRT+Pre", "reason": "graf yo‘q"}],
    }


def test_the_h2_table_contains_no_number_that_is_not_in_the_metrics():
    document = h2_metrics()
    markdown = tables.render_h2_report(document)

    assert tables.verify(markdown, document) == []


def test_the_h2_table_marks_a_quick_run_as_not_a_thesis_result():
    markdown = tables.render_h2_report(h2_metrics())
    assert "dissertatsiya natijasi emas" in markdown


def test_the_h2_table_shows_an_unavailable_model_rather_than_dropping_it():
    """
    D48: BKT+IRT+Pre is in the table, saying why it did not run.

    A model that cannot run on data that *is* present gets its own sentence,
    not the "dataset missing" one — a different thing is missing, and the
    reason belongs in the cell once rather than twice.
    """
    markdown = tables.render_h2_report(h2_metrics())

    assert "BKT+IRT+Pre" in markdown
    assert f"{tables.NOT_APPLICABLE}: graf yo‘q" in markdown
    assert tables.NOT_RUN not in markdown


def test_each_section_is_numbered_once():
    """
    The provenance block is shared with the graph report, where it is section
    5; in the H2 table there are more sections before it.
    """
    import re

    for markdown in (tables.render_h2_report(h2_metrics()),):
        numbers = [int(match) for match in re.findall(r"^## (\d+)\.", markdown, re.M)]
        assert numbers == sorted(numbers)
        assert len(numbers) == len(set(numbers))


def test_the_h2_table_carries_the_confidence_level_and_the_hash():
    document = h2_metrics()
    markdown = tables.render_h2_report(document)

    assert "95%" in markdown
    assert document["provenance"]["sources"][0]["sha256"] in markdown
    assert "python -m experiments.h2 --quick" in markdown


def test_the_h2_table_reports_a_missing_auc_as_missing():
    """DKT's first_3 AUC is None in the fixture; it must not render as 0."""
    markdown = tables.render_h2_report(h2_metrics())
    early = [line for line in markdown.splitlines() if line.startswith("| DKT |")]

    assert any("—" in line for line in early)


def test_the_h2_table_says_pybkt_went_outside_chapter_twos_bounds():
    """The systematic difference between the two fitters, not a discrepancy."""
    markdown = tables.render_h2_report(h2_metrics())

    assert "G0" in markdown or "S0" in markdown
    assert "pyBKT" in markdown
