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
    assert tables.CITATIONS == frozenset({"2.2", "2.3", "3.3"})


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
    document = {"a": 0.7312, "b": 98, "c": "0.9999"}
    allowed = tables.allowed_numbers(document)

    assert "0.731" in allowed      # fmt
    assert "0.7312" in allowed     # raw
    assert "98" in allowed
    assert "0.9999" not in allowed  # a string is not a number of the metrics


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
