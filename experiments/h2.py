"""
experiments/h2.py — H2 on ASSISTments 2009 (D53).

Six models on identical data, five folds by learner, and every number that
comes out of it recorded with the sha256 of the file it was computed from
(D48).

    python -m experiments.h2 --quick
    python -m experiments.h2

The models are BKT, BKT+IRT (λ=0), Elo/Rasch, PFA, DKT and AKT. BKT+IRT+Pre
is **not** run: it needs a prerequisite graph and ASSISTments has none, so it
appears in the table as "graf yo‘q" rather than being dropped. The first two
and the unavailable third are one piece of code under three flag settings
(``experiments.models.classical.BKTFamily``), which is the whole point of the
ablation: the model being measured is the model the platform runs.

What each fold does:

1. fit the per-skill BKT parameters on train + validation, once, and share
   them with every flag variant;
2. fit each model, giving the neural ones the validation set for early
   stopping — the test fold is not touched until step 3;
3. predict the test fold, streaming each learner's answers in order so every
   prediction is made before its answer is seen;
4. score: AUC, RMSE, accuracy, over everything and over each learner's first
   3 and first 5 answers.

Across folds the predictions are pooled per model, so the interval and the
pairwise tests are computed once on the whole dataset rather than averaged
over five smaller estimates. The bootstrap resamples **learners**; DeLong is
paired and Holm corrects the family of pairs.

One sanity bound, and it is a warning rather than a test (D53): on
de-duplicated ASSISTments, Xiong et al. (EDM 2016) report DKT at 0.73–0.75.
A value far outside that says the cleaning is wrong, not that the model is
interesting, so it is written into the metadata where it cannot be missed.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import asdict
from pathlib import Path

from experiments import metrics, splits, tables
from experiments.datasets import DatasetMissing, assist09
from experiments.models import Unavailable
from experiments.models.classical import PFA, BKTFamily, EloRasch
from experiments.provenance import Provenance, Source, results_dir

# Xiong et al. (EDM 2016), DKT on ASSISTments 2009 with duplicates removed.
DKT_SANITY_RANGE = (0.70, 0.80)
DKT_LITERATURE_RANGE = (0.73, 0.75)

QUICK_LEARNERS = 500
QUICK_EPOCHS = 3
FULL_EPOCHS = 10


def build_models(params, *, epochs: int, seed: int) -> list:
    """
    The six models of D53, in table order. Built per fold, because each one
    carries fitted state.
    """
    from experiments.models.neural import AKTModel, DKTModel

    return [
        BKTFamily("BKT", use_irt=False, use_prereq_init=False, params=params),
        BKTFamily("BKT+IRT (λ=0)", use_irt=True, use_prereq_init=False, params=params),
        BKTFamily("BKT+IRT+Pre", use_irt=True, use_prereq_init=True, params=params),
        EloRasch(),
        PFA(seed=seed),
        DKTModel(epochs=epochs, seed=seed),
        AKTModel(epochs=epochs, seed=seed),
    ]


def run_fold(fold, rows, *, epochs: int, seed: int, log=print) -> tuple[dict, dict]:
    """
    One fold. Returns (per-model fold report, per-model pooled predictions).

    The parameters are fitted on train + validation so that no model sees the
    test fold before step 3, and the neural models get the validation set for
    early stopping.
    """
    from experiments.models.classical import fit_skill_params

    train = splits.subset(rows, fold.train)
    validation = splits.subset(rows, fold.validation)
    test = splits.subset(rows, fold.test)
    fitting = splits.subset(rows, fold.fitting)

    started = time.perf_counter()
    params, params_metadata = fit_skill_params(fitting)
    log(f"    parameters fitted in {time.perf_counter() - started:.0f}s "
        f"({params_metadata['skills_fitted']} skills, "
        f"{params_metadata['skills_kept_defaults']} kept defaults)")

    labels = [int(row.correct) for row in test]
    learners = [row.user_id for row in test]
    report: dict = {
        "index": fold.index,
        "counts": fold.counts() | {"test_answers": len(test)},
        "parameters": params_metadata,
        "models": {},
    }
    predictions: dict[str, list[float]] = {}

    for model in build_models(params, epochs=epochs, seed=seed):
        started = time.perf_counter()
        try:
            info = model.fit(train if _wants_validation(model) else fitting,
                             validation if _wants_validation(model) else None)
        except Unavailable as unavailable:
            report["models"][model.name] = {
                "status": "unavailable",
                "reason": unavailable.reason,
            }
            log(f"    {model.name:16s} unavailable — {unavailable.reason}")
            continue

        scores = model.predict(test)
        if len(scores) != len(labels):
            raise RuntimeError(
                f"{model.name} returned {len(scores)} predictions for {len(labels)} answers"
            )
        measured = metrics.by_first_k(labels, scores, learners)
        entry = {
            "status": "ok",
            "fit": info,
            "scores": measured,
            "seconds": round(time.perf_counter() - started, 1),
        }
        cold = getattr(model, "cold_rows", None)
        if cold is not None:
            entry["cold_rows"] = cold
        report["models"][model.name] = entry
        predictions[model.name] = scores
        log(f"    {model.name:16s} auc={_text(measured['all']['auc'])} "
            f"rmse={_text(measured['all']['rmse'])} "
            f"acc={_text(measured['all']['accuracy'])}  ({entry['seconds']:.0f}s)")

    return report, (predictions, labels, learners)


def _wants_validation(model) -> bool:
    """Only the neural models use a validation set (for early stopping)."""
    return model.name in ("DKT", "AKT")


def _text(value) -> str:
    return "—" if value is None else f"{value:.4f}"


def pool(fold_outputs: list[tuple[dict, list[int], list[str]]]) -> tuple[dict, list[int], list[str]]:
    """
    Concatenate the folds' test predictions. Every learner is in exactly one
    test fold, so the pooled set is the whole dataset, once.
    """
    names: list[str] = []
    for predictions, _, _ in fold_outputs:
        for name in predictions:
            if name not in names:
                names.append(name)
    pooled: dict[str, list[float]] = {name: [] for name in names}
    labels: list[int] = []
    learners: list[str] = []
    for predictions, fold_labels, fold_learners in fold_outputs:
        complete = [name for name in names if name in predictions]
        if len(complete) != len(names):
            # A model that failed on one fold cannot be pooled with the rest:
            # the paired test needs the same answers for every model.
            missing = sorted(set(names) - set(complete))
            raise RuntimeError(f"models missing from a fold, cannot pool: {missing}")
        labels.extend(fold_labels)
        learners.extend(fold_learners)
        for name in names:
            pooled[name].extend(predictions[name])
    return pooled, labels, learners


def analyse_pooled(
    pooled: dict,
    labels: list[int],
    learners: list[str],
    *,
    replicates: int,
    seed: int,
    cold_rows: dict[str, int] | None = None,
) -> dict:
    """
    Intervals per model, pairwise DeLong tests, Holm over the family.

    ``cold_rows`` carries how many answers each model could not predict from
    history and scored with the base rate. It matters most in the first-k
    columns: a sequence model has one such answer per learner, so with k = 3
    a third of that column is a constant and the early AUC reads lower than
    the model deserves. Recorded so the column is read correctly.
    """
    from experiments import stats

    out: dict = {
        "models": {},
        "cold_rows": dict(cold_rows or {}),
        "comparisons": [],
        "replicates": replicates,
        # In the metrics so the table can print it without writing a literal (D48).
        "confidence_percent": int(round(stats.CONFIDENCE * 100)),
    }
    for name, scores in pooled.items():
        measured = metrics.by_first_k(labels, scores, learners)
        interval = stats.bootstrap_auc(
            labels, scores, learners, replicates=replicates, seed=seed, by_learner=True,
        )
        out["models"][name] = {
            "scores": measured,
            "auc_interval": interval.payload(),
            "cold_rows": (cold_rows or {}).get(name, 0),
        }

    names = list(pooled)
    comparisons = []
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            comparisons.append(stats.delong_test(
                labels, pooled[left], pooled[right], name_a=left, name_b=right,
            ))
    out["comparisons"] = [item.payload() for item in stats.holm(comparisons)]
    return out


def sanity(pooled_models: dict) -> dict:
    """
    The DKT bound of D53. A warning in the metadata, never a failing test: the
    cleaning is what it checks, and a model is allowed to be surprising.
    """
    entry = pooled_models.get("DKT")
    auc = None if entry is None else entry["scores"]["all"]["auc"]
    low, high = DKT_SANITY_RANGE
    note = {
        "model": "DKT",
        "auc": auc,
        "expected_range": list(DKT_SANITY_RANGE),
        "literature_range": list(DKT_LITERATURE_RANGE),
        "reference": "Xiong et al., EDM 2016 — duplicates removed",
        "within_range": None if auc is None else bool(low <= auc <= high),
    }
    if auc is not None and not (low <= auc <= high):
        note["warning"] = (
            "DKT AUC is outside the range reported for de-duplicated "
            "ASSISTments 2009; re-check the cleaning of D50 before reading "
            "anything else in this table."
        )
    return note


def run(args, argv: list[str]) -> tuple[dict, Provenance]:
    dataset = assist09.load(
        args.data or None, original_only=args.original_only,
    )
    rows = list(dataset.rows)
    learners = list(dict.fromkeys(row.user_id for row in rows))

    if args.quick:
        learners = learners[:args.quick_learners]
        rows = splits.subset(rows, learners)
        print(f"  --quick: {len(learners)} learners, {len(rows)} answers")

    folds = splits.learner_folds(
        learners, folds=args.folds, validation_fraction=args.validation_fraction, seed=args.seed,
    )
    epochs = QUICK_EPOCHS if args.quick else args.epochs

    fold_reports = []
    fold_outputs = []
    for fold in folds:
        print(f"  fold {fold.index + 1}/{len(folds)}: {fold.counts()}")
        report, output = run_fold(fold, rows, epochs=epochs, seed=args.seed + fold.index)
        fold_reports.append(report)
        fold_outputs.append(output)

    pooled, labels, pooled_learners = pool(fold_outputs)
    print(f"  pooled {len(labels)} answers from {len(set(pooled_learners))} learners")
    cold = {}
    for report in fold_reports:
        for name, entry in report["models"].items():
            if "cold_rows" in entry:
                cold[name] = cold.get(name, 0) + entry["cold_rows"]
    analysis = analyse_pooled(
        pooled, labels, pooled_learners,
        replicates=args.replicates, seed=args.seed, cold_rows=cold,
    )
    warning = sanity(analysis["models"])
    if warning.get("warning"):
        print(f"  WARNING: {warning['warning']}", file=sys.stderr)

    cross = None
    if not args.skip_pybkt:
        from experiments.models import pybkt_check

        try:
            print("  pyBKT cross-check…")
            # pyBKT's EM is the slowest step in the run and this is a
            # consistency check between two fitters, not a result, so its
            # input is bounded and the bound goes into the metadata.
            fitting_learners = list(folds[0].fitting)[:args.pybkt_learners]
            cross = pybkt_check.cross_check(
                splits.subset(rows, fitting_learners),
                skills=args.pybkt_skills,
                seed=args.seed,
            )
            cross["learners_used"] = len(fitting_learners)
            cross["learners_available"] = len(folds[0].fitting)
            print(f"    {cross['skills_compared']} skill(s) compared, "
                  f"{cross['pybkt_outside_bounds_count']} outside chapter II's bounds")
        except Unavailable as unavailable:
            cross = {"status": "unavailable", "reason": unavailable.reason}
            print(f"    unavailable — {unavailable.reason}")

    provenance = Provenance.capture(
        sources=(Source.of("assistments2009", dataset.path),),
        seeds={"split": args.seed, "models": args.seed, "bootstrap": args.seed},
        argv=["python", "-m", "experiments.h2", *argv],
        packages=_packages(),
    )
    metrics_document = {
        "report": "h2",
        "spec": "D53",
        "quick": bool(args.quick),
        "thesis_result": not args.quick,
        "provenance": provenance.payload(),
        "dataset": dataset.metadata() | {
            "status": "ok",
            "name": "assistments2009",
            # The human label lives here rather than in the renderer, so the
            # year in the heading is data and not a literal (D48).
            "label": "ASSISTments 2009–2010 skill builder",
            "source": asdict(provenance.sources[0]),
            "learners_used": len(learners),
            "answers_used": len(rows),
        },
        "split": splits.metadata(
            folds, seed=args.seed, validation_fraction=args.validation_fraction,
        ),
        "epochs": epochs,
        "folds": fold_reports,
        "pooled": analysis,
        "sanity": warning,
        "pybkt_cross_check": cross,
        "unavailable": _unavailable(fold_reports),
    }
    return metrics_document, provenance


def _unavailable(fold_reports: list[dict]) -> list[dict]:
    """Models that could not run, with the reason, for the table (D48)."""
    out: dict[str, str] = {}
    for report in fold_reports:
        for name, entry in report["models"].items():
            if entry.get("status") == "unavailable":
                out[name] = entry["reason"]
    return [{"model": name, "reason": reason} for name, reason in sorted(out.items())]


# Import name → distribution name, where they differ.
_DISTRIBUTIONS = {
    "sklearn": "scikit-learn",
    "pykt": "pykt-toolkit",
    "pyBKT": "pyBKT",
}


def _packages() -> dict[str, str]:
    """
    The versions the run actually used (D48).

    Read from the installed distribution metadata rather than ``__version__``:
    pyBKT and pykt-toolkit do not define that attribute, and "unknown" in a
    provenance record is worse than useless.
    """
    from importlib.metadata import PackageNotFoundError, version

    found: dict[str, str] = {}
    for name in ("numpy", "pandas", "scipy", "sklearn", "torch", "pyBKT", "pykt"):
        try:
            __import__(name)
        except Exception:  # noqa: BLE001 - a missing package is simply absent
            continue
        try:
            found[name] = version(_DISTRIBUTIONS.get(name, name))
        except PackageNotFoundError:
            found[name] = "installed, version unknown"
    return found


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.h2",
        description="H2 on ASSISTments 2009 (D53). Takes paths; downloads nothing (D49).",
    )
    parser.add_argument("--data", default=None, help="Path to as.csv (default: the data root).")
    parser.add_argument("--quick", action="store_true",
                        help=f"{QUICK_LEARNERS} learners and {QUICK_EPOCHS} epochs, for CI.")
    parser.add_argument("--quick-learners", type=int, default=QUICK_LEARNERS)
    parser.add_argument("--original-only", action="store_true",
                        help="Keep only original=1 answers (D50, rule 4).")
    parser.add_argument("--folds", type=int, default=splits.DEFAULT_FOLDS)
    parser.add_argument("--validation-fraction", type=float,
                        default=splits.DEFAULT_VALIDATION_FRACTION)
    parser.add_argument("--epochs", type=int, default=FULL_EPOCHS,
                        help="Maximum epochs for DKT and AKT (early stopping on validation).")
    parser.add_argument("--replicates", type=int, default=1000,
                        help="Bootstrap replicates over learners.")
    parser.add_argument("--pybkt-skills", type=int, default=5)
    parser.add_argument(
        "--pybkt-learners", type=int, default=400,
        help=(
            "Learners given to the pyBKT cross-check. Bounded because its EM is "
            "the slowest step and the check compares fitters rather than "
            "producing a result; the bound is recorded in the metadata."
        ),
    )
    parser.add_argument("--skip-pybkt", action="store_true")
    parser.add_argument("--seed", type=int, default=splits.DEFAULT_SEED)
    parser.add_argument("--out", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    given = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(given)

    print("h2 (D53) — ASSISTments 2009")
    try:
        document, provenance = run(args, given)
    except DatasetMissing as missing:
        print(f"h2: {missing}", file=sys.stderr)
        return 2

    directory = (
        Path(args.out).expanduser() if args.out
        else results_dir("assist09-quick" if args.quick else "assist09")
    )
    written = tables.write(
        directory, document, provenance.env_txt(), renderer=tables.render_h2_report,
    )
    print(f"\nwritten to {directory}")
    for path in written.values():
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
