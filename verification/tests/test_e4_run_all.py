"""
V-E4 — ``experiments/run_all.py --quick`` (stage 8, D62-12).

The specification of V-E4 reads: "run_all.py --quick runs on simulated data;
the parameter-recovery test passes and the result carries the 'simulated — not
a thesis result' mark". What landed differs on purpose, and this file checks
what landed against the decisions that changed it:

- **real data, not simulated** (D48: a number comes only from a run on open,
  real data; D13: the platform's simulator is not used for results). The
  quick pass therefore runs on ASSISTments 2009 or Junyi, and the mark is
  "``--quick`` ishga tushirish — dissertatsiya natijasi emas";
- **parameter recovery** lives with the calibration it tests
  (``neuro_model/tests/test_calibrate.py::test_the_generating_parameters_are_recovered_closely``),
  not in the pipeline run;
- **dispatcher only** (D62-12): ``run_all`` owns no metric and no result
  directory; each hypothesis keeps its own ``metrics.json``.

Running ``--quick`` itself takes 18-24 minutes and writes under
``experiments/results/``, which the verifier does not write to, so the run is
checked through the committed quick results and through a spy on each
hypothesis's ``main``.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from django.conf import settings

REPO = Path(settings.BASE_DIR)
RESULTS = REPO / "experiments" / "results"
QUICK_MARK = "`--quick` ishga tushirish — dissertatsiya natijasi emas"


def _main(argv, capsys):
    from experiments import run_all

    code = run_all.main(argv)
    return code, capsys.readouterr()


@pytest.mark.parametrize(
    ("dataset", "runs", "unavailable"),
    [("assist09", {"h2"}, {"h1", "h3"}), ("junyi", {"h1", "h3"}, {"h2"})],
)
def test_v_e4_the_plan_follows_what_each_dataset_can_carry(dataset, runs, unavailable, capsys):
    """D62-12 / D53 / D61: a hypothesis a dataset cannot carry is said, with its reason."""
    from experiments import run_all

    args = run_all.build_parser().parse_args(["--dataset", dataset, "--quick"])
    steps = {step["hypothesis"]: step for step in run_all.plan(args)}
    assert {h for h, s in steps.items() if s["status"] == "runs"} == runs
    assert {h for h, s in steps.items() if s["status"] == "unavailable"} == unavailable
    for name in unavailable:
        assert steps[name]["reason"].strip(), name

    before = sorted(p.relative_to(RESULTS) for p in RESULTS.glob("*/*"))
    code, out = _main(["--dataset", dataset, "--quick", "--dry-run"], capsys)
    assert code == 0
    for name in unavailable:
        assert f"{name}: ishga tushirilmadi — " in out.out
    for name in runs:
        assert f"{name}: ishga tushiriladi" in out.out
    assert sorted(p.relative_to(RESULTS) for p in RESULTS.glob("*/*")) == before, "dry run wrote a result"


@pytest.mark.parametrize("argv", [
    ["--dataset", "nowhere", "--dry-run"],
    ["--dataset", "assist09", "--models", "nope", "--dry-run"],
    ["--dataset", "junyi", "--hypotheses", "h9", "--dry-run"],
])
def test_v_e4_an_unknown_name_is_an_error_not_an_empty_run(argv, capsys):
    code, out = _main(argv, capsys)
    assert code == 2
    assert "unknown" in out.err


def test_v_e4_quick_reaches_each_runnable_hypothesis_and_stops_on_failure(monkeypatch, capsys):
    """--quick is forwarded to every runnable hypothesis, in order; a non-zero exit stops the chain."""
    from experiments import h1, h2, h3

    calls: list[tuple[str, list[str]]] = []

    def spy(name, code=0):
        def main(argv):
            calls.append((name, list(argv)))
            return code
        return main

    monkeypatch.setattr(h1, "main", spy("h1"))
    monkeypatch.setattr(h2, "main", spy("h2"))
    monkeypatch.setattr(h3, "main", spy("h3"))
    code, _ = _main(["--dataset", "junyi", "--quick", "--workers", "2"], capsys)
    assert code == 0
    assert calls == [("h1", ["--quick", "--workers", "2"]), ("h3", ["--quick", "--workers", "2"])]

    calls.clear()
    code, _ = _main(["--dataset", "assist09", "--quick", "--models", "bkt,dkt"], capsys)
    assert code == 0
    assert calls == [("h2", ["--quick", "--models", "bkt,dkt"])]

    calls.clear()
    monkeypatch.setattr(h1, "main", spy("h1", code=3))
    code, out = _main(["--dataset", "junyi", "--quick"], capsys)
    assert code == 3 and calls == [("h1", ["--quick"])], "h3 must not run after h1 failed"
    assert "h1 exited with 3" in out.err


def _quick_results() -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {}
    for path in sorted(RESULTS.glob("*-quick/*/metrics.json")):
        metrics = json.loads(path.read_text(encoding="utf-8"))
        out.setdefault(metrics.get("report"), []).append(path.parent)
    return out


@pytest.mark.parametrize("report", ["h1", "h2", "h3"])
def test_v_e4_every_hypothesis_run_all_dispatches_has_a_committed_quick_result(report):
    """
    The quick pass of each hypothesis exists, is committed, is marked "not a
    thesis result" in both files, and its tables verify against its metrics.
    """
    from experiments import tables

    found = _quick_results().get(report)
    assert found, f"no committed --quick result for {report}"
    for directory in found:
        where = directory.relative_to(REPO)
        metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
        text = (directory / "tables.md").read_text(encoding="utf-8")
        assert metrics["quick"] is True and metrics["thesis_result"] is False, where
        assert QUICK_MARK in text, where
        assert "--quick" in metrics["provenance"]["command"], where
        tracked = subprocess.run(
            ["git", "-C", str(REPO), "ls-files", "--error-unmatch", str(directory / "metrics.json")],
            capture_output=True,
        )
        assert tracked.returncode == 0, f"{where} is not committed"
        assert tables.verify(text, metrics) == [], where


def test_v_e4_parameter_recovery_lives_with_the_calibration():
    """The recovery test V-E4 asks for exists where the calibration is (not in the pipeline)."""
    source = (REPO / "neuro_model" / "tests" / "test_calibrate.py").read_text(encoding="utf-8")
    assert re.search(r"^def test_the_generating_parameters_are_recovered_closely\(", source, re.M)
