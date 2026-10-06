"""
experiments/h2_bounds.py — how much H2 depends on chapter II's caps (D55).

On ASSISTments 2009 the fitted guess and slip pile up against chapter II's
ceilings: P(G) on G_MAX = 0.30 and P(S) on S_MAX = 0.10 for most skills. The
caps are a decision of chapter II — γ in ``neuro_model.irt.gamma`` needs
G0 < G_MAX, and the 2.5 assertion needs P(G) + P(S) < 1 — and **they do not
change**: the main result stays the one under (0.30, 0.10). What this script
adds is how much the conclusion moves when the caps are relaxed, so that the
reader can tell a finding about the model from a finding about the bound.

    python -m experiments.h2_bounds --quick
    python -m experiments.h2_bounds

The bounds are an experiment parameter here and nowhere else: the platform's
constants (``settings.THESIS_MODEL``, ``neuro_model``) are not touched, and
the models receive a copy of ``classical.CONSTANTS`` with G_MAX and S_MAX
replaced.

Per setting:

1. **A grid relative to the bound.** The P(G) and P(S) values are those of
   ``calibrate.DEFAULT_GRID`` as fractions of chapter II's bounds, rescaled to
   the setting's, so the top value sits at the same share of the ceiling
   (about 97 %). Under (0.30, 0.10) this *is* ``DEFAULT_GRID`` — the main
   setting reproduces H2's BKT and BKT+IRT exactly.
2. **The grid is checked before anything is fitted.** On the five busiest
   skills of the first fold's fitting set, the grid's best log-likelihood
   must be within ``LBFGS_TOLERANCE`` (relative) of a bounded L-BFGS-B
   optimum of the same likelihood. If not, the run stops and writes nothing:
   a grid that cannot reach the optimum under a wider bound would make the
   wider setting look worse than it is.
3. **Per fold**, the platform's fitter (``calibrate.grid_search``) on train +
   validation, then BKT and BKT+IRT (λ=0) predict the test fold — the same
   split and seeds as H2.
4. **Pooled**: AUC with a learner bootstrap, RMSE, accuracy, the held-out
   log-likelihood, BKT+IRT − BKT (DeLong with Holm over the settings, and a
   learner bootstrap of the difference), the share of fits on the top of the
   grid, and the training log-likelihood.

The grid search is the slow part (about 20 minutes per fold on the full
data), so the (setting, fold) fits run in parallel processes. Each one is the
same pure function of its rows, so the result does not depend on how many
workers ran it.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from neuro_model import calibrate
from neuro_model import student as engine

from experiments import metrics, splits, stats, tables
from experiments.datasets import DatasetMissing, assist09
from experiments.h2 import QUICK_LEARNERS, _packages, aggregate_grid_checks
from experiments.models.classical import CONSTANTS, BKTFamily, fit_skill_params
from experiments.models.pybkt_check import busiest_skills, sequences_by_skill
from experiments.provenance import GitState, Provenance, Source, results_dir

# D55: the two models whose difference H2 is about.
BKT = "BKT"
BKT_IRT = "BKT+IRT (λ=0)"
MODELS: tuple[str, ...] = (BKT, BKT_IRT)

DEFAULT_REPLICATES = 200
CHECK_SKILLS = 5
LBFGS_TOLERANCE = 0.01
# Rescaled grid values are rounded to this many decimals, which is also what
# makes the main setting's grid come out as DEFAULT_GRID exactly.
GRID_DIGITS = 4
# L-BFGS-B works on closed boxes; γ needs the open ones.
EDGE = 1e-6
# As in neuro_model.calibrate: one impossible prediction cannot make the
# held-out log-likelihood -inf.
_FLOOR = 1e-12


@dataclass(frozen=True)
class Setting:
    """One pair of caps. ``main`` is chapter II's and the reported result."""
    name: str
    g_max: float
    s_max: float
    main: bool = False


SETTINGS: tuple[Setting, ...] = (
    Setting("asosiy", 0.30, 0.10, main=True),
    Setting("kengroq", 0.40, 0.20),
    Setting("eng keng", 0.49, 0.30),
)


class BoundsCheckFailed(RuntimeError):
    """The grid does not reach the bounded optimum; the run stops (D55)."""


def validate(settings: tuple[Setting, ...] = SETTINGS) -> None:
    """
    Every setting keeps the conditions chapter II's model needs: G_MAX < 0.5
    (a guess is never better than chance on a two-option reading) and
    G_MAX + S_MAX < 1 (the 2.5 assertion). Exactly one is the main setting,
    and it is chapter II's.
    """
    mains = [setting for setting in settings if setting.main]
    if len(mains) != 1:
        raise ValueError("exactly one setting must be the main one")
    if (mains[0].g_max, mains[0].s_max) != (CONSTANTS.g_max, CONSTANTS.s_max):
        raise ValueError("the main setting must be chapter II's bounds")
    for setting in settings:
        if not 0.0 < setting.g_max < 0.5:
            raise ValueError(f"{setting.name}: G_MAX must be in (0, 0.5)")
        if not 0.0 < setting.s_max or setting.g_max + setting.s_max >= 1.0:
            raise ValueError(f"{setting.name}: S_MAX must be positive and G_MAX + S_MAX < 1")


def constants_for(setting: Setting) -> engine.Constants:
    """Chapter II's constants with this setting's caps; nothing else differs."""
    return replace(CONSTANTS, g_max=setting.g_max, s_max=setting.s_max)


def scaled_grid(setting: Setting) -> calibrate.Grid:
    """``DEFAULT_GRID`` with P(G) and P(S) at the same share of this setting's caps."""
    base = calibrate.DEFAULT_GRID

    def scale(values: tuple[float, ...], bound: float, reference: float) -> tuple[float, ...]:
        return tuple(round(bound * value / reference, GRID_DIGITS) for value in values)

    return calibrate.Grid(
        p0=base.p0,
        pt=base.pt,
        g0=scale(base.g0, setting.g_max, CONSTANTS.g_max),
        s0=scale(base.s0, setting.s_max, CONSTANTS.s_max),
    )


def grid_payload(setting: Setting, grid: calibrate.Grid) -> dict:
    return {
        "p0": list(grid.p0),
        "pt": list(grid.pt),
        "g0": list(grid.g0),
        "s0": list(grid.s0),
        "ceiling_share_g0": round(max(grid.g0) / setting.g_max, 4),
        "ceiling_share_s0": round(max(grid.s0) / setting.s_max, 4),
        "candidates": len(grid.candidates(g_max=setting.g_max, s_max=setting.s_max)),
    }


# ---------------------------------------------------------------------------
# The L-BFGS-B check
# ---------------------------------------------------------------------------

def continuous_optimum(answers, setting: Setting, *, start: calibrate.Candidate) -> dict:
    """
    The bounded maximum of ``calibrate.log_likelihood`` by L-BFGS-B, from the
    grid's best point and two others; the best of the three is kept.
    """
    try:
        from scipy.optimize import minimize
    except ModuleNotFoundError as missing:  # pragma: no cover - environment guard
        raise BoundsCheckFailed(f"scipy is needed for the L-BFGS-B check: {missing}") from missing

    bounds = [
        (EDGE, 1.0 - EDGE),
        (0.0, 1.0),
        (EDGE, setting.g_max - EDGE),
        (EDGE, setting.s_max - EDGE),
    ]

    def negative(x) -> float:
        return -calibrate.log_likelihood(answers, p0=x[0], pt=x[1], g0=x[2], s0=x[3])

    starts = (
        (start.p0, start.pt, start.g0, start.s0),
        (0.5, 0.2, setting.g_max / 2.0, setting.s_max / 2.0),
        (0.3, 0.1, 0.9 * setting.g_max, 0.9 * setting.s_max),
    )
    best = None
    for x0 in starts:
        result = minimize(negative, x0, method="L-BFGS-B", bounds=bounds)
        if best is None or result.fun < best.fun:
            best = result
    return {
        "log_likelihood": -float(best.fun),
        "p0": float(best.x[0]),
        "pt": float(best.x[1]),
        "g0": float(best.x[2]),
        "s0": float(best.x[3]),
    }


def lbfgs_check(
    rows,
    setting: Setting,
    grid: calibrate.Grid,
    *,
    skills: int = CHECK_SKILLS,
    tolerance: float = LBFGS_TOLERANCE,
) -> dict:
    """The grid's best against the bounded optimum on the busiest ``skills``."""
    sequences = sequences_by_skill(rows)
    entries = []
    for skill in busiest_skills(rows, skills):
        answers = sequences[skill]
        best = calibrate.grid_search(answers, g_max=setting.g_max, s_max=setting.s_max, grid=grid)
        if best is None:
            continue
        optimum = continuous_optimum(answers, setting, start=best)
        gap = (optimum["log_likelihood"] - best.log_likelihood) / abs(optimum["log_likelihood"])
        # Where the grid's best sits on an edge of its own values: the first
        # thing to look at when the gap is large. An edge of P(G) or P(S) is
        # the cap; an edge of P0 or PT is the grid.
        edges = [
            f"{name}={'min' if value == min(values) else 'max'}"
            for name, value, values in (
                ("p0", best.p0, grid.p0), ("pt", best.pt, grid.pt),
                ("g0", best.g0, grid.g0), ("s0", best.s0, grid.s0),
            )
            if value in (min(values), max(values))
        ]
        entries.append({
            "skill": skill,
            "answers": calibrate.count_observations(answers),
            "grid": {
                "p0": best.p0, "pt": best.pt, "g0": best.g0, "s0": best.s0,
                "log_likelihood": round(best.log_likelihood, 4),
            },
            "lbfgs": {key: round(value, 6) for key, value in optimum.items()},
            "relative_gap": round(gap, 6),
            "within_tolerance": gap < tolerance,
            "grid_edges": edges,
        })
    return {
        "skills": [entry["skill"] for entry in entries],
        "tolerance": tolerance,
        "max_relative_gap": max((entry["relative_gap"] for entry in entries), default=None),
        "passed": bool(entries) and all(entry["within_tolerance"] for entry in entries),
        "entries": entries,
    }


def _describe(entry: dict) -> str:
    """One failed skill of the check, in a line the log can be read by."""
    edges = ", ".join(entry["grid_edges"]) or "no edge"
    optimum = ", ".join(f"{key}={entry['lbfgs'][key]}" for key in ("p0", "pt", "g0", "s0"))
    return (
        f"skill {entry['skill']} gap {entry['relative_gap']}, "
        f"grid best on {edges}, L-BFGS-B at {optimum}"
    )


# ---------------------------------------------------------------------------
# Fitting and predicting
# ---------------------------------------------------------------------------

def _fit_task(task: tuple[int, Setting, int, list]) -> tuple[int, int, dict, dict, float]:
    """One (setting, fold) fit; a top-level function so a process pool can run it."""
    setting_index, setting, fold_index, fitting = task
    started = time.perf_counter()
    params, meta = fit_skill_params(
        fitting, grid=scaled_grid(setting), constants=constants_for(setting),
    )
    return setting_index, fold_index, params, meta, time.perf_counter() - started


def fit_all(tasks: list, *, workers: int, log=print) -> dict[tuple[int, int], tuple[dict, dict, float]]:
    """Run the fits, in a process pool when ``workers > 1``."""
    out: dict[tuple[int, int], tuple[dict, dict, float]] = {}
    names = {task[0]: task[1].name for task in tasks}

    def record(result) -> None:
        setting_index, fold_index, params, meta, seconds = result
        out[(setting_index, fold_index)] = (params, meta, seconds)
        log(f"    fitted {names[setting_index]} / fold {fold_index + 1} "
            f"in {seconds:.0f}s ({meta['skills_fitted']} skills)")

    if workers <= 1:
        for task in tasks:
            record(_fit_task(task))
        return out

    import multiprocessing
    from concurrent.futures import as_completed

    # Logged as each fit finishes, so a long run shows progress; the results
    # are keyed by (setting, fold), so the order they arrive in is irrelevant.
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("fork")) as pool:
        for future in as_completed([pool.submit(_fit_task, task) for task in tasks]):
            record(future.result())
    return out


def predict_fold(setting: Setting, params: dict, fitting, test) -> dict[str, list[float]]:
    """BKT and BKT+IRT (λ=0) on the test fold, with the shared parameters (D53)."""
    constants = constants_for(setting)
    out = {}
    for name, use_irt in ((BKT, False), (BKT_IRT, True)):
        model = BKTFamily(name, use_irt=use_irt, use_prereq_init=False, params=params, constants=constants)
        model.fit(fitting)
        out[name] = model.predict(test)
    return out


def held_out_log_likelihood(labels: list[int], scores: list[float]) -> float:
    """Σ log p̂ over correct answers + Σ log(1 − p̂) over wrong ones, on the test folds."""
    total = 0.0
    for label, score in zip(labels, scores):
        probability = score if label else 1.0 - score
        total += math.log(max(probability, _FLOOR))
    return total


def analyse(pooled: dict[str, list[float]], labels: list[int], learners: list[str], *,
            replicates: int, seed: int) -> dict:
    out: dict = {"models": {}}
    for name in MODELS:
        scores = pooled[name]
        interval = stats.bootstrap_auc(
            labels, scores, learners, replicates=replicates, seed=seed, by_learner=True,
        )
        out["models"][name] = {
            "scores": metrics.score(labels, scores).payload(),
            "auc_interval": interval.payload(),
            "log_likelihood": round(held_out_log_likelihood(labels, scores), 4),
        }
    out["delong"] = stats.delong_test(
        labels, pooled[BKT_IRT], pooled[BKT], name_a=BKT_IRT, name_b=BKT,
    )
    out["bootstrap_difference"] = stats.bootstrap_auc_difference(
        labels, pooled[BKT_IRT], pooled[BKT], learners, replicates=replicates, seed=seed,
    ).payload()
    return out


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def run(args, argv: list[str], *, dataset=None, settings: tuple[Setting, ...] = SETTINGS,
        log=print) -> tuple[dict, Provenance]:
    validate(settings)
    # D54: taken before anything is loaded, so a tree edited mid-run shows.
    git_start = GitState.capture()
    if dataset is None:
        dataset = assist09.load(args.data or None, original_only=args.original_only)
    rows = list(dataset.rows)
    learners = list(dict.fromkeys(row.user_id for row in rows))
    if args.quick:
        learners = learners[:args.quick_learners]
        rows = splits.subset(rows, learners)
        log(f"  --quick: {len(learners)} learners, {len(rows)} answers")

    folds = splits.learner_folds(
        learners, folds=args.folds, validation_fraction=args.validation_fraction, seed=args.seed,
    )
    fitting_rows = [splits.subset(rows, fold.fitting) for fold in folds]
    test_rows = [splits.subset(rows, fold.test) for fold in folds]
    grids = [scaled_grid(setting) for setting in settings]

    # 1. The grid check, before any fold is fitted (D55).
    checks = []
    for setting, grid in zip(settings, grids):
        log(f"  L-BFGS-B check, {setting.name} (G_MAX={setting.g_max}, S_MAX={setting.s_max})")
        check = lbfgs_check(fitting_rows[0], setting, grid, skills=args.check_skills,
                            tolerance=args.tolerance)
        log(f"    max relative gap {check['max_relative_gap']} (tolerance {check['tolerance']})")
        checks.append(check)
    failed = [setting.name for setting, check in zip(settings, checks) if not check["passed"]]
    if failed:
        raise BoundsCheckFailed(
            f"the grid is not within {args.tolerance:.0%} of the bounded L-BFGS-B optimum "
            f"for: {', '.join(failed)}. Nothing was written. "
            + "; ".join(
                f"{setting.name}: {_describe(entry)}"
                for setting, check in zip(settings, checks)
                for entry in check["entries"] if not entry["within_tolerance"]
            )
        )

    # 2. Every (setting, fold) fit.
    tasks = [
        (index, setting, fold.index, fitting_rows[fold.index])
        for index, setting in enumerate(settings)
        for fold in folds
    ]
    workers = max(1, min(args.workers, len(tasks)))
    log(f"  fitting {len(tasks)} (setting, fold) pairs on {workers} worker(s)")
    fits = fit_all(tasks, workers=workers, log=log)

    # 3. Predictions and the pooled analysis, per setting.
    results = []
    for index, (setting, grid, check) in enumerate(zip(settings, grids, checks)):
        pooled: dict[str, list[float]] = {name: [] for name in MODELS}
        labels: list[int] = []
        pooled_learners: list[str] = []
        fold_reports = []
        fit_log_likelihood = 0.0
        for fold in folds:
            params, meta, seconds = fits[(index, fold.index)]
            test = test_rows[fold.index]
            predictions = predict_fold(setting, params, fitting_rows[fold.index], test)
            fold_labels = [int(row.correct) for row in test]
            labels.extend(fold_labels)
            pooled_learners.extend(row.user_id for row in test)
            for name in MODELS:
                pooled[name].extend(predictions[name])
            fit_log_likelihood += meta["fit_log_likelihood"]
            fold_reports.append({
                "index": fold.index,
                "counts": fold.counts() | {"test_answers": len(test)},
                "seconds": round(seconds, 1),
                "parameters": meta,
                "auc": {name: metrics.auc(fold_labels, predictions[name]) for name in MODELS},
            })
        analysis = analyse(pooled, labels, pooled_learners,
                           replicates=args.replicates, seed=args.seed)
        log(f"  {setting.name}: " + ", ".join(
            f"{name} auc={analysis['models'][name]['scores']['auc']:.4f}" for name in MODELS
        ))
        results.append({
            "name": setting.name,
            "g_max": setting.g_max,
            "s_max": setting.s_max,
            "main": setting.main,
            "grid": grid_payload(setting, grid),
            "lbfgs_check": check,
            "grid_check": aggregate_grid_checks(fold_reports),
            "fit_log_likelihood": round(fit_log_likelihood, 4),
            "models": analysis["models"],
            "difference": {
                "a": BKT_IRT,
                "b": BKT,
                "delong": analysis["delong"],
                "bootstrap": analysis["bootstrap_difference"],
            },
            "folds": [
                {key: value for key, value in report.items() if key != "parameters"}
                | {"skills_fitted": report["parameters"]["skills_fitted"],
                   "skills_kept_defaults": report["parameters"]["skills_kept_defaults"]}
                for report in fold_reports
            ],
        })

    # Holm over the family of the settings' BKT+IRT − BKT tests.
    corrected = stats.holm([result["difference"]["delong"] for result in results])
    for result, comparison in zip(results, corrected):
        result["difference"]["delong"] = comparison.payload()

    provenance = Provenance.capture(
        sources=(Source.of("assistments2009", dataset.path),),
        seeds={"split": args.seed, "bootstrap": args.seed},
        argv=["python", "-m", "experiments.h2_bounds", *argv],
        packages=_packages(),
        git_start=git_start,
    )
    document = {
        "report": "h2_bounds",
        "spec": "D55",
        "quick": bool(args.quick),
        "thesis_result": not args.quick,
        "provenance": provenance.payload(),
        "dataset": dataset.metadata() | {
            "status": "ok",
            "name": "assistments2009",
            "label": "ASSISTments 2009–2010 skill builder",
            "source": asdict(provenance.sources[0]),
            "learners_used": len(learners),
            "answers_used": len(rows),
        },
        "split": splits.metadata(folds, seed=args.seed, validation_fraction=args.validation_fraction),
        "models": list(MODELS),
        "chapter_two_bounds": {"g_max": CONSTANTS.g_max, "s_max": CONSTANTS.s_max},
        "replicates": args.replicates,
        "confidence_percent": int(round(stats.CONFIDENCE * 100)),
        "lbfgs": {
            "skills": args.check_skills,
            "tolerance": args.tolerance,
            "fitting_set": "fold 1, train + validation",
            "starts": "grid optimum, centre of the box, near the caps",
        },
        "workers": workers,
        "settings": results,
    }
    return document, provenance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.h2_bounds",
        description="H2's sensitivity to G_MAX and S_MAX (D55). Downloads nothing (D49).",
    )
    parser.add_argument("--data", default=None, help="Path to as.csv (default: the data root).")
    parser.add_argument("--quick", action="store_true", help=f"{QUICK_LEARNERS} learners, for CI.")
    parser.add_argument("--quick-learners", type=int, default=QUICK_LEARNERS)
    parser.add_argument("--original-only", action="store_true")
    parser.add_argument("--folds", type=int, default=splits.DEFAULT_FOLDS)
    parser.add_argument("--validation-fraction", type=float, default=splits.DEFAULT_VALIDATION_FRACTION)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--check-skills", type=int, default=CHECK_SKILLS)
    parser.add_argument("--tolerance", type=float, default=LBFGS_TOLERANCE)
    parser.add_argument(
        "--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2)),
        help="Processes for the (setting, fold) grid searches; the result does not depend on it.",
    )
    parser.add_argument("--seed", type=int, default=splits.DEFAULT_SEED)
    parser.add_argument("--out", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    given = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(given)
    print("h2_bounds (D55) — ASSISTments 2009")
    try:
        document, provenance = run(args, given)
    except DatasetMissing as missing:
        print(f"h2_bounds: {missing}", file=sys.stderr)
        return 2
    except BoundsCheckFailed as failed:
        print(f"h2_bounds: {failed}", file=sys.stderr)
        return 3

    directory = (
        Path(args.out).expanduser() if args.out
        else results_dir("assist09-bounds-quick" if args.quick else "assist09-bounds")
    )
    written = tables.write(
        directory, document, provenance.env_txt(), renderer=tables.render_h2_bounds_report,
    )
    print(f"\nwritten to {directory}")
    for path in written.values():
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
