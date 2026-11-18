"""
experiments/h2_tuned.py — H2's neural models, trained to convergence (D73).

    experiments/.venv/bin/python -m experiments.h2_tuned --quick
    experiments/.venv/bin/python -m experiments.h2_tuned

Why this run exists. In the main result the neural models stopped early for
reasons that had nothing to do with the data: DKT hit the 10-epoch ceiling in
all five folds with its validation AUC still rising, and AKT/AKT-R stopped at
epoch 3-4 under ``patience = 2``. H2's second condition was therefore tested
against an under-trained DKT. This run removes that doubt by giving the neural
models room — 200 epochs, ``patience = 10``, a hyper-parameter grid chosen on
validation AUC alone — and reports what the comparison looks like then.

It is a **post-hoc sensitivity analysis**. H2's verdict is not re-decided here:
that verdict was reached under a rule fixed before its result, and a second
look at the same data cannot be allowed to overturn it retroactively. What
D73 fixed in advance is how *this* table is read, and that rule is in
:func:`reading`.

Everything that could move a number is the main run's own code — ``h2.prepare``
(D50 cleaning, five learner folds, seed 20261006), ``h2.fold_sets``,
``h2.fit_predict`` (D57 evaluation), ``h2.analyse_pooled`` (bootstrap over
learners, DeLong, Holm). This module only chooses hyper-parameters and writes
its own result folder; ``h2.py`` and ``models/neural.py`` are untouched, so no
committed result depends on anything written here.

Two guards, both from the decision:

- **the control.** BKT+IRT (λ=0) is recomputed through the same path and its
  pooled AUC must equal the main result's to 1e-4. If it does not, the path is
  not the same path and no table is written;
- **the time gate.** After the first fold the total is extrapolated; past 24
  hours the run stops and says so instead of occupying the machine.

The test fold is never read during selection: a candidate is chosen on the
validation AUC its own ``fit`` reports, and the chosen candidate already holds
its best-validation weights, so it is not retrained afterwards.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from experiments import h2, metrics, orders, splits
from experiments.models import Unavailable
from experiments.provenance import GitState, Provenance, Source, results_dir

# D73's grid. DKT: embedding size x dropout x learning rate. AKT and AKT-R
# keep pyKT's architecture and vary only the learning rate.
DKT_EMB_SIZES: tuple[int, ...] = (64, 100, 200)
DKT_DROPOUTS: tuple[float, ...] = (0.1, 0.3)
LEARNING_RATES: tuple[float, ...] = (1e-3, 1e-4)

# pykt/models/train_model.py breaks at ``i - best_epoch >= 10``; 200 is the
# ceiling the sweeps in that repository use. The improvement threshold there
# is 1e-3 against this code's 1e-5, which stops *later* — in DKT's favour,
# which is the direction this analysis wants (D73).
TUNED_EPOCHS = 200
TUNED_PATIENCE = 10

QUICK_EPOCHS = 4
QUICK_PATIENCE = 2
QUICK_LEARNERS = 500

NEURAL_MODELS: tuple[str, ...] = ("DKT", "AKT", "AKT-R")
CONTROL = "BKT+IRT (λ=0)"

#: The main result this run has to reproduce on the control model (D73).
CONTROL_REFERENCE_AUC = 0.7239
CONTROL_TOLERANCE = 1e-4

#: D73's reading rule: the lower end of BKT+IRT - DKT.
SECOND_CONDITION_FLOOR = -0.01
HOLDS = "ikkinchi shart to‘liq o‘qitilgan DKT ga nisbatan ham bajariladi"
LIMITED = "ikkinchi shart faqat 10 epoch bilan cheklangan DKT ga nisbatan bajarilgan"
NOT_COMPUTED = "o‘qish qoidasi qo‘llanmadi — farq hisoblanmadi"

#: The time gate of D73, in hours.
TIME_BUDGET_HOURS = 24.0

#: Where a finished fold is parked so an interrupted pass resumes (rule 8).
CHECKPOINTS = "experiments/.runs/checkpoints"


class Checkpoint:
    """
    Finished folds, so a pass that is killed does not start from zero.

    Keyed by the digest of everything that could change a number — commit,
    seed, folds, epochs, patience, the grid, the quick flag — and the key is
    stored and compared, so a changed setting starts afresh instead of mixing
    two runs. Nothing here is a result: ``results/`` is written at the end
    and only from the finished document (D48).

    ``benchmarks/runner.py`` has the same class for stage 9. It is not
    imported here because that module imports Django, and the experiments
    deliberately do not.
    """

    def __init__(self, root: str | Path, key: dict, *, enabled: bool) -> None:
        import hashlib

        self.key = key
        self.enabled = enabled
        self.digest = hashlib.sha256(
            json.dumps(key, sort_keys=True).encode()
        ).hexdigest()[:16]
        self.directory = Path(root) / f"h2-tuned-{self.digest}"
        self.resumed = 0

    def _matches(self) -> bool:
        stored = self.directory / "key.json"
        if not stored.exists():
            return False
        return json.loads(stored.read_text(encoding="utf-8")) == self.key

    def load(self, name: str):
        if not self.enabled or not self._matches():
            return None
        path = self.directory / f"{name}.json"
        if not path.exists():
            return None
        self.resumed += 1
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, name: str, payload) -> None:
        if not self.enabled:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        stored = self.directory / "key.json"
        if not stored.exists():
            stored.write_text(json.dumps(self.key, sort_keys=True), encoding="utf-8")
        temporary = self.directory / f"{name}.tmp"
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        temporary.replace(self.directory / f"{name}.json")

    def payload(self) -> dict:
        return {
            "enabled": self.enabled,
            "key_digest": self.digest,
            "resumed_folds": self.resumed,
        }


# ---------------------------------------------------------------------------
# The grid
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Candidate:
    """One point of the grid, and how to build the model it names."""

    model: str
    emb_size: int | None
    dropout: float | None
    learning_rate: float

    def label(self) -> str:
        parts = [f"lr={self.learning_rate:g}"]
        if self.emb_size is not None:
            parts.insert(0, f"emb={self.emb_size}")
        if self.dropout is not None:
            parts.insert(1, f"dropout={self.dropout:g}")
        return ", ".join(parts)

    def payload(self) -> dict:
        return {
            "model": self.model,
            "emb_size": self.emb_size,
            "dropout": self.dropout,
            "learning_rate": self.learning_rate,
            "label": self.label(),
        }

    def build(self, *, epochs: int, patience: int, seed: int):
        from experiments.models.neural import AKTModel, AKTRModel, DKTModel

        common = {
            "epochs": epochs, "patience": patience,
            "seed": seed, "learning_rate": self.learning_rate,
        }
        if self.model == "DKT":
            return DKTModel(emb_size=self.emb_size, dropout=self.dropout, **common)
        if self.model == "AKT":
            return AKTModel(**common)
        if self.model == "AKT-R":
            return AKTRModel(**common)
        raise ValueError(f"unknown model {self.model!r}")


def grid(model: str) -> tuple[Candidate, ...]:
    """D73's candidates for one model, in a fixed order."""
    if model == "DKT":
        return tuple(
            Candidate("DKT", emb, dropout, lr)
            for emb in DKT_EMB_SIZES
            for dropout in DKT_DROPOUTS
            for lr in LEARNING_RATES
        )
    return tuple(Candidate(model, None, None, lr) for lr in LEARNING_RATES)


# ---------------------------------------------------------------------------
# One fold
# ---------------------------------------------------------------------------

def select(
    model_name: str,
    sets: dict[str, list],
    *,
    epochs: int,
    patience: int,
    seed: int,
    log=print,
) -> dict:
    """
    Fit every candidate and keep the one with the best **validation** AUC.

    The test fold is not touched here. The winner is returned already fitted
    and already holding its best-validation weights, so it is scored without
    a second training run — refitting it would only reintroduce the question
    of which weights were used.
    """
    candidates = grid(model_name)
    trials: list[dict] = []
    best: tuple[float, Candidate, object, dict] | None = None

    for candidate in candidates:
        started = time.perf_counter()
        built = candidate.build(epochs=epochs, patience=patience, seed=seed)
        try:
            info = built.fit(sets["train"], sets["validation"])
        except Unavailable as unavailable:
            trials.append({
                **candidate.payload(),
                "status": "unavailable", "reason": unavailable.reason,
            })
            log(f"      {candidate.label():34s} unavailable — {unavailable.reason}")
            continue
        seconds = time.perf_counter() - started
        auc = info.get("best_validation_auc")
        trials.append({
            **candidate.payload(),
            "status": "ok",
            "validation_auc": auc,
            "epochs_run": info.get("epochs_run"),
            "seconds": round(seconds, 1),
        })
        log(f"      {candidate.label():34s} val_auc={_text(auc)} "
            f"epochs={info.get('epochs_run')} ({seconds:.0f}s)")
        if auc is not None and (best is None or auc > best[0]):
            best = (auc, candidate, built, info)

    if best is None:
        raise Unavailable(model_name, "hech bir nomzod validatsiya AUC bermadi")
    auc, candidate, built, info = best
    log(f"    {model_name:6s} chose {candidate.label()} (val_auc={_text(auc)})")
    return {
        "model": model_name,
        "chosen": candidate.payload(),
        "validation_auc": auc,
        "fit": info,
        "trials": trials,
        "candidates": len(candidates),
        "fitted": built,
    }


def run_fold(
    fold,
    rows,
    *,
    params,
    epochs: int,
    patience: int,
    seed: int,
    log=print,
) -> tuple[dict, dict]:
    """One fold: the control model, then each neural model's grid."""
    from experiments.models.classical import BKTFamily

    sets = h2.fold_sets(fold, rows)
    test = sets["test"]
    labels = [int(row.correct) for row in test]
    learners = [row.user_id for row in test]

    report: dict = {"index": fold.index, "counts": fold.counts() | {
        "test_answers": len(test)}, "models": {}}
    predictions: dict[str, list[float]] = {}

    control = BKTFamily(CONTROL, use_irt=True, use_prereq_init=False, params=params)
    started = time.perf_counter()
    info, scores = h2.fit_predict(control, sets)
    measured = metrics.by_first_k(labels, scores, learners)
    report["models"][CONTROL] = {
        "status": "ok", "fit": info, "scores": measured,
        "seconds": round(time.perf_counter() - started, 1),
    }
    predictions[CONTROL] = scores
    log(f"    {CONTROL:16s} auc={_text(measured['all']['auc'])} (control)")

    for name in NEURAL_MODELS:
        started = time.perf_counter()
        try:
            selection = select(
                name, sets, epochs=epochs, patience=patience, seed=seed, log=log,
            )
        except Unavailable as unavailable:
            report["models"][name] = {
                "status": "unavailable", "reason": unavailable.reason,
            }
            log(f"    {name:16s} unavailable — {unavailable.reason}")
            continue

        built = selection.pop("fitted")
        scores = built.predict(test)
        if len(scores) != len(test):
            raise RuntimeError(
                f"{name} returned {len(scores)} predictions for {len(test)} answers"
            )
        measured = metrics.by_first_k(labels, scores, learners)
        entry = {
            "status": "ok",
            "selection": selection,
            "fit": selection["fit"],
            "scores": measured,
            "seconds": round(time.perf_counter() - started, 1),
        }
        cold = getattr(built, "cold_rows", None)
        if cold is not None:
            entry["cold_rows"] = cold
        unseen = getattr(built, "unseen_rows", None)
        if unseen is not None:
            entry["unseen_rows"] = unseen
        report["models"][name] = entry
        predictions[name] = scores
        log(f"    {name:16s} auc={_text(measured['all']['auc'])} "
            f"rmse={_text(measured['all']['rmse'])}  ({entry['seconds']:.0f}s)")

    return report, (predictions, labels, learners)


# ---------------------------------------------------------------------------
# The two guards and the reading rule
# ---------------------------------------------------------------------------

def control_check(analysis: dict) -> dict:
    """The control model has to land on the main run's pooled AUC (D73)."""
    entry = (analysis.get("models") or {}).get(CONTROL) or {}
    auc = ((entry.get("scores") or {}).get("all") or {}).get("auc")
    difference = None if auc is None else round(abs(auc - CONTROL_REFERENCE_AUC), 6)
    return {
        "model": CONTROL,
        "reference_auc": CONTROL_REFERENCE_AUC,
        "auc": auc,
        "absolute_difference": difference,
        "tolerance": CONTROL_TOLERANCE,
        "agrees": bool(difference is not None and difference <= CONTROL_TOLERANCE),
    }


def time_gate(seconds_first_fold: float, folds: int) -> dict:
    """D73's 24-hour gate, extrapolated linearly from the first fold."""
    projected = seconds_first_fold * folds
    return {
        "first_fold_seconds": round(seconds_first_fold, 1),
        "folds": folds,
        "projected_seconds": round(projected, 1),
        "projected_hours": round(projected / 3600.0, 2),
        "budget_hours": TIME_BUDGET_HOURS,
        "within_budget": bool(projected <= TIME_BUDGET_HOURS * 3600.0),
    }


def reading(analysis: dict) -> dict:
    """
    D73's rule, fixed before the numbers.

    The lower end of the BKT+IRT - DKT interval decides, and nothing else:
    at or above -0.01 the second condition survives full training, below it
    the condition is recorded as holding only against the 10-epoch DKT.
    """
    contrast = next(
        (item for item in analysis.get("contrasts", [])
         if item.get("a") == CONTROL and item.get("b") == "DKT"),
        None,
    )
    low = None if not contrast or contrast.get("status") != "ok" else contrast.get("ci_low")
    if low is None:
        status = NOT_COMPUTED
    elif low >= SECOND_CONDITION_FLOOR:
        status = HOLDS
    else:
        status = LIMITED
    return {
        "rule": (
            "D73: BKT+IRT − DKT farqining 95 % CI pastki chegarasi "
            "SECOND_CONDITION_FLOOR dan kichik bo‘lmasa — ikkinchi shart to‘liq "
            "o‘qitilgan DKT ga nisbatan ham bajariladi"
        ),
        "floor": SECOND_CONDITION_FLOOR,
        "ci_low": low,
        "status": status,
        "post_hoc": True,
        "note": (
            "H2 ning asosiy hukmi o‘zgarmaydi: u natijadan oldin belgilangan "
            "qoida bo‘yicha chiqarilgan (D56, D59). Bu — post-hoc sezgirlik."
        ),
    }


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def run(args, argv: list[str]) -> tuple[dict, Provenance]:
    from experiments.datasets import assist09  # noqa: F401 - h2.prepare uses it

    git_start = GitState.capture()
    dataset, rows, learners, folds = h2.prepare(args)
    epochs = QUICK_EPOCHS if args.quick else args.epochs
    patience = QUICK_PATIENCE if args.quick else args.patience
    workers = max(1, min(args.workers, len(folds)))

    print(f"  grid: DKT {len(grid('DKT'))} candidates, "
          f"AKT/AKT-R {len(grid('AKT'))} each; "
          f"epochs={epochs}, patience={patience}")
    print(f"  fitting the BKT parameters of {len(folds)} folds on {workers} worker(s)")
    fitted = h2.fit_parameters(folds, rows, workers=workers)

    checkpoint = Checkpoint(
        args.checkpoint_dir,
        {
            "commit": git_start.commit,
            "dirty": git_start.dirty,
            "seed": args.seed,
            "folds": args.folds,
            "validation_fraction": args.validation_fraction,
            "epochs": epochs,
            "patience": patience,
            "quick": bool(args.quick),
            "quick_learners": args.quick_learners if args.quick else None,
            "grid_dkt": [candidate.payload() for candidate in grid("DKT")],
            "grid_attention": [candidate.payload() for candidate in grid("AKT")],
        },
        enabled=bool(git_start.dirty is False and not args.no_checkpoint),
    )
    print(f"  checkpoint: {checkpoint.directory if checkpoint.enabled else 'off (tree not clean or --no-checkpoint)'}")

    fold_reports, fold_outputs = [], []
    gate: dict | None = None
    for position, fold in enumerate(folds):
        print(f"  fold {fold.index + 1}/{len(folds)}: {fold.counts()}")
        stored = checkpoint.load(f"fold-{fold.index}")
        if stored is not None:
            print(f"  fold {fold.index + 1}: resumed from the checkpoint")
            fold_reports.append(stored["report"])
            fold_outputs.append((
                stored["predictions"], stored["labels"], stored["learners"],
            ))
            if position == 0 and stored.get("gate"):
                gate = stored["gate"]
            continue

        started = time.perf_counter()
        report, output = run_fold(
            fold, rows, params=fitted[fold.index][0],
            epochs=epochs, patience=patience,
            seed=h2.fold_seed(args, fold), log=print,
        )
        elapsed = time.perf_counter() - started
        fold_reports.append(report)
        fold_outputs.append(output)

        if position == 0:
            gate = time_gate(elapsed, len(folds))
            print(f"  time gate: first fold {gate['first_fold_seconds']}s → "
                  f"{gate['projected_hours']}h projected "
                  f"(budget {gate['budget_hours']}h)")
            if not gate["within_budget"] and not args.ignore_time_gate:
                print(
                    "  STOPPED: the projection is past D73's 24-hour budget. "
                    "No result folder is written. Re-run with --ignore-time-gate "
                    "to proceed anyway.",
                    file=sys.stderr,
                )
                return {"report": "h2_tuned", "stopped": "time_gate", "time_gate": gate}, None

        predictions, labels_, learners_ = output
        checkpoint.save(f"fold-{fold.index}", {
            "report": report,
            "predictions": predictions,
            "labels": labels_,
            "learners": learners_,
            "gate": gate if position == 0 else None,
        })

    pooled, labels, pooled_learners = h2.pool(fold_outputs)
    print(f"  pooled {len(labels)} answers from {len(set(pooled_learners))} learners")

    first_rows: list[bool] = []
    for fold in folds:
        first_rows.extend(orders.first_in_order(splits.subset(rows, fold.test)))
    cold: dict[str, int] = {}
    for report in fold_reports:
        for name, entry in report["models"].items():
            if "cold_rows" in entry:
                cold[name] = cold.get(name, 0) + entry["cold_rows"]

    analysis = h2.analyse_pooled(
        pooled, labels, pooled_learners,
        replicates=args.replicates, seed=args.seed,
        cold_rows=cold, first_in_order=first_rows,
    )
    control = control_check(analysis)
    print(f"  control {CONTROL}: auc={_text(control['auc'])} "
          f"(reference {control['reference_auc']}, agrees={control['agrees']})")
    if not control["agrees"] and not args.ignore_control:
        raise RuntimeError(
            f"the control model did not reproduce the main result "
            f"({control['auc']} vs {control['reference_auc']}): the evaluation "
            "path is not the same, so no table is written (D73)"
        )

    provenance = Provenance.capture(
        sources=(Source.of("assistments2009", dataset.path),),
        seeds={"split": args.seed, "models": args.seed, "bootstrap": args.seed},
        argv=["python", "-m", "experiments.h2_tuned", *argv],
        packages=h2._packages(),
        git_start=git_start,
    )
    document = {
        "report": "h2_tuned",
        "spec": "D73",
        "quick": bool(args.quick),
        "thesis_result": not args.quick,
        "post_hoc": True,
        "provenance": provenance.payload(),
        "dataset": dataset.metadata() | {
            "status": "ok",
            "name": "assistments2009",
            "label": "ASSISTments 2009–2010 skill builder",
            "source": asdict(provenance.sources[0]),
            "learners_used": len(learners),
            "answers_used": len(rows),
        },
        "split": splits.metadata(
            folds, seed=args.seed, validation_fraction=args.validation_fraction,
        ),
        "training": {
            "epochs_max": epochs,
            "patience": patience,
            "pykt_patience": TUNED_PATIENCE,
            "pykt_improvement_threshold": 1e-3,
            "this_improvement_threshold": 1e-5,
            "grid_dkt": [candidate.payload() for candidate in grid("DKT")],
            "grid_attention": [candidate.payload() for candidate in grid("AKT")],
            # Counted here, not in the renderer: a number a table computes is
            # a number metrics.json cannot vouch for (D48).
            "grid_dkt_candidates": len(grid("DKT")),
            "grid_attention_candidates": len(grid("AKT")),
            "selected_on": "validation_auc",
        },
        "parameter_fit_workers": workers,
        "checkpoint": checkpoint.payload(),
        "time_gate": gate,
        "control_check": control,
        "folds": fold_reports,
        "pooled": analysis,
        "reading": reading(analysis),
    }
    return document, provenance


def _text(value) -> str:
    return "—" if value is None else f"{value:.4f}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.h2_tuned",
        description="H2's neural models trained to convergence (D73, post-hoc).",
    )
    parser.add_argument("--data", default=None)
    parser.add_argument("--quick", action="store_true",
                        help=f"{QUICK_LEARNERS} learners, {QUICK_EPOCHS} epochs — pipeline only.")
    parser.add_argument("--quick-learners", type=int, default=QUICK_LEARNERS)
    parser.add_argument("--original-only", action="store_true")
    parser.add_argument("--folds", type=int, default=splits.DEFAULT_FOLDS)
    parser.add_argument("--validation-fraction", type=float,
                        default=splits.DEFAULT_VALIDATION_FRACTION)
    parser.add_argument("--epochs", type=int, default=TUNED_EPOCHS)
    parser.add_argument("--patience", type=int, default=TUNED_PATIENCE)
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=splits.DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--checkpoint-dir", default=CHECKPOINTS)
    parser.add_argument("--no-checkpoint", action="store_true")
    parser.add_argument("--ignore-time-gate", action="store_true",
                        help="Run past D73's 24-hour projection (recorded in the metrics).")
    parser.add_argument("--ignore-control", action="store_true",
                        help="Write the table even if the control model disagrees.")
    parser.add_argument("--out", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    from experiments import tables
    from experiments.h2_tuned_tables import render

    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)

    print("h2_tuned (D73) — ASSISTments 2009, neural models trained to convergence")
    document, provenance = run(args, argv)
    if document.get("stopped"):
        print(json.dumps(document["time_gate"], indent=2))
        return 2

    directory = (
        Path(args.out).expanduser() if args.out
        else results_dir(
            "assist09-neural-tuned-quick" if args.quick else "assist09-neural-tuned",
        )
    )
    written = tables.write(directory, document, provenance.env_txt(), renderer=render)
    print(f"\nwritten to {directory}")
    for path in written.values():
        print(f"  {path.name}")
    print(f"D73: {document['reading']['status']}")
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
