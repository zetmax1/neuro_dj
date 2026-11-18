"""
D71 — the post-hoc, descriptive H1/H3 analyses, on the synthetic Junyi fixture.

These numbers are not results; they pin the pipeline: both directories are
written and verify cell by cell (D48), the reproduction gate passes against
H1/H3 run on the same fixture and stops a run that does not reproduce them,
a finished fold is read back from the checkpoint, and the memory gate reads
/proc/meminfo the way D71 states.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments import d71, h1, h3, splits, tables
from experiments.datasets import junyi
from experiments.tests.conftest import FIXTURES, write_junyi_log

ARGS = ["--quick", "--no-verify", "--learners", "30", "--replicates", "20", "--workers", "1"]


@pytest.fixture(scope="module")
def world(tmp_path_factory) -> tuple[Path, Path, Path]:
    """The small Junyi fixture, and H1 and H3 run on it once for the module."""
    root = tmp_path_factory.mktemp("d71")
    data = root / "junyi"
    data.mkdir()
    table = data / junyi.EXERCISE_TABLE
    table.write_text((FIXTURES / "junyi_exercise_table_small.csv").read_text(encoding="utf-8"), encoding="utf-8")
    write_junyi_log(data / junyi.PROBLEM_LOG, table=table)
    h1_dir, h3_dir = root / "ref-h1", root / "ref-h3"
    assert h1.main([*ARGS, "--data", str(data), "--out", str(h1_dir)]) == 0
    assert h3.main([*ARGS, "--data", str(data), "--random-graphs", "2", "--out", str(h3_dir)]) == 0
    return data, h1_dir, h3_dir


def _written(root: Path) -> dict[str, Path]:
    return {path.parent.parent.name: path for path in root.glob("*/*/metrics.json")}


def test_both_directories_are_written_verified_and_marked_post_hoc(world, tmp_path):
    junyi_small, h1_dir, h3_dir = world
    root = tmp_path / "d71"
    code = d71.main([
        *ARGS, "--data", str(junyi_small), "--out", str(root), "--no-checkpoint",
        "--reference-h1", str(h1_dir), "--reference-h3", str(h3_dir),
    ])
    assert code == 0

    written = _written(root)
    assert set(written) == {"junyi-h1-posthoc-quick", "junyi-h3-lambda-quick"}
    for name, path in written.items():
        document = json.loads(path.read_text(encoding="utf-8"))
        markdown = (path.parent / "tables.md").read_text(encoding="utf-8")
        assert tables.verify(markdown, document) == [], name
        assert document["posthoc"] is True and document["descriptive"] is True
        assert "D61/D62 ning o‘qish qoidasi va hukmi o‘zgarmaydi" in markdown
        assert "dissertatsiya natijasi emas" in markdown
        assert "reading" not in document  # no verdict in a post-hoc result
        gate = document["reproduction_gate"]
        assert gate and all(check.get("equal", True) for check in gate)

    h1_doc = json.loads(written["junyi-h1-posthoc-quick"].read_text(encoding="utf-8"))
    for block in h1_doc["subset"].values():
        completeness = next(r for r in block["rules"] if r["rule"] == h1.COMPLETENESS)
        assert completeness["coverage"] in (1.0, None)  # S is defined by completeness
        assert [e["rule"] for e in block["equal_coverage"]] == list(d71.SUBSET_COMPARED)
    assert [p["tau"] for p in h1_doc["curve"]["3"]["points"]] == list(d71.TAU_CURVE)
    covered = [p["coverage"] for p in h1_doc["curve"]["3"]["points"]]
    assert covered == sorted(covered, reverse=True), "coverage must fall as τ rises"
    assert covered[0] == 1.0  # τ = 0 flags every event

    h3_doc = json.loads(written["junyi-h3-lambda-quick"].read_text(encoding="utf-8"))
    for block in h3_doc["by_k"].values():
        assert [row["lambda"] for row in block["rows"]] == list(d71.LAMBDAS)
        assert block["rows"][0]["arm"] == "grafsiz"


def test_the_gate_stops_a_run_that_does_not_reproduce_h1(world, tmp_path):
    junyi_small, h1_dir, h3_dir = world
    metrics = json.loads((h1_dir / "metrics.json").read_text(encoding="utf-8"))
    metrics["rules"][0]["flagged"] += 1
    broken = tmp_path / "broken-h1"
    broken.mkdir()
    (broken / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    root = tmp_path / "d71"
    code = d71.main([
        *ARGS, "--data", str(junyi_small), "--out", str(root), "--no-checkpoint",
        "--reference-h1", str(broken), "--reference-h3", str(h3_dir),
    ])
    assert code == 5
    assert not root.exists() or not any(root.rglob("metrics.json"))


def test_the_h3_gate_compares_an_arm_only_at_the_lambda_it_ran_at():
    reference_h1 = {"events": {"total": 1, "with_every_prerequisite_answered": 1}, "rules": []}
    reference_h3 = {
        "folds": [{"arms": {"asl": {"lambda": 0.25}, "grafsiz": {"lambda": 0.0}}},
                  {"arms": {"asl": {"lambda": 0.5}, "grafsiz": {"lambda": 0.0}}}],
        "pooled": {str(k): {"arms": {"grafsiz": {"scores": {"auc": 0.7, "n": 10}}}} for k in (3, 5)},
    }
    h1_doc = {"events": {"total": 1, "subset": 1}, "full_rules": []}
    h3_doc = {"by_k": {str(k): {"rows": [{"arm": "grafsiz", "scores": {"auc": 0.7000001, "n": 10}}]}
                       for k in (3, 5)}}
    checks = d71.gate(h1_doc, h3_doc, reference_h1=reference_h1, reference_h3=reference_h3)
    assert any("skipped" in check and check["check"] == "h3 asl" for check in checks)
    assert sum(1 for check in checks if check.get("equal")) == 2 + 4


def test_a_finished_fold_is_read_back_from_the_checkpoint(junyi_small, tmp_path):
    graph = junyi.load_graph(junyi_small / junyi.EXERCISE_TABLE, verify=False, sha256=False)
    log = junyi.load_log(junyi_small / junyi.PROBLEM_LOG, graph=graph,
                         learners=tuple(str(index) for index in range(1, 31)), sha256=False)
    rows = list(log.rows)
    folds = splits.learner_folds(list(log.learners), folds=2, validation_fraction=0.2, seed=1)
    key = {"spec": "D71", "test": True}

    first = d71.fit_checkpoint(tmp_path, key, enabled=True)
    fitted, resumed = d71.fit(folds, rows, workers=1, checkpoint=first, log=lambda *a: None)
    assert resumed == 0 and first.directory.name.startswith("d71-")

    again = d71.fit_checkpoint(tmp_path, key, enabled=True)
    refitted, resumed = d71.fit(folds, rows, workers=1, checkpoint=again, log=lambda *a: None)
    assert resumed == len(folds)
    assert {i: fit[0] for i, fit in refitted.items()} == {i: fit[0] for i, fit in fitted.items()}

    other = d71.fit_checkpoint(tmp_path, key | {"commit": "another"}, enabled=True)
    _, resumed = d71.fit(folds[:1], rows, workers=1, checkpoint=other, log=lambda *a: None)
    assert resumed == 0  # another key starts afresh


def test_the_memory_gate_reads_meminfo_as_d71_states():
    quiet = "MemAvailable: 7000000 kB\nSwapTotal: 4194300 kB\nSwapFree: 4194300 kB\n"
    swapped = "MemAvailable: 9000000 kB\nSwapTotal: 4194300 kB\nSwapFree: 3000000 kB\n"
    short = "MemAvailable: 5000000 kB\nSwapTotal: 4194300 kB\nSwapFree: 4194300 kB\n"
    assert d71.memory_condition(quiet)["ok"] is True
    assert d71.memory_condition(swapped)["ok"] is False
    assert d71.memory_condition(short)["ok"] is False
