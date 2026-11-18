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

D58 (under D57). The run goes through H2's own path — ``h2.prepare``,
``h2.fold_sets``, ``h2.fit_predict``, ``h2.dkt_model`` — so the data, the
cleaning, the split, the seeds and the order-level evaluation are H2's, not a
copy of them. Three additions:

- **Reproduction gates.** The main setting's fold-1 BKT and BKT+IRT AUCs, and
  then the pooled ones, rounded to six places, must equal the H2 result named
  by ``--reference``; otherwise the run stops with exit status 5 and writes
  nothing. The fold-1 gate runs as soon as that fit arrives (it is fitted first).
- **DKT**, retrained as H2 trains it, for BKT+IRT − DKT (D56) per setting. If
  its pooled AUC is more than ``DKT_TOLERANCE`` from H2's, that contrast is
  "hisoblanmadi — DKT qayta tiklanmadi", not a number.
- **Checkpoints** in experiments/.runs/checkpoints, keyed by commit, data
  sha256, seeds, mode, split, settings and epochs; a run with another key
  starts afresh. Nothing partial is written under results/ (D48).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from neuro_model import calibrate
from neuro_model import student as engine

from experiments import h2, metrics, splits, stats, tables
from experiments.datasets import DatasetMissing
from experiments.h2 import QUICK_LEARNERS, _packages, aggregate_grid_checks
from experiments.models import Unavailable
from experiments.models.classical import CONSTANTS, BKTFamily, fit_skill_params
from experiments.models.pybkt_check import busiest_skills, sequences_by_skill
from experiments.provenance import GitState, Provenance, Source, results_dir

# D55: the two models whose difference H2 is about.
BKT = "BKT"
BKT_IRT = "BKT+IRT (λ=0)"
MODELS: tuple[str, ...] = (BKT, BKT_IRT)

DKT = "DKT"
ELO = "Elo/Rasch"

DEFAULT_REPLICATES = 200
# D58: the retrained DKT must land within this of H2's pooled AUC for its
# contrast to be computed. A methodological choice, not from a source.
DKT_TOLERANCE = 5e-4
# D56: "comparable with DKT" is the lower end of BKT+IRT − DKT's interval at or
# above this. Recorded next to the contrast; nothing here decides with it.
D56_MARGIN = -0.01
CHECKPOINTS = "experiments/.runs/checkpoints"
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


class ReproductionFailed(RuntimeError):
    """The main setting does not reproduce H2, or the reference is not H2's run (D58)."""


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


def fit_all(tasks: list, *, workers: int, log=print, on_fit=None) -> dict[tuple[int, int], tuple[dict, dict, float]]:
    """
    Run the fits, in a process pool when ``workers > 1``, in the order given.

    ``on_fit(setting_index, fold_index, params, meta, seconds)`` is called in
    this process as each fit arrives — the checkpoint and the reproduction
    gate hang on it. If it raises, the pool is terminated (not waited for)
    and the error propagates.
    """
    out: dict[tuple[int, int], tuple[dict, dict, float]] = {}
    names = {task[0]: task[1].name for task in tasks}

    def record(result) -> None:
        setting_index, fold_index, params, meta, seconds = result
        out[(setting_index, fold_index)] = (params, meta, seconds)
        log(f"    fitted {names[setting_index]} / fold {fold_index + 1} "
            f"in {seconds:.0f}s ({meta['skills_fitted']} skills)")
        if on_fit is not None:
            on_fit(setting_index, fold_index, params, meta, seconds)

    if workers <= 1 or len(tasks) <= 1:
        for task in tasks:
            record(_fit_task(task))
        return out

    import multiprocessing

    # Logged as each fit finishes, so a long run shows progress; the results
    # are keyed by (setting, fold), so the order they arrive in is irrelevant.
    # Pool rather than ProcessPoolExecutor: leaving the block on an error
    # terminates the workers instead of waiting out fits that no longer matter.
    with multiprocessing.get_context("fork").Pool(processes=workers) as pool:
        for result in pool.imap_unordered(_fit_task, tasks):
            record(result)
    return out


def predict_fold(setting: Setting, params: dict, sets: dict[str, list]) -> dict[str, list[float]]:
    """
    BKT and BKT+IRT (λ=0) on the test fold, with the shared parameters (D53),
    through H2's own fit-and-predict (``h2.fit_predict``, D57).
    """
    constants = constants_for(setting)
    out = {}
    for name, use_irt in ((BKT, False), (BKT_IRT, True)):
        model = BKTFamily(name, use_irt=use_irt, use_prereq_init=False, params=params, constants=constants)
        _, out[name] = h2.fit_predict(model, sets)
    return out


# ---------------------------------------------------------------------------
# The reference H2 run, and the gates on it (D58)
# ---------------------------------------------------------------------------

def load_reference(path: str | Path, *, dataset, args) -> dict:
    """
    The H2 numbers the main setting must reproduce, from that run's metrics.
    The run must be H2 under D57 on the same file, mode, seed and split.
    """
    metrics_path = Path(path) / "metrics.json"
    if not metrics_path.exists():
        raise ReproductionFailed(f"reference {metrics_path} does not exist")
    document = json.loads(metrics_path.read_text(encoding="utf-8"))
    split = document.get("split") or {}
    pooled = (document.get("pooled") or {}).get("models") or {}
    problems = []
    if document.get("report") != "h2":
        problems.append(f"report is {document.get('report')!r}, not 'h2'")
    if (document.get("pooled") or {}).get("evaluation_protocol") != h2.EVALUATION_PROTOCOL:
        problems.append(f"not evaluated under {h2.EVALUATION_PROTOCOL}")
    if bool(document.get("quick")) != bool(args.quick):
        problems.append(f"quick is {document.get('quick')}, this run's is {bool(args.quick)}")
    if (document.get("dataset") or {}).get("sha256") != dataset.sha256:
        problems.append("a different data file")
    for key, value in (("seed", args.seed), ("folds", args.folds),
                       ("validation_fraction", args.validation_fraction)):
        if split.get(key) != value:
            problems.append(f"split {key} {split.get(key)!r}, this run's {value!r}")
    provenance = document.get("provenance") or {}
    if not provenance.get("code_commit"):
        problems.append("no commit in its provenance")
    if provenance.get("tree_warnings"):
        problems.append("its tree was not clean: " + "; ".join(provenance["tree_warnings"]))
    main = next(setting for setting in SETTINGS if setting.main)
    candidates = len(calibrate.DEFAULT_GRID.candidates(g_max=main.g_max, s_max=main.s_max))
    recorded = {fold.get("parameters", {}).get("grid_candidates") for fold in document.get("folds", [])}
    if recorded != {candidates}:
        problems.append(f"fitted on another grid ({sorted(map(str, recorded))} candidates, now {candidates})")
    if problems:
        raise ReproductionFailed(f"reference {path}: " + "; ".join(problems))
    first = document["folds"][0]["models"]
    return {
        "path": str(path),
        "commit": (document.get("provenance") or {}).get("code_commit"),
        "learners": split.get("learners"),
        "fold_1": {name: first[name]["scores"]["all"]["auc"] for name in MODELS},
        "pooled": {name: pooled[name]["scores"]["all"]["auc"] for name in (*MODELS, DKT, ELO)
                   if name in pooled},
    }


def reproduction_gate(where: str, got: dict[str, float], expected: dict[str, float]) -> dict:
    """Each model's AUC, rounded to six places as H2 records it, must equal H2's."""
    models = {}
    for name in MODELS:
        value = None if got.get(name) is None else round(got[name], 6)
        models[name] = {"bounds": value, "h2": expected.get(name), "equal": value == expected.get(name)}
    return {"where": where, "models": models, "passed": all(entry["equal"] for entry in models.values())}


def _gate_failure(gate: dict) -> str:
    return f"{gate['where']}: " + "; ".join(
        f"{name} {entry['bounds']} is not H2's {entry['h2']}"
        for name, entry in gate["models"].items() if not entry["equal"]
    )


def dkt_gate(auc: float | None, reference: float | None, *, tolerance: float = DKT_TOLERANCE) -> dict:
    """The retrained DKT against H2's pooled DKT AUC (D58)."""
    if auc is None or reference is None:
        return {"auc": auc, "h2": reference, "difference": None, "tolerance": tolerance, "passed": False}
    difference = round(auc - reference, 6)
    return {"auc": round(auc, 6), "h2": reference, "difference": difference,
            "tolerance": tolerance, "passed": abs(auc - reference) <= tolerance}


# ---------------------------------------------------------------------------
# Checkpoints (experiments/.runs, never results/)
# ---------------------------------------------------------------------------

class Checkpoint:
    """
    Finished (setting, fold) fits and DKT folds, so an interrupted run resumes.

    Kept under a directory named by the digest of the key — commit, data
    sha256, seeds, mode and split, settings, epochs, protocol — and the key is
    stored and compared on every read: anything that changed starts afresh.
    Disabled when the tree is dirty, because the commit then does not name
    the code. Nothing here is a result (D48); results/ is written only at the end.
    """

    def __init__(self, root: str | Path, key: dict, *, enabled: bool, log=print) -> None:
        self.key = key
        self.enabled = enabled
        self.digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:16]
        self.directory = Path(root) / f"h2-bounds-{self.digest}"
        self.resumed = 0
        self.log = log

    def _matches(self) -> bool:
        stored = self.directory / "key.json"
        if not stored.exists():
            return False
        return json.loads(stored.read_text(encoding="utf-8")) == self.key

    def _read(self, name: str):
        if not self.enabled or not self._matches():
            return None
        path = self.directory / name
        if not path.exists():
            return None
        self.resumed += 1
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, name: str, payload) -> None:
        if not self.enabled:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        if not (self.directory / "key.json").exists():
            (self.directory / "key.json").write_text(json.dumps(self.key, sort_keys=True), encoding="utf-8")
        elif not self._matches():
            raise ReproductionFailed(f"checkpoint {self.directory} holds another run's key")
        temporary = self.directory / (name + ".tmp")
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        temporary.replace(self.directory / name)

    def load_fit(self, setting_index: int, fold_index: int):
        payload = self._read(f"fit-{setting_index}-{fold_index}.json")
        if payload is None:
            return None
        params = {skill: engine.TopicParams(**values) for skill, values in payload["params"].items()}
        return params, payload["meta"], payload["seconds"]

    def save_fit(self, setting_index: int, fold_index: int, params: dict, meta: dict, seconds: float) -> None:
        self._write(f"fit-{setting_index}-{fold_index}.json", {
            "params": {skill: asdict(value) for skill, value in params.items()},
            "meta": meta, "seconds": seconds,
        })

    def load_dkt(self, fold_index: int):
        return self._read(f"dkt-{fold_index}.json")

    def save_dkt(self, fold_index: int, payload: dict) -> None:
        self._write(f"dkt-{fold_index}.json", payload)

    def payload(self) -> dict:
        return {"enabled": self.enabled, "key_digest": self.digest, "resumed_items": self.resumed}


def checkpoint_key(git_start: GitState, dataset, args, settings: tuple[Setting, ...]) -> dict:
    return {
        "commit": git_start.commit,
        "data_sha256": dataset.sha256,
        "seeds": {"split": args.seed, "models": args.seed, "bootstrap": args.seed},
        "quick": bool(args.quick),
        "quick_learners": args.quick_learners if args.quick else None,
        "original_only": bool(args.original_only),
        "folds": args.folds,
        "validation_fraction": args.validation_fraction,
        "epochs": h2.epochs_for(args),
        "settings": [[setting.name, setting.g_max, setting.s_max] for setting in settings],
        "protocol": h2.EVALUATION_PROTOCOL,
    }


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
        log=print, reference: dict | None = None) -> tuple[dict, Provenance]:
    validate(settings)
    # D54: taken before anything is loaded, so a tree edited mid-run shows.
    git_start = GitState.capture()
    # H2's own data, cleaning, quick cap and split (D58: one evaluation path).
    dataset, rows, learners, folds = h2.prepare(args, dataset=dataset, log=log)
    if reference is None:
        if not args.reference:
            raise ReproductionFailed("--reference (the H2 result to reproduce) is required")
        reference = load_reference(args.reference, dataset=dataset, args=args)
    if reference.get("learners") not in (None, len(learners)):
        raise ReproductionFailed(
            f"reference has {reference['learners']} learners, this run {len(learners)}")
    sets = [h2.fold_sets(fold, rows) for fold in folds]
    fitting_rows = [fold_set["fitting"] for fold_set in sets]
    test_rows = [fold_set["test"] for fold_set in sets]
    grids = [scaled_grid(setting) for setting in settings]
    main_index = next(index for index, setting in enumerate(settings) if setting.main)

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

    checkpoint = Checkpoint(
        args.checkpoint_dir, checkpoint_key(git_start, dataset, args, settings),
        enabled=(git_start.dirty is False and git_start.commit is not None
                 and not args.no_checkpoint),
        log=log,
    )
    log(f"  checkpoint: {checkpoint.directory if checkpoint.enabled else 'off (tree not clean or --no-checkpoint)'}")

    # 2. Every (setting, fold) fit, the main setting's first fold first: its
    # gate is the first thing the run can be wrong about (D58).
    gates: dict = {}
    fits: dict[tuple[int, int], tuple[dict, dict, float]] = {}

    def on_fit(setting_index, fold_index, params, meta, seconds, *, stored=False) -> None:
        fits[(setting_index, fold_index)] = (params, meta, seconds)
        if not stored:
            checkpoint.save_fit(setting_index, fold_index, params, meta, seconds)
        if setting_index == main_index and fold_index == 0:
            predictions = predict_fold(settings[main_index], params, sets[0])
            labels_first = [int(row.correct) for row in test_rows[0]]
            gate = reproduction_gate(
                "fold 1", {name: metrics.auc(labels_first, predictions[name]) for name in MODELS},
                reference["fold_1"],
            )
            gates["fold_1"] = gate
            log(f"  reproduction gate, {settings[main_index].name} fold 1: "
                + ", ".join(f"{name} {entry['bounds']} vs H2 {entry['h2']}"
                            for name, entry in gate["models"].items())
                + (" — passed" if gate["passed"] else " — FAILED"))
            if not gate["passed"]:
                raise ReproductionFailed(_gate_failure(gate))

    order = sorted(
        ((index, setting, fold.index) for index, setting in enumerate(settings) for fold in folds),
        key=lambda item: (item[0] != main_index or item[2] != 0, item[0], item[2]),
    )
    tasks = []
    for index, setting, fold_index in order:
        stored = checkpoint.load_fit(index, fold_index)
        if stored is not None:
            log(f"    resumed {setting.name} / fold {fold_index + 1} from the checkpoint")
            on_fit(index, fold_index, *stored, stored=True)
        else:
            tasks.append((index, setting, fold_index, fitting_rows[fold_index]))
    workers = max(1, min(args.workers, len(tasks) or 1))
    log(f"  fitting {len(tasks)} (setting, fold) pairs on {workers} worker(s)")
    fit_all(tasks, workers=workers, log=log, on_fit=on_fit)

    # 3. DKT, retrained as H2 trains it (D58); one per fold, not per setting.
    dkt_scores: list[float] = []
    dkt_folds = []
    dkt_status = "ok"
    for fold in folds:
        stored = checkpoint.load_dkt(fold.index)
        if stored is None:
            started = time.perf_counter()
            try:
                info, scores = h2.fit_predict(
                    h2.dkt_model(epochs=h2.epochs_for(args), seed=h2.fold_seed(args, fold)),
                    sets[fold.index],
                )
            except Unavailable as unavailable:
                dkt_status = f"unavailable: {unavailable.reason}"
                log(f"    DKT unavailable — {unavailable.reason}")
                break
            stored = {"scores": scores, "epochs_run": info.get("epochs_run"),
                      "seconds": round(time.perf_counter() - started, 1)}
            checkpoint.save_dkt(fold.index, stored)
        fold_labels = [int(row.correct) for row in test_rows[fold.index]]
        dkt_folds.append({"index": fold.index, "auc": metrics.auc(fold_labels, stored["scores"]),
                          "epochs_run": stored["epochs_run"], "seconds": stored["seconds"]})
        dkt_scores.extend(stored["scores"])
        log(f"    DKT fold {fold.index + 1}: auc={dkt_folds[-1]['auc']:.4f}")

    # 4. Predictions and the pooled analysis, per setting.
    labels = [int(row.correct) for fold_rows in test_rows for row in fold_rows]
    pooled_learners = [row.user_id for fold_rows in test_rows for row in fold_rows]
    dkt_auc = metrics.auc(labels, dkt_scores) if dkt_status == "ok" else None
    gates["dkt"] = dkt_gate(dkt_auc, reference["pooled"].get(DKT))
    log(f"  DKT gate: {gates['dkt']}")

    results = []
    for index, (setting, grid, check) in enumerate(zip(settings, grids, checks)):
        pooled: dict[str, list[float]] = {name: [] for name in MODELS}
        fold_reports = []
        fit_log_likelihood = 0.0
        for fold in folds:
            params, meta, seconds = fits[(index, fold.index)]
            predictions = predict_fold(setting, params, sets[fold.index])
            fold_labels = [int(row.correct) for row in test_rows[fold.index]]
            for name in MODELS:
                pooled[name].extend(predictions[name])
            fit_log_likelihood += meta["fit_log_likelihood"]
            fold_reports.append({
                "index": fold.index,
                "counts": fold.counts() | {"test_answers": len(test_rows[fold.index])},
                "seconds": round(seconds, 1),
                "parameters": meta,
                "auc": {name: metrics.auc(fold_labels, predictions[name]) for name in MODELS},
            })
        if index == main_index:
            gates["pooled"] = reproduction_gate(
                "pooled", {name: metrics.auc(labels, pooled[name]) for name in MODELS},
                reference["pooled"],
            )
            if not gates["pooled"]["passed"]:
                raise ReproductionFailed(_gate_failure(gates["pooled"]))
        analysis = analyse(pooled, labels, pooled_learners,
                           replicates=args.replicates, seed=args.seed)
        log(f"  {setting.name}: " + ", ".join(
            f"{name} auc={analysis['models'][name]['scores']['auc']:.4f}" for name in MODELS
        ))
        if gates["dkt"]["passed"]:
            dkt_contrast = {"status": "ok"} | stats.bootstrap_auc_difference(
                labels, pooled[BKT_IRT], dkt_scores, pooled_learners,
                replicates=args.replicates, seed=args.seed,
            ).payload()
        else:
            dkt_contrast = {"status": "not_computed", "reason": "DKT qayta tiklanmadi"}
        bkt_irt_auc = analysis["models"][BKT_IRT]["scores"]["auc"]
        elo_auc = reference["pooled"].get(ELO)
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
            "dkt_difference": {"a": BKT_IRT, "b": DKT, "d56_margin": D56_MARGIN} | dkt_contrast,
            "elo_difference": {
                "a": BKT_IRT, "b": ELO, "elo_auc_h2": elo_auc,
                "difference": None if elo_auc is None or bkt_irt_auc is None
                else round(bkt_irt_auc - elo_auc, 6),
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
        seeds={"split": args.seed, "models": args.seed, "bootstrap": args.seed},
        argv=["python", "-m", "experiments.h2_bounds", *argv],
        packages=_packages(),
        git_start=git_start,
    )
    document = {
        "report": "h2_bounds",
        "spec": "D55",
        "quick": bool(args.quick),
        "thesis_result": not args.quick,
        "evaluation_protocol": h2.EVALUATION_PROTOCOL,
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
        "reference": reference,
        "gates": gates,
        "dkt": {"status": dkt_status, "auc": None if dkt_auc is None else round(dkt_auc, 6),
                "epochs": h2.epochs_for(args), "folds": dkt_folds},
        "checkpoint": checkpoint.payload(),
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
    parser.add_argument("--epochs", type=int, default=h2.FULL_EPOCHS,
                        help="DKT's epoch cap, as in H2 (--quick uses H2's quick cap).")
    parser.add_argument("--reference", default=None,
                        help="The H2 result directory the main setting must reproduce (required; "
                             "its metrics.json is read and its provenance checked).")
    parser.add_argument("--checkpoint-dir", default=CHECKPOINTS)
    parser.add_argument("--no-checkpoint", action="store_true")
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
    except ReproductionFailed as failed:
        # D58: the main setting does not reproduce H2; nothing is written.
        print(f"h2_bounds: reproduction gate failed — {failed}. Nothing was written.", file=sys.stderr)
        return 5

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
