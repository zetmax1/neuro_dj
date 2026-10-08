"""
experiments/reproduce.py — the check that a rebuilt environment reproduces
an old H2 run (after the Ubuntu 26.04 reinstall).

Synthetic metrics documents only; the real comparison is run by hand on the
published --quick result and reported in REMEDIATION_PROGRESS.md.
"""

from __future__ import annotations

import copy
import json

from experiments import reproduce


def _model(auc: float) -> dict:
    return {
        "status": "ok",
        "fit": {"parameters": {"p0": 0.3}},
        "scores": {"all": {"auc": auc, "rmse": 0.43, "n": 100}, "first_3": {"auc": None}},
        "seconds": 1.5,
    }


def document() -> dict:
    names = ("BKT", "BKT+IRT (λ=0)", "Elo/Rasch", "PFA", "DKT", "AKT")
    fold = {
        "index": 0,
        "counts": {"train": 8, "validation": 2, "test": 2},
        "parameters": {"skills_fitted": 3, "grid_check": {"skills": 3}},
        "models": {name: _model(0.7 + index / 100) for index, name in enumerate(names)},
    }
    return {
        "quick": True,
        "split": {"seed": 1, "folds": 1},
        "folds": [fold],
        "pooled": {
            "models": {
                name: {"scores": {"all": {"auc": 0.7 + index / 100}},
                       "auc_interval": {"ci_low": 0.6, "ci_high": 0.8}}
                for index, name in enumerate(names)
            },
            "comparisons": [
                {"a": "BKT", "b": "PFA", "auc_a": 0.7, "auc_b": 0.73, "difference": -0.03,
                 "z": -2.0, "p": 0.04, "p_holm": 0.4},
                {"a": "BKT", "b": "DKT", "auc_a": 0.7, "auc_b": 0.74, "difference": -0.04,
                 "z": -3.0, "p": 0.003, "p_holm": 0.03},
            ],
        },
    }


def test_an_identical_run_is_reproduced():
    result = reproduce.compare(document(), document())

    assert result["reproduced"] and result["mismatches"] == []
    assert result["checked"] > 0 and result["added"] == 0


def test_a_classical_number_off_by_more_than_the_tolerance_fails():
    new = document()
    new["folds"][0]["models"]["PFA"]["scores"]["all"]["auc"] += 1e-8

    result = reproduce.compare(document(), new)
    assert not result["reproduced"]
    assert [item["where"] for item in result["mismatches"]] == ["folds[0]/PFA/scores/all/auc"]


def test_a_difference_within_the_tolerance_passes():
    new = document()
    new["pooled"]["models"]["BKT"]["auc_interval"]["ci_low"] += 5e-10

    assert reproduce.compare(document(), new)["reproduced"]


def test_dkt_and_akt_are_reported_not_checked():
    new = document()
    new["folds"][0]["models"]["DKT"]["scores"]["all"]["auc"] = 0.9
    new["pooled"]["models"]["AKT"]["scores"]["all"]["auc"] = 0.5
    new["pooled"]["comparisons"][1]["p"] = 0.5          # BKT vs DKT: not checked

    result = reproduce.compare(document(), new)
    assert result["reproduced"]
    reported = {item["where"]: item for item in result["reported"]}
    assert reported["folds[0]/DKT"]["difference"] == round(0.9 - 0.74, 6)
    assert reported["pooled/AKT"]["new_auc"] == 0.5


def test_holm_p_and_timings_are_not_compared():
    new = document()
    new["pooled"]["comparisons"][0]["p_holm"] = 0.9
    new["folds"][0]["models"]["BKT"]["seconds"] = 99.0

    assert reproduce.compare(document(), new)["reproduced"]


def test_a_key_the_new_run_adds_is_counted_and_one_it_drops_fails():
    new = document()
    new["folds"][0]["parameters"]["fit_log_likelihood"] = -12.5
    new["pooled"]["contrasts"] = [{"a": "x"}]
    result = reproduce.compare(document(), new)
    assert result["reproduced"] and result["added"] == 1

    dropped = document()
    del dropped["folds"][0]["parameters"]["skills_fitted"]
    result = reproduce.compare(document(), dropped)
    assert not result["reproduced"]
    assert result["mismatches"][0]["new"] == "missing"


def test_a_missing_model_or_fold_fails():
    new = document()
    del new["folds"][0]["models"]["Elo/Rasch"]
    assert not reproduce.compare(document(), new)["reproduced"]

    new = document()
    new["folds"] = []
    assert not reproduce.compare(document(), new)["reproduced"]


def test_a_full_run_is_not_compared_with_a_quick_one():
    new = document()
    new["quick"] = False
    assert not reproduce.compare(document(), new)["reproduced"]


def test_the_command_exits_by_the_result(tmp_path, capsys):
    old_dir, new_dir = tmp_path / "old", tmp_path / "new"
    for directory, payload in ((old_dir, document()), (new_dir, copy.deepcopy(document()))):
        directory.mkdir()
        (directory / "metrics.json").write_text(json.dumps(payload), encoding="utf-8")
    assert reproduce.main([str(old_dir), str(new_dir)]) == 0
    assert "reproduced: yes" in capsys.readouterr().out

    changed = document()
    changed["folds"][0]["models"]["BKT"]["scores"]["all"]["rmse"] = 0.5
    (new_dir / "metrics.json").write_text(json.dumps(changed), encoding="utf-8")
    assert reproduce.main([str(old_dir), str(new_dir)]) == 1
    assert "MISMATCH folds[0]/BKT/scores/all/rmse" in capsys.readouterr().out
