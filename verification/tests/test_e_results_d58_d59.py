"""
Independent checks on the committed H2 and D55 results (D58, D59).

Three things, none of which re-runs an experiment:

1. **D58's refusals.** ``h2_bounds.load_reference`` is handed a reference that
   is wrong in one way at a time — a bounds result instead of H2, a quick run,
   another data file, another split, no commit, a dirty tree, an older grid,
   a missing directory — and must refuse each one. A gate that cannot refuse
   proves nothing about the run that passed it.

2. **The tables.** ``tables.verify`` is called here, by the verifier, on both
   committed results, and five values are drawn at random from each
   ``metrics.json`` and found in their own cell of ``tables.md``.

3. **Provenance.** Every commit a result names exists in this repository's
   history, and the result's own directory was committed.

Nothing here needs torch: the bounds module imports the neural arms lazily.
"""

from __future__ import annotations

import json
import random
import re
import subprocess
from pathlib import Path

import pytest
from django.conf import settings

REPO = Path(settings.BASE_DIR)
RESULTS = REPO / "experiments" / "results"
SEED: int = settings.VERIFICATION_SEED

H2_DIR = RESULTS / "assist09" / "20261010-060005"
BOUNDS_DIR = RESULTS / "assist09-bounds" / "20261011-183756"


def _metrics(directory: Path) -> dict:
    return json.loads((directory / "metrics.json").read_text(encoding="utf-8"))


def _committed_results() -> list[Path]:
    out = [d for d in (H2_DIR, BOUNDS_DIR) if (d / "metrics.json").exists()]
    if not out:
        pytest.skip("neither the H2 nor the D55 result is on disk")
    return out


# ---------------------------------------------------------------------------
# 1. D58 — what the reference gate refuses
# ---------------------------------------------------------------------------


class _Args:
    """The parts of the argument namespace ``load_reference`` reads."""

    def __init__(self, *, quick=False, seed=20261006, folds=5, validation_fraction=0.2):
        self.quick = quick
        self.seed = seed
        self.folds = folds
        self.validation_fraction = validation_fraction


class _Dataset:
    def __init__(self, sha256: str):
        self.sha256 = sha256


@pytest.fixture
def reference_inputs():
    """The real H2 reference plus the arguments under which it is accepted."""
    if not (H2_DIR / "metrics.json").exists():
        pytest.skip(f"{H2_DIR} is not on disk")
    document = _metrics(H2_DIR)
    split = document["split"]
    args = _Args(
        quick=bool(document.get("quick")), seed=split["seed"], folds=split["folds"],
        validation_fraction=split["validation_fraction"],
    )
    return document, _Dataset(document["dataset"]["sha256"]), args


def test_d58_the_real_reference_is_accepted(reference_inputs, tmp_path):
    from experiments import h2_bounds

    document, dataset, args = reference_inputs
    loaded = h2_bounds.load_reference(H2_DIR, dataset=dataset, args=args)
    assert loaded["commit"] == document["provenance"]["code_commit"]
    assert loaded["learners"] == document["split"]["learners"]
    assert loaded["pooled"]["BKT"] == pytest.approx(
        document["pooled"]["models"]["BKT"]["scores"]["all"]["auc"], abs=0.0
    )


def _broken(document: dict, how: str) -> dict:
    """One copy of the reference, wrong in exactly one way."""
    import copy

    out = copy.deepcopy(document)
    if how == "a bounds result":
        out["report"] = "h2_bounds"
    elif how == "another protocol":
        out["pooled"]["evaluation_protocol"] = "D53"
    elif how == "a quick run":
        out["quick"] = True
    elif how == "another data file":
        out["dataset"]["sha256"] = "0" * 64
    elif how == "another seed":
        out["split"]["seed"] = 1
    elif how == "another fold count":
        out["split"]["folds"] = 4
    elif how == "no commit":
        out["provenance"]["code_commit"] = ""
    elif how == "a dirty tree":
        out["provenance"]["tree_warnings"] = ["the tree changed during the run"]
    elif how == "an older grid":
        for fold in out["folds"]:
            fold["parameters"]["grid_candidates"] = 2160
    else:  # pragma: no cover - the parametrisation is closed
        raise AssertionError(how)
    return out


@pytest.mark.parametrize("how", [
    "a bounds result", "another protocol", "a quick run", "another data file",
    "another seed", "another fold count", "no commit", "a dirty tree", "an older grid",
])
def test_d58_a_wrong_reference_is_refused(reference_inputs, tmp_path, how):
    from experiments import h2_bounds

    document, dataset, args = reference_inputs
    directory = tmp_path / how.replace(" ", "-")
    directory.mkdir()
    (directory / "metrics.json").write_text(
        json.dumps(_broken(document, how)), encoding="utf-8"
    )

    with pytest.raises(h2_bounds.ReproductionFailed) as refused:
        h2_bounds.load_reference(directory, dataset=dataset, args=args)
    assert str(refused.value).startswith(f"reference {directory}")


def test_d58_a_missing_reference_is_refused(reference_inputs, tmp_path):
    from experiments import h2_bounds

    _, dataset, args = reference_inputs
    with pytest.raises(h2_bounds.ReproductionFailed, match="does not exist"):
        h2_bounds.load_reference(tmp_path / "nowhere", dataset=dataset, args=args)


def test_d58_the_committed_bounds_run_used_a_reference_that_passes_the_gate(
    reference_inputs,
):
    """
    The run on disk names a reference; that reference must still be acceptable
    today, under the committed run's own arguments.
    """
    if not (BOUNDS_DIR / "metrics.json").exists():
        pytest.skip(f"{BOUNDS_DIR} is not on disk")
    from experiments import h2_bounds

    document, dataset, args = reference_inputs
    bounds = _metrics(BOUNDS_DIR)
    named = REPO / bounds["reference"]["path"]
    assert named.resolve() == H2_DIR.resolve(), bounds["reference"]["path"]

    loaded = h2_bounds.load_reference(named, dataset=dataset, args=args)
    assert loaded["commit"] == bounds["reference"]["commit"]
    assert loaded["learners"] == bounds["reference"]["learners"]
    for model, value in bounds["reference"]["fold_1"].items():
        assert loaded["fold_1"][model] == pytest.approx(value, abs=0.0), model


# ---------------------------------------------------------------------------
# 2. the tables, verified here rather than taken on trust
# ---------------------------------------------------------------------------


def test_the_verifier_runs_tables_verify_on_both_results():
    from experiments import tables

    for directory in _committed_results():
        document = _metrics(directory)
        markdown = (directory / "tables.md").read_text(encoding="utf-8")
        where = directory.relative_to(REPO)
        assert tables.verify(markdown, document) == [], where
        positional = (
            tables.verify_h2_positions if document["report"] == "h2"
            else tables.verify_h2_bounds_positions
        )
        assert positional(markdown, document) == [], where


def _leaf_numbers(node, path="") -> list[tuple[str, float]]:
    """Every number in the document, with the path that leads to it."""
    out: list[tuple[str, float]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            out += _leaf_numbers(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            out += _leaf_numbers(value, f"{path}[{index}]")
    elif isinstance(node, bool) or node is None:
        pass
    elif isinstance(node, (int, float)):
        out.append((path, float(node)))
    return out


def test_five_random_values_of_each_metrics_json_are_in_the_right_cell():
    """
    A spot check of the whole pipeline from the other end: five AUC-like values
    are drawn at random from each result and have to appear, at some rounding,
    in a row of ``tables.md`` that also names their own model or setting. A
    value printed in the wrong row would pass "the number is somewhere in the
    file" and fail here.
    """
    for directory in _committed_results():
        document = _metrics(directory)
        markdown = (directory / "tables.md").read_text(encoding="utf-8")
        where = directory.relative_to(REPO)

        # Candidates are the values the tables are meant to print: H2's pooled
        # block and D55's per-setting block. Per-fold detail such as
        # ``folds[0]/models/X/scores/first_3/accuracy`` is in metrics.json but
        # not in any table, and drawing from it would test the wrong claim.
        printed_paths = re.compile(
            r"^/pooled/models/[^/]+/(scores/(all|first_3|first_5)|auc_interval|first_in_order)/"
            r"(auc|rmse|accuracy|estimate|ci_low|ci_high)$"
            r"|^/settings\[\d+\]/models/[^/]+/(scores|auc_interval)/"
            r"(auc|rmse|accuracy|estimate|ci_low|ci_high)$"
            r"|^/settings\[\d+\]/difference/bootstrap/(estimate|ci_low|ci_high)$"
        )
        candidates = [
            (path, value) for path, value in _leaf_numbers(document)
            if printed_paths.match(path) and 0.0 < abs(value) < 1.0
        ]
        assert len(candidates) >= 5, (where, len(candidates))
        drawn = random.Random(SEED).sample(candidates, 5)

        rows = [line for line in markdown.splitlines() if line.startswith("|")]
        for path, value in drawn:
            owner = _owner_of(path, document)
            printed = [
                row for row in rows
                if owner in row and any(
                    _cell_shows(cell, value) for cell in row.split("|")
                )
            ]
            assert printed, (
                f"{where}: {path} = {value} does not appear in any row naming {owner!r}"
            )


def _owner_of(path: str, document: dict) -> str:
    """The model or setting name the value belongs to, as the table prints it."""
    model = re.search(r"/models/([^/]+)", path)
    if model:
        return model.group(1)
    setting = re.search(r"/settings\[(\d+)\]", path)
    if setting:
        return document["settings"][int(setting.group(1))]["name"]
    return ""


def _cell_shows(cell: str, value: float) -> bool:
    cell = cell.strip()
    for token in re.findall(r"-?\d+\.\d+", cell):
        places = len(token.split(".")[1])
        if round(value, places) == float(token):
            return True
    return False


# ---------------------------------------------------------------------------
# 3. provenance against the repository's own history
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=60
    )
    assert done.returncode == 0, done.stderr[:300]
    return done.stdout.strip()


def test_every_commit_a_result_names_exists_in_the_history():
    for directory in _committed_results():
        document = _metrics(directory)
        where = directory.relative_to(REPO)
        provenance = document["provenance"]
        commits = {provenance["code_commit"]}
        for end in ("git_start", "git_end"):
            if provenance.get(end):
                commits.add(provenance[end]["commit"])
        if document["report"] == "h2_bounds":
            commits.add(document["reference"]["commit"])
        for commit in commits:
            assert re.fullmatch(r"[0-9a-f]{7,40}", commit), (where, commit)
            kind = _git("cat-file", "-t", commit)
            assert kind == "commit", (where, commit, kind)


def test_the_result_directories_are_committed_and_unmodified():
    for directory in _committed_results():
        relative = directory.relative_to(REPO)
        listed = _git("ls-files", str(relative)).splitlines()
        assert sorted(Path(p).name for p in listed) == [
            "env.txt", "metrics.json", "tables.md",
        ], (relative, listed)
        assert _git("status", "--porcelain", str(relative)) == "", (
            f"{relative} has uncommitted changes"
        )


def test_the_recorded_run_was_clean_at_both_ends():
    for directory in _committed_results():
        provenance = _metrics(directory)["provenance"]
        where = directory.relative_to(REPO)
        assert provenance["code_dirty"] is False, where
        assert provenance["tree_changed"] is False, where
        assert provenance["tree_warnings"] == [], where
        for end in ("git_start", "git_end"):
            assert provenance[end]["dirty"] is False, (where, end)
            assert provenance[end]["changes"] == [], (where, end)
        assert provenance["git_start"]["commit"] == provenance["git_end"]["commit"], where


def test_the_env_txt_and_metrics_json_tell_the_same_story():
    for directory in _committed_results():
        document = _metrics(directory)
        env = (directory / "env.txt").read_text(encoding="utf-8")
        where = directory.relative_to(REPO)
        provenance = document["provenance"]
        assert provenance["code_commit"] in env, where
        assert provenance["command"] in env, where
        for source in provenance["sources"]:
            assert source["sha256"] in env, (where, source["sha256"])
        for name, version in provenance["packages"].items():
            assert f"{name} {version}" in env, (where, name)
