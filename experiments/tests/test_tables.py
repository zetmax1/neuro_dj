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


def test_only_declared_phrases_may_carry_numbers_in_the_prose():
    """
    The allow-list is tiny, fixed, and made of whole phrases, each admitted by
    a named decision. If it grows, this test fails, which is the point: a new
    phrase needs a new D-numbered decision and a visible edit here.

    It held bare numbers until the verification report's K2 ("2.2", "2.3",
    "2.4", "3.3", "2016"), and grew from three to five without a decision. A
    bare number is allowed everywhere it appears; a phrase only where it is
    the citation.
    """
    import re
    from pathlib import Path

    assert dict(tables.CITATIONS) == {
        "3.3-bo‘limga": "D52",
        "Algoritm 2.3": "D52",
        "EDM 2016": "D53",
    }
    decisions = (Path(__file__).resolve().parents[2] / "NEUROLEARN_B8B.md").read_text(encoding="utf-8")
    for phrase, decision in tables.CITATIONS.items():
        assert re.fullmatch(r"D\d+", decision), phrase
        assert f"### {decision} " in decisions, f"{phrase}: {decision} is not a decision in NEUROLEARN_B8B.md"
    with pytest.raises(TypeError):
        tables.CITATIONS["2017"] = "D99"


def test_a_citation_number_outside_its_phrase_is_caught(tiny_graphml):
    """ "2016" is a year inside "EDM 2016" and a stray number anywhere else."""
    document, _ = metrics_of(tiny_graphml)
    markdown = tables.render_graph_report(document)

    assert tables.verify(markdown + "\nXiong va boshq. (EDM 2016)\n", document) == []
    assert tables.verify(markdown + "\n| DKT | 2016 |\n", document) == ["2016"]
    assert tables.verify(markdown + "\nqarang: 3.3\n", document) == ["3.3"]


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
                    "cold_rows": 0,
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
                    "cold_rows": 200,
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
        "grid_check": {
            "folds": 5,
            "fits": 405,
            "bounds": {"g_max": 0.3, "s_max": 0.1},
            "parameters": {
                "p0": {
                    "admissible_values": [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5],
                    "lowest": 0.05, "highest": 0.5,
                    "at_lowest": 12, "at_highest": 190,
                    "share_at_highest": 0.4691, "share_at_lowest": 0.0296,
                    "ceiling_is_chapter_two": False,
                },
                "g0": {
                    "admissible_values": [0.05, 0.1, 0.15, 0.2, 0.25],
                    "lowest": 0.05, "highest": 0.25,
                    "at_lowest": 20, "at_highest": 300,
                    "share_at_highest": 0.7407, "share_at_lowest": 0.0494,
                    "ceiling_is_chapter_two": True,
                },
            },
        },
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


def test_the_grid_check_section_distinguishes_who_sets_the_ceiling():
    """
    Saturation on P0 means the grid is too narrow. Saturation on P(G) means
    chapter II's cap is binding, which is a finding rather than a defect — so
    the table must not present the two the same way.
    """
    document = h2_metrics()
    markdown = tables.render_h2_report(document)

    assert "Grid tekshiruvi" in markdown
    grid_rows = [line for line in markdown.splitlines() if line.startswith(("| P0 |", "| P(G) |"))]
    assert len(grid_rows) == 2
    assert grid_rows[0].rstrip().endswith("grid |")
    assert grid_rows[1].rstrip().endswith("II bob |")
    assert tables.verify(markdown, document) == []


def test_the_h2_table_verifies_clean_when_the_sanity_warning_fires():
    """
    The gap that let a stray number through for two and a half hours: the
    fixture above has ``within_range: True``, so the warning block never
    rendered in a test — and that block carried a year in its prose, which the
    D48 check correctly rejected only at the end of a real run.

    Every conditional block of the table needs its own case, or the check
    only guards the paths the happy fixture happens to take.
    """
    document = h2_metrics()
    document["sanity"]["auc"] = 0.6412
    document["sanity"]["within_range"] = False
    markdown = tables.render_h2_report(document)

    assert "Ogohlantirish" in markdown
    assert tables.verify(markdown, document) == []


def test_the_h2_table_verifies_clean_with_no_comparisons_and_no_pybkt():
    """The other conditional branches: the empty-row paths."""
    document = h2_metrics()
    document["pooled"]["comparisons"] = []
    document["pybkt_cross_check"] = {"status": "unavailable", "reason": "pyBKT yo‘q"}
    document["grid_check"] = {}
    document["folds"] = []
    markdown = tables.render_h2_report(document)

    assert tables.verify(markdown, document) == []


def test_the_h2_table_verifies_clean_for_a_full_run():
    """A full run has no --quick banner, which is its own branch."""
    document = h2_metrics()
    document["quick"] = False
    markdown = tables.render_h2_report(document)

    assert "dissertatsiya natijasi emas" not in markdown
    assert tables.verify(markdown, document) == []


def test_the_graph_table_verifies_clean_when_a_graph_is_cyclic_and_absent_together():
    """The same lesson for the 8b-1 table: mixed statuses in one document."""
    document = {
        "provenance": {"command": "python -m experiments.graph_report", "sources": []},
        "graphs": [
            {"name": "A", "status": "not_run", "reason": "ma’lumot yo‘q",
             "edge_direction": "prereq_to_dependent", "path": "/x"},
            {"name": "B", "status": "ok", "edge_direction": "prereq_to_dependent",
             "source": {"sha256": "a" * 64, "name": "B", "path": "/b", "bytes": 10},
             "nodes": 5, "raw_edges": 6, "edges": 5, "self_loops": 1, "isolated": 0,
             "weak_components": 1, "is_dag": False, "scc_nontrivial": 1,
             "scc_merged_nodes": 3, "scc_merged": [["b", "c", "d"]],
             "ordered_nodes": 3, "longest_path": 2,
             "redundant_edges": 0, "redundant_edge_list": [],
             "readiness": {"samples": 0, "repeats": 2,
                           "incremental_touched_median": 0,
                           "incremental_touched_max": 0, "full_touched": 3,
                           "note": "nothing to propagate"}},
        ],
    }
    markdown = tables.render_graph_report(document)

    assert tables.NOT_RUN in markdown
    assert tables.verify(markdown, document) == []


# ---------------------------------------------------------------------------
# The H2 tables, cell by cell (verification report K1)
# ---------------------------------------------------------------------------

# Each edit puts a number that *is* in the metrics into a cell whose own key
# holds another one — the edit the numeric scan cannot see.
H2_SWAPS = [
    ("§1", "| BKT | 0.67 [0.651, 0.689] |", "| BKT | 0.731 [0.651, 0.689] |"),   # DKT's AUC
    ("§1", "| DKT | 0.731 [0.71, 0.75] | 0.45 |", "| DKT | 0.731 [0.71, 0.75] | 0.448 |"),  # BKT's RMSE
    ("§2", "| BKT | 0.67 | 0.64 | 0.65 |", "| BKT | 0.67 | 0.69 | 0.65 |"),   # DKT's first-5
    ("§3", "| DKT | BKT | 0.731 | 0.67 |", "| DKT | BKT | 0.67 | 0.731 |"),   # A and B swapped
    ("§4", "| BKT | 0.665 |", "| BKT | 0.67 |"),                             # pooled for the fold
    ("§5", "- DKT AUC: 0.731", "- DKT AUC: 0.67"),                           # BKT's AUC
    ("§6", "| 12 | 190 | 0.469 | grid |", "| 190 | 12 | 0.469 | grid |"),   # lowest and highest swapped
    ("§7", "| 47 | 4210 | 0.3 / 0.572 |", "| 47 | 4210 | 0.572 / 0.3 |"),   # grid and EM swapped
]


@pytest.mark.parametrize("section, before, after", H2_SWAPS)
def test_a_cell_holding_another_keys_number_is_caught(section, before, after):
    document = h2_metrics()
    markdown = tables.render_h2_report(document)
    assert before in markdown
    tampered = markdown.replace(before, after, 1)

    problems = tables.verify(tampered, document)
    # The numeric scan alone lets it through: every number is in the metrics.
    assert all(problem.startswith("§") for problem in problems), problems
    assert any(problem.startswith(section) for problem in problems), problems


def test_a_dropped_model_row_is_caught():
    document = h2_metrics()
    markdown = tables.render_h2_report(document)
    row = next(line for line in markdown.splitlines() if line.startswith("| DKT | 0.731 ["))

    problems = tables.verify(markdown.replace(row + "\n", "", 1), document)
    assert any(problem.startswith("§1 rows") for problem in problems), problems


def test_a_missing_value_is_a_dash_not_a_zero():
    """
    An RMSE the metrics do not have used to render as 0 — a number the run
    never produced. It is a dash now, and a 0 in its place is caught.
    """
    document = h2_metrics()
    del document["pooled"]["models"]["BKT"]["scores"]["all"]["rmse"]
    markdown = tables.render_h2_report(document)

    assert "| BKT | 0.67 [0.651, 0.689] | — |" in markdown
    assert tables.verify(markdown, document) == []
    zeroed = markdown.replace("| BKT | 0.67 [0.651, 0.689] | — |", "| BKT | 0.67 [0.651, 0.689] | 0 |")
    assert any(problem.startswith("§1 BKT RMSE") for problem in tables.verify(zeroed, document))


def test_writing_an_h2_table_with_a_misplaced_cell_is_refused(tmp_path):
    document = h2_metrics()

    def misplaced(metrics):
        return tables.render_h2_report(metrics).replace(*H2_SWAPS[0][1:], 1)

    with pytest.raises(ValueError, match="§1 BKT AUC"):
        tables.write(tmp_path / "out", document, "env", renderer=misplaced)
    assert not (tmp_path / "out").exists()


def test_the_published_results_verify_cell_by_cell():
    """Every tables.md under experiments/results/ passes the full check."""
    from pathlib import Path

    results = Path(__file__).resolve().parents[1] / "results"
    found = sorted(results.glob("*/*/tables.md"))
    if not found:
        pytest.skip("no published result in experiments/results/")
    for path in found:
        metrics = json.loads((path.parent / "metrics.json").read_text(encoding="utf-8"))
        assert tables.verify(path.read_text(encoding="utf-8"), metrics) == [], path
