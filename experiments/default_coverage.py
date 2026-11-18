"""
experiments/default_coverage.py — how much of an H2 run the default BKT
parameters carried.

    python -m experiments.default_coverage experiments/results/assist09/<timestamp>

A skill whose fitting set (train + validation) holds fewer than
``MIN_ANSWERS_TO_FIT`` answers keeps the defaults; so does a skill the
fitting set does not have at all. ``metrics.json`` records how many skills
kept them per fold (``parameters.skills_kept_defaults``) but not how many
answers those skills hold. This rebuilds each fold from the run's own record
— the dataset file (its sha256 must match), the quick cap, the seed, the
fold count and the validation fraction — and counts:

- the skills that kept the defaults, which must equal the run's count, or
  the script stops (a skill whose grid search returned nothing would be
  missed by the answer-count rule alone);
- the test answers the BKT models predicted with default parameters (a
  skill that kept them, or one absent from the fitting set), per fold and
  pooled — the share of the scored answers they make up;
- the fitting answers of the skills that kept them.

Nothing is fitted; the result is printed, and with ``--json`` as JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from experiments import splits
from experiments.datasets import assist09
from experiments.models.classical import MIN_ANSWERS_TO_FIT


def coverage(metrics: dict, rows: list) -> dict:
    split = metrics["split"]
    learners = list(dict.fromkeys(row.user_id for row in rows))
    if metrics.get("quick"):
        learners = learners[:split["learners"]]
        rows = splits.subset(rows, learners)
    if len(learners) != split["learners"]:
        raise ValueError(f"{len(learners)} learners, the run had {split['learners']}")
    folds = splits.learner_folds(
        learners, folds=split["folds"], validation_fraction=split["validation_fraction"],
        seed=split["seed"],
    )

    out: dict = {"min_answers_to_fit": MIN_ANSWERS_TO_FIT, "folds": []}
    totals = {"test_answers": 0, "test_answers_with_defaults": 0,
              "fitting_answers": 0, "fitting_answers_of_default_skills": 0}
    for fold, recorded in zip(folds, metrics["folds"]):
        fitting = splits.subset(rows, fold.fitting)
        test = splits.subset(rows, fold.test)
        counts: dict[str, int] = {}
        for row in fitting:
            counts[row.skill_id] = counts.get(row.skill_id, 0) + 1
        kept = {skill for skill, count in counts.items() if count < MIN_ANSWERS_TO_FIT}
        expected = recorded["parameters"]["skills_kept_defaults"]
        if len(kept) != expected:
            raise ValueError(
                f"fold {fold.index + 1}: {len(kept)} skills under the answer threshold, "
                f"the run kept defaults for {expected}"
            )
        with_defaults = [row for row in test if row.skill_id in kept or row.skill_id not in counts]
        entry = {
            "fold": fold.index + 1,
            "skills_kept_defaults": len(kept),
            "test_skills_absent_from_fitting": len({row.skill_id for row in test} - set(counts)),
            "test_answers": len(test),
            "test_answers_with_defaults": len(with_defaults),
            "fitting_answers": len(fitting),
            "fitting_answers_of_default_skills": sum(counts[skill] for skill in kept),
        }
        entry["test_share_with_defaults"] = round(
            entry["test_answers_with_defaults"] / entry["test_answers"], 6)
        out["folds"].append(entry)
        for key in totals:
            totals[key] += entry[key]
    totals["test_share_with_defaults"] = round(
        totals["test_answers_with_defaults"] / totals["test_answers"], 6)
    totals["fitting_share_of_default_skills"] = round(
        totals["fitting_answers_of_default_skills"] / totals["fitting_answers"], 6)
    out["pooled"] = totals
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("result", type=Path, help="an H2 result directory")
    parser.add_argument("--data", default=None, help="as.csv (default: the path the run recorded)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    metrics = json.loads((args.result / "metrics.json").read_text(encoding="utf-8"))
    recorded = metrics["dataset"]
    dataset = assist09.load(args.data or recorded["path"], original_only=recorded["original_only"])
    if dataset.sha256 != recorded["sha256"]:
        print(f"the data file is not the one the run used: {dataset.sha256}", file=sys.stderr)
        return 2
    result = coverage(metrics, list(dataset.rows))
    result["result"] = str(args.result)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print("fold | skills kept defaults | test answers | with defaults | share | "
          "fitting answers of default skills")
    for entry in result["folds"]:
        print(f"{entry['fold']} | {entry['skills_kept_defaults']} | {entry['test_answers']} | "
              f"{entry['test_answers_with_defaults']} | {entry['test_share_with_defaults']} | "
              f"{entry['fitting_answers_of_default_skills']} / {entry['fitting_answers']}")
    pooled = result["pooled"]
    print(f"pooled | — | {pooled['test_answers']} | {pooled['test_answers_with_defaults']} | "
          f"{pooled['test_share_with_defaults']} | {pooled['fitting_answers_of_default_skills']} / "
          f"{pooled['fitting_answers']} ({pooled['fitting_share_of_default_skills']})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
