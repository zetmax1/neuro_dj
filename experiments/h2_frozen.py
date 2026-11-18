"""
experiments/h2_frozen.py — D60: item difficulty frozen at test time.

Why. In chapter II's model the item difficulty is online: ``b_q −= K(n_q)(x − p)``
after every answer, from every learner. Over a test fold that makes one
learner's prediction depend on the other test learners' answers, and the
stream is ordered by ``user_id`` rather than by time (verification/REPORT.md,
K-2). D57 is not violated — it governs the learner's own history, and b_q is a
property of the item — but how much H2's claims lean on that stream order has
to be measured.

What this run does. The same cleaning, split, seeds and D57 protocol as H2, at
chapter II's bounds only, for two variants of the same fitted models:

* ``current`` — exactly H2: b_q and n_q keep moving over the test stream;
* ``frozen`` — b_q and n_q stay where the training fold left them, while θ
  keeps following the learner's own answers.

Each model is fitted **once** and then asked for both variants, so the two
columns differ in the test-time rule and in nothing else. BKT is the control:
with ``use_irt=False`` it never reads b_q, so freezing must leave it bit for
bit identical, and the run checks that.

DKT is a frozen model by construction (its weights stop moving after
training), so it is the same scores in both columns; it is here because D56 is
stated against it, and it passes D58's |Δ| ≤ 5e-4 gate against H2's own DKT.
AKT and AKT-R are frozen in the same way and add nothing to the question, so
they are not re-run. PFA's coefficients are fitted on the training fold and its
prediction-time counts are per learner, so PFA has no frozen variant either
(D60, with the lines of ``models/classical.py`` that show it).

Reads nothing from the network (D49). Writes one result directory (D48).

    python -m experiments.h2_frozen --reference experiments/results/assist09/<ts>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from experiments import h2, h2_bounds, metrics, orders, splits, tables
from experiments.datasets import DatasetMissing
from experiments.models import Unavailable
from experiments.models.classical import CONSTANTS, BKTFamily, EloRasch
from experiments.provenance import GitState, Provenance, Source, results_dir

BKT = "BKT"
BKT_IRT = "BKT+IRT (λ=0)"
ELO = "Elo/Rasch"
DKT = "DKT"

# The models this run reports, in table order. DKT comes from the retrained
# (or checkpointed) scores, the other three from the two-variant pass.
MODELS: tuple[str, ...] = (BKT, BKT_IRT, ELO, DKT)
# The three models whose test-time rule the variants differ in.
VARIED: tuple[str, ...] = (BKT, BKT_IRT, ELO)
VARIANTS: tuple[str, ...] = ("current", "frozen")

# D60: the differences the two variants are compared on. The first two are
# H2's own (D53, D56); the third is the one the frozen rule touches most, since
# Elo/Rasch is nothing but θ and b.
CONTRASTS: tuple[tuple[str, str, str], ...] = (
    (BKT_IRT, BKT, "D53"),
    (BKT_IRT, DKT, "D56"),
    (ELO, DKT, "D60"),
)

# D56's margin, and the digits the reproduction gate compares on (D58).
D56_MARGIN = -0.01
GATE_DIGITS = 6
DKT_TOLERANCE = h2_bounds.DKT_TOLERANCE
DEFAULT_REPLICATES = 1000
CHECKPOINTS = h2_bounds.CHECKPOINTS


class GateFailed(RuntimeError):
    """A gate of D60 did not hold; nothing is written."""


# ---------------------------------------------------------------------------
# The models, fitted once and asked twice
# ---------------------------------------------------------------------------


def build(params) -> dict:
    """The three varied models, unfrozen; the flag is flipped after fitting."""
    return {
        BKT: BKTFamily(BKT, use_irt=False, use_prereq_init=False, params=params),
        BKT_IRT: BKTFamily(BKT_IRT, use_irt=True, use_prereq_init=False, params=params),
        ELO: EloRasch(),
    }


def predict_both(model, sets: dict[str, list]) -> tuple[dict, dict[str, list[float]]]:
    """
    Fit once, predict twice: once as H2 does, once with the items held still.

    The fitted state is the same object in both passes — ``predict`` copies the
    item dictionaries it starts from — so the only difference between the two
    score vectors is the test-time rule.
    """
    info = model.fit(sets["fitting"], None)
    scores: dict[str, list[float]] = {}
    for variant in VARIANTS:
        model.freeze_items = variant == "frozen"
        produced = model.predict(sets["test"])
        if len(produced) != len(sets["test"]):
            raise RuntimeError(
                f"{model.name} returned {len(produced)} predictions for "
                f"{len(sets['test'])} answers"
            )
        scores[variant] = produced
    model.freeze_items = False
    return info, scores


# ---------------------------------------------------------------------------
# What may be reused from D55's full run
# ---------------------------------------------------------------------------


def reusable_checkpoint(*, dataset, args, root: str | Path | None = None) -> Path | None:
    """
    A D55 checkpoint directory whose key matches this run's data and split.

    Only the main setting's fits (``fit-0-*``) and the DKT scores are read, and
    both are then put through their own gate below. The key is compared on the
    fields that decide whether a fit is the same computation: the data file,
    the seeds, the mode and the split. The commit is deliberately *not*
    compared — the fits are a function of the data and the grid, and the grid
    is checked by the pooled-AUC gate.
    """
    root = Path(root if root is not None else CHECKPOINTS)
    if not root.exists():
        return None
    for directory in sorted(root.glob("h2-bounds-*")):
        key_path = directory / "key.json"
        if not key_path.exists():
            continue
        key = json.loads(key_path.read_text(encoding="utf-8"))
        same = (
            key.get("data_sha256") == dataset.sha256
            and bool(key.get("quick")) == bool(args.quick)
            and key.get("folds") == args.folds
            and key.get("validation_fraction") == args.validation_fraction
            and key.get("seeds", {}).get("split") == args.seed
            and key.get("protocol") == h2.EVALUATION_PROTOCOL
            and (key.get("settings") or [[None]])[0][:1] == ["asosiy"]
        )
        if not same:
            continue
        fits = [directory / f"fit-0-{index}.json" for index in range(args.folds)]
        if all(path.exists() for path in fits):
            return directory
    return None


def load_fits(directory: Path, folds) -> dict[int, tuple[dict, dict, float]]:
    """The main setting's per-fold BKT parameters from a D55 checkpoint."""
    from neuro_model.student import TopicParams

    out: dict[int, tuple[dict, dict, float]] = {}
    for fold in folds:
        payload = json.loads(
            (directory / f"fit-0-{fold.index}.json").read_text(encoding="utf-8")
        )
        params = {
            skill: TopicParams(**values) for skill, values in payload["params"].items()
        }
        out[fold.index] = (params, payload["meta"], payload["seconds"])
    return out


def load_dkt(directory: Path, folds, test_rows) -> dict | None:
    """
    The DKT scores of a D55 checkpoint, if they are there and fit the folds.

    A length mismatch means the split is not the one those scores were made
    for, which must stop the reuse rather than be padded over.
    """
    scores: dict[int, dict] = {}
    for fold in folds:
        path = directory / f"dkt-{fold.index}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if len(payload["scores"]) != len(test_rows[fold.index]):
            raise GateFailed(
                f"checkpoint {path.name} holds {len(payload['scores'])} scores for "
                f"{len(test_rows[fold.index])} test answers"
            )
        scores[fold.index] = payload
    return scores


# ---------------------------------------------------------------------------
# The analysis, per variant
# ---------------------------------------------------------------------------


def analyse(
    pooled: dict[str, list[float]],
    labels: list[int],
    learners: list[str],
    *,
    replicates: int,
    seed: int,
    first_in_order: list[bool],
) -> dict:
    """
    Intervals per model, the pairwise DeLong family with Holm, and D60's three
    contrasts with a paired bootstrap over learners.

    The shape follows ``h2.analyse_pooled`` so the tables read the same way;
    the contrast list is D60's, not H2's.
    """
    from experiments import stats

    out: dict = {
        "models": {},
        "comparisons": [],
        "replicates": replicates,
        "confidence_percent": int(round(stats.CONFIDENCE * 100)),
        "evaluation_protocol": h2.EVALUATION_PROTOCOL,
    }
    picked = [index for index, first in enumerate(first_in_order) if first]
    for name, scores in pooled.items():
        interval = stats.bootstrap_auc(
            labels, scores, learners, replicates=replicates, seed=seed, by_learner=True,
        )
        out["models"][name] = {
            "scores": metrics.by_first_k(labels, scores, learners),
            "auc_interval": interval.payload(),
            "first_in_order": metrics.score(
                [labels[index] for index in picked],
                [scores[index] for index in picked],
            ).payload(),
        }

    names = list(pooled)
    comparisons = []
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            comparisons.append(stats.delong_test(
                labels, pooled[left], pooled[right], name_a=left, name_b=right,
            ))
    out["comparisons"] = [item.payload() for item in stats.holm(comparisons)]

    out["contrasts"] = []
    for a, b, decision in CONTRASTS:
        entry: dict = {"a": a, "b": b, "decision": decision}
        missing = [name for name in (a, b) if name not in pooled]
        if missing:
            entry |= {"status": "unavailable", "missing": missing}
            out["contrasts"].append(entry)
            continue
        difference = stats.bootstrap_auc_difference(
            labels, pooled[a], pooled[b], learners, replicates=replicates, seed=seed,
        ).payload()
        family = next(
            (item for item in out["comparisons"] if {item["a"], item["b"]} == {a, b}), {},
        )
        entry |= {
            "status": "ok",
            "difference": difference["estimate"],
            "ci_low": difference["ci_low"],
            "ci_high": difference["ci_high"],
            "replicates": replicates,
            "clustered_by_learner": True,
            "delong_p": family.get("p"),
            "p_holm": family.get("p_holm"),
        }
        out["contrasts"].append(entry)
    return out


def claims(variants: dict) -> dict:
    """
    D53 and D56 in both variants, and whether the reading rule of D60 lets them
    be called robust.

    D53: the BKT+IRT − BKT interval is above zero. D56: the lower end of the
    BKT+IRT − DKT interval is at or above −0.01. "Robust" means both variants,
    which is what D60 fixed before the numbers existed.
    """
    def contrast(variant: str, a: str, b: str) -> dict:
        for entry in variants[variant]["contrasts"]:
            if (entry["a"], entry["b"]) == (a, b):
                return entry
        return {}

    out: dict = {"d56_margin": D56_MARGIN}
    d53 = {
        variant: contrast(variant, BKT_IRT, BKT) for variant in VARIANTS
    }
    d56 = {
        variant: contrast(variant, BKT_IRT, DKT) for variant in VARIANTS
    }
    out["D53"] = {
        "statement": "BKT+IRT (λ=0) − BKT > 0",
        "per_variant": {
            variant: {
                "difference": entry.get("difference"),
                "ci_low": entry.get("ci_low"),
                "ci_high": entry.get("ci_high"),
                "holds": bool(entry.get("status") == "ok" and entry["ci_low"] > 0.0),
            }
            for variant, entry in d53.items()
        },
    }
    out["D56"] = {
        "statement": "BKT+IRT (λ=0) − DKT, CI lower end ≥ −0.01",
        "per_variant": {
            variant: {
                "difference": entry.get("difference"),
                "ci_low": entry.get("ci_low"),
                "ci_high": entry.get("ci_high"),
                "holds": bool(
                    entry.get("status") == "ok" and entry["ci_low"] >= D56_MARGIN
                ),
            }
            for variant, entry in d56.items()
        },
    }
    for key in ("D53", "D56"):
        out[key]["robust"] = all(
            item["holds"] for item in out[key]["per_variant"].values()
        )
    return out


# ---------------------------------------------------------------------------
# The gates (D60)
# ---------------------------------------------------------------------------


def reproduction_gate(current: dict, reference: dict) -> dict:
    """
    The unfrozen column must be H2 to six digits for BKT and BKT+IRT.

    This is what makes the frozen column readable: if the unfrozen numbers are
    H2's own, the difference between the columns is the frozen rule and not a
    different fit, a different split or a different grid.
    """
    models = {}
    for name in (BKT, BKT_IRT):
        produced = current["models"][name]["scores"]["all"]["auc"]
        expected = reference["pooled"].get(name)
        models[name] = {
            "frozen_run": round(produced, GATE_DIGITS),
            "h2": None if expected is None else round(expected, GATE_DIGITS),
            "equal": expected is not None
            and round(produced, GATE_DIGITS) == round(expected, GATE_DIGITS),
        }
    return {
        "where": "pooled, unfrozen",
        "digits": GATE_DIGITS,
        "models": models,
        "passed": all(entry["equal"] for entry in models.values()),
    }


def control_gate(pooled: dict[str, dict[str, list[float]]]) -> dict:
    """
    BKT never reads b_q, so freezing the items may not move it at all.

    Compared on the score vectors themselves, not on the rounded AUC: a
    difference here would mean the flag reaches something it should not.
    """
    current, frozen = pooled["current"][BKT], pooled["frozen"][BKT]
    largest = max(
        (abs(a - b) for a, b in zip(current, frozen)), default=0.0,
    )
    return {
        "model": BKT,
        "answers": len(current),
        "identical_predictions": current == frozen,
        "largest_difference": largest,
        "passed": current == frozen,
    }


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------


def _fit_parameters(folds, rows, args, *, log) -> tuple[dict, dict]:
    """Fit the per-fold BKT parameters from scratch, as H2 does."""
    workers = max(1, min(args.workers, len(folds)))
    log(f"  fitting the BKT parameters of {len(folds)} folds on {workers} worker(s)")
    started = time.perf_counter()
    fitted = h2.fit_parameters(folds, rows, workers=workers)
    return fitted, {
        "source": "fitted",
        "checkpoint": None,
        "files": [],
        "workers": workers,
        "seconds": round(time.perf_counter() - started, 1),
    }


def _predict_folds(folds, sets, test_rows, fitted, *, log) -> tuple[dict, list[dict]]:
    """
    Both variants of the three varied models, fold by fold.

    Returns the pooled score vectors per variant and the per-fold report.
    """
    pooled: dict[str, dict[str, list[float]]] = {
        variant: {name: [] for name in VARIED} for variant in VARIANTS
    }
    fold_reports = []
    for fold in folds:
        log(f"  fold {fold.index + 1}/{len(folds)}: {fold.counts()}")
        params, params_meta, seconds = fitted[fold.index]
        report = {
            "index": fold.index,
            "counts": fold.counts(),
            "parameters": params_meta | {"seconds": round(seconds, 1)},
            "models": {},
        }
        labels = [int(row.correct) for row in test_rows[fold.index]]
        for name, model in build(params).items():
            try:
                info, scores = predict_both(model, sets[fold.index])
            except Unavailable as unavailable:  # pragma: no cover - E_P is absent here
                report["models"][name] = {
                    "status": "unavailable", "reason": unavailable.reason,
                }
                log(f"    {name:16s} unavailable — {unavailable.reason}")
                continue
            entry = {"status": "ok", "fit": info, "variants": {}}
            for variant in VARIANTS:
                pooled[variant][name].extend(scores[variant])
                entry["variants"][variant] = {"auc": metrics.auc(labels, scores[variant])}
            report["models"][name] = entry
            log(
                f"    {name:16s} current={entry['variants']['current']['auc']:.4f} "
                f"frozen={entry['variants']['frozen']['auc']:.4f}"
            )
        fold_reports.append(report)
    return pooled, fold_reports


def _reproduces(pooled: dict, labels: list[int], reference: dict) -> bool:
    """H2's unfrozen BKT and BKT+IRT to six digits, without any bootstrap."""
    for name in (BKT, BKT_IRT):
        expected = reference["pooled"].get(name)
        produced = metrics.auc(labels, pooled["current"][name])
        if expected is None or produced is None:
            return False
        if round(produced, GATE_DIGITS) != round(expected, GATE_DIGITS):
            return False
    return True


def _dkt_scores(folds, sets, test_rows, *, epochs, args, stored, log):
    """DKT per fold, from a checkpoint payload or by training it again."""
    dkt_folds, dkt_scores = [], []
    for fold in folds:
        labels = [int(row.correct) for row in test_rows[fold.index]]
        if stored is not None:
            payload = stored[fold.index]
        else:
            started = time.perf_counter()
            info, scores = h2.fit_predict(
                h2.dkt_model(epochs=epochs, seed=h2.fold_seed(args, fold)),
                sets[fold.index],
            )
            payload = {
                "scores": scores, "epochs_run": info.get("epochs_run"),
                "seconds": round(time.perf_counter() - started, 1),
            }
        dkt_folds.append({
            "index": fold.index,
            "auc": metrics.auc(labels, payload["scores"]),
            "epochs_run": payload["epochs_run"],
            "seconds": payload["seconds"],
        })
        dkt_scores.extend(payload["scores"])
        log(f"    DKT fold {fold.index + 1}: auc={dkt_folds[-1]['auc']:.4f}")
    return dkt_folds, dkt_scores


def run(
    args,
    argv: list[str],
    *,
    dataset=None,
    reference: dict | None = None,
    log=print,
) -> tuple[dict, Provenance]:
    """
    The run. ``dataset`` and ``reference`` are injected by the tests, which
    use H2 itself as the oracle rather than a file on disk (as D55's tests do).
    """
    git_start = GitState.capture()
    dataset, rows, learners, folds = h2.prepare(args, dataset=dataset, log=log)
    epochs = h2.epochs_for(args)

    if reference is None:
        reference = h2_bounds.load_reference(args.reference, dataset=dataset, args=args)
    log(f"  reference {reference['path']} ({reference['commit']})")
    if reference.get("learners") not in (None, len(learners)):
        raise GateFailed(
            f"reference has {reference['learners']} learners, this run {len(learners)}"
        )

    sets = {fold.index: h2.fold_sets(fold, rows) for fold in folds}
    test_rows = {fold.index: sets[fold.index]["test"] for fold in folds}
    labels = [int(row.correct) for fold in folds for row in test_rows[fold.index]]
    pooled_learners = [row.user_id for fold in folds for row in test_rows[fold.index]]

    # 1. The BKT parameters. D55's full-run fits are reused when they are there
    #    and when they reproduce H2 unfrozen to six digits (D60's first gate);
    #    otherwise they are refitted, which is what the decision asks for.
    checkpoint = None if args.no_checkpoint else reusable_checkpoint(dataset=dataset, args=args)
    if checkpoint is not None:
        fitted = load_fits(checkpoint, folds)
        parameters = {
            "source": "checkpoint",
            "checkpoint": checkpoint.name,
            "files": [f"fit-0-{fold.index}.json" for fold in folds],
            "workers": 0,
            "seconds": round(sum(entry[2] for entry in fitted.values()), 1),
        }
        log(f"  BKT parameters from {checkpoint.name} (fit-0-*)")
    else:
        fitted, parameters = _fit_parameters(folds, rows, args, log=log)

    # 2. The three varied models, both variants.
    pooled, fold_reports = _predict_folds(folds, sets, test_rows, fitted, log=log)

    if parameters["source"] == "checkpoint" and _reproduces(pooled, labels, reference):
        log(f"  checkpointed parameters reproduce H2 to {GATE_DIGITS} digits")
    elif parameters["source"] == "checkpoint":
        log("  the checkpointed parameters do not reproduce H2 — refitting")
        parameters["rejected_checkpoint"] = parameters["checkpoint"]
        fitted, parameters = _fit_parameters(folds, rows, args, log=log)
        parameters["rejected_checkpoint"] = checkpoint.name
        pooled, fold_reports = _predict_folds(folds, sets, test_rows, fitted, log=log)
        checkpoint = None

    # 3. DKT: one set of scores for both columns, from the checkpoint when it
    #    passes D58's gate and retrained when it does not.
    stored = load_dkt(checkpoint, folds, test_rows) if checkpoint is not None else None
    dkt_source = "checkpoint" if stored is not None else "trained"
    dkt_folds, dkt_scores = _dkt_scores(
        folds, sets, test_rows, epochs=epochs, args=args, stored=stored, log=log,
    )
    dkt_gate = h2_bounds.dkt_gate(
        metrics.auc(labels, dkt_scores), reference["pooled"].get(DKT),
        tolerance=DKT_TOLERANCE,
    )
    if dkt_source == "checkpoint" and not dkt_gate["passed"]:
        log(f"  the checkpointed DKT is outside D58's gate ({dkt_gate}) — retraining")
        dkt_folds, dkt_scores = _dkt_scores(
            folds, sets, test_rows, epochs=epochs, args=args, stored=None, log=log,
        )
        dkt_source = "trained"
        dkt_gate = h2_bounds.dkt_gate(
            metrics.auc(labels, dkt_scores), reference["pooled"].get(DKT),
            tolerance=DKT_TOLERANCE,
        )
    for variant in VARIANTS:
        pooled[variant][DKT] = dkt_scores

    # 4. The pooled analysis of each variant.
    first_rows: list[bool] = []
    for fold in folds:
        first_rows.extend(orders.first_in_order(test_rows[fold.index]))
    log(f"  pooled {len(labels)} answers from {len(set(pooled_learners))} learners")

    variants = {}
    for variant in VARIANTS:
        log(f"  analysing the {variant} variant ({args.replicates} replicates)…")
        variants[variant] = analyse(
            pooled[variant], labels, pooled_learners,
            replicates=args.replicates, seed=args.seed, first_in_order=first_rows,
        )

    gates = {
        "reproduction": reproduction_gate(variants["current"], reference),
        "dkt": dkt_gate,
        "bkt_control": control_gate(pooled),
    }
    for name, gate in gates.items():
        log(f"  gate {name}: {'passed' if gate['passed'] else 'FAILED'}")
    if not gates["reproduction"]["passed"]:
        raise GateFailed(
            f"the unfrozen column is not H2 to {GATE_DIGITS} digits: "
            f"{gates['reproduction']['models']}"
        )
    if not gates["bkt_control"]["passed"]:
        raise GateFailed(
            f"freezing the items moved BKT, which never reads b_q: {gates['bkt_control']}"
        )

    provenance = Provenance.capture(
        sources=(Source.of("assistments2009", dataset.path),),
        seeds={"split": args.seed, "models": args.seed, "bootstrap": args.seed},
        argv=["python", "-m", "experiments.h2_frozen", *argv],
        packages=h2._packages(),
        git_start=git_start,
    )
    document = {
        "report": "h2_frozen",
        "spec": "D60",
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
        "split": splits.metadata(
            folds, seed=args.seed, validation_fraction=args.validation_fraction,
        ),
        "epochs": epochs,
        "replicates": args.replicates,
        "confidence_percent": variants["current"]["confidence_percent"],
        "chapter_two_bounds": {"g_max": CONSTANTS.g_max, "s_max": CONSTANTS.s_max},
        "models": list(MODELS),
        "varied_models": list(VARIED),
        "variants_compared": list(VARIANTS),
        "frozen_rule": {
            "items_frozen_at_test_time": True,
            "theta_follows_the_learner": True,
            "bkt_parameters_unchanged": True,
        },
        "reference": reference,
        "parameters": parameters,
        "dkt": {
            "source": dkt_source,
            "auc": round(metrics.auc(labels, dkt_scores), 6),
            "epochs": epochs,
            "folds": dkt_folds,
        },
        "gates": gates,
        "variants": variants,
        "claims": claims(variants),
        "folds": fold_reports,
    }
    return document, provenance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.h2_frozen",
        description="H2 with the item difficulty frozen at test time (D60). Downloads nothing (D49).",
    )
    parser.add_argument("--data", default=None, help="Path to as.csv (default: the data root).")
    parser.add_argument("--quick", action="store_true", help=f"{h2.QUICK_LEARNERS} learners, for CI.")
    parser.add_argument("--quick-learners", type=int, default=h2.QUICK_LEARNERS)
    parser.add_argument("--original-only", action="store_true")
    parser.add_argument("--folds", type=int, default=splits.DEFAULT_FOLDS)
    parser.add_argument("--validation-fraction", type=float, default=splits.DEFAULT_VALIDATION_FRACTION)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument(
        "--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2)),
        help="Processes for the grid searches, used only when no checkpoint fits the run.",
    )
    parser.add_argument("--seed", type=int, default=splits.DEFAULT_SEED)
    parser.add_argument("--epochs", type=int, default=h2.FULL_EPOCHS,
                        help="DKT's epoch cap, as in H2 (--quick uses H2's quick cap).")
    parser.add_argument("--reference", required=True,
                        help="The H2 result this run must reproduce unfrozen (D58's checks apply).")
    parser.add_argument("--no-checkpoint", action="store_true",
                        help="Fit the parameters and train DKT instead of reading D55's checkpoint.")
    parser.add_argument("--out", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    given = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(given)

    print("h2_frozen (D60) — ASSISTments 2009")
    try:
        document, provenance = run(args, given)
    except DatasetMissing as missing:
        print(f"h2_frozen: {missing}", file=sys.stderr)
        return 2
    except (GateFailed, h2_bounds.ReproductionFailed) as refused:
        print(f"h2_frozen: {refused}. Nothing was written.", file=sys.stderr)
        return 5

    directory = (
        Path(args.out).expanduser() if args.out
        else results_dir("assist09-frozen-quick" if args.quick else "assist09-frozen")
    )
    written = tables.write(
        directory, document, provenance.env_txt(), renderer=tables.render_h2_frozen_report,
    )
    print(f"\nwritten to {directory}")
    for path in written.values():
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
