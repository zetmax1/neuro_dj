"""
experiments/default_coverage.py — the answers the default BKT parameters
carried in an H2 run. Synthetic rows; the real numbers are in
REMEDIATION_PROGRESS.md, computed on the published full result.
"""

from __future__ import annotations

import pytest

from experiments import splits
from experiments.datasets.assist09 import Interaction
from experiments.default_coverage import coverage
from experiments.models.classical import MIN_ANSWERS_TO_FIT


def rows_with(skill_answers: dict[str, int], learners: int = 20) -> list[Interaction]:
    """Each skill gets this many answers in total, spread over the learners in turn."""
    rows, order = [], 0
    for skill, total in skill_answers.items():
        for index in range(total):
            order += 1
            rows.append(Interaction(
                user_id=str(index % learners), order_id=order, problem_id=f"p{skill}",
                skill_id=skill, correct=index % 3 != 0, original=True,
            ))
    rows.sort(key=lambda row: (int(row.user_id), row.order_id))
    return rows


def run_record(rows, *, folds=2, seed=7, fraction=0.25) -> dict:
    """What an H2 run records, with the kept-defaults count computed the run's way."""
    learners = list(dict.fromkeys(row.user_id for row in rows))
    out = {"quick": False, "split": {"learners": len(learners), "folds": folds, "seed": seed,
                                     "validation_fraction": fraction}, "folds": []}
    for fold in splits.learner_folds(learners, folds=folds, validation_fraction=fraction, seed=seed):
        counts: dict[str, int] = {}
        for row in splits.subset(rows, fold.fitting):
            counts[row.skill_id] = counts.get(row.skill_id, 0) + 1
        kept = sum(1 for count in counts.values() if count < MIN_ANSWERS_TO_FIT)
        out["folds"].append({"parameters": {"skills_kept_defaults": kept}})
    return out


def test_a_rare_skills_answers_are_counted_as_carried_by_the_defaults():
    rows = rows_with({"big": 400, "rare": 20})
    result = coverage(run_record(rows), rows)

    for entry, fold in zip(result["folds"], splits.learner_folds(
            list(dict.fromkeys(row.user_id for row in rows)), folds=2, validation_fraction=0.25, seed=7)):
        test = splits.subset(rows, fold.test)
        assert entry["skills_kept_defaults"] == 1
        assert entry["test_answers"] == len(test)
        assert entry["test_answers_with_defaults"] == sum(1 for row in test if row.skill_id == "rare")
    pooled = result["pooled"]
    assert pooled["test_answers"] == len(rows)
    assert pooled["test_answers_with_defaults"] == 20
    assert pooled["test_share_with_defaults"] == round(20 / len(rows), 6)


def test_a_skill_absent_from_fitting_counts_as_defaults_too():
    rows = rows_with({"big": 400})
    learners = list(dict.fromkeys(row.user_id for row in rows))
    fold = splits.learner_folds(learners, folds=2, validation_fraction=0.25, seed=7)[0]
    learner = fold.test[0]
    rows.append(Interaction(user_id=learner, order_id=10_000, problem_id="x", skill_id="only-test",
                            correct=1, original=True))
    result = coverage(run_record(rows), rows)

    assert result["folds"][0]["test_skills_absent_from_fitting"] == 1
    assert result["folds"][0]["test_answers_with_defaults"] == 1
    assert result["folds"][0]["skills_kept_defaults"] == 0


def test_a_count_that_disagrees_with_the_run_stops():
    rows = rows_with({"big": 400, "rare": 20})
    record = run_record(rows)
    record["folds"][1]["parameters"]["skills_kept_defaults"] += 1

    with pytest.raises(ValueError, match="fold 2"):
        coverage(record, rows)


def test_a_quick_run_is_rebuilt_on_its_own_learners():
    rows = rows_with({"big": 400, "rare": 20})
    learners = list(dict.fromkeys(row.user_id for row in rows))[:12]
    quick_rows = splits.subset(rows, learners)
    record = run_record(quick_rows)
    record["quick"] = True

    assert coverage(record, rows)["pooled"]["test_answers"] == len(quick_rows)
