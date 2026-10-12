"""
experiments/h1.py — H1: do the readiness rules of 3.4 hold (D61, D62)?

H1 is not about predicting an answer. It is about a **decision**: the platform
opens a topic w for a learner when R_s(w) = 1, and the question is whether that
decision is better than the two rules a course designer would otherwise write
down. So the unit here is not an answer but an *event*: the learner's first
attempt at w, with Pre(w) non-empty and at least one prerequisite already
practised (D62, decision 5). At that moment four rules are asked "is this
learner ready for w?":

1. **probabilistic** — r_s(w) = min P(L) over Pre(w) ≥ τ, chapter II's score;
2. **chapter II (M, δ)** — R_s(w) = 1, i.e. M = 1 for every prerequisite, with
   the hysteresis of width δ that 3.4 defines. This is the rule the prototype
   runs, and the only one δ touches, which is why the τ × δ sensitivity grid
   is computed on it;
3. **completeness** — every prerequisite has at least one answer;
4. **pass mark** — accuracy over the prerequisites' answers ≥ ``pass_mark``
   (0.60, the platform's default, D62 decision 7);

and one more that is the platform's own and not chapter II's:

5. **earned_proficiency** — Junyi's own mastery flag on every prerequisite
   (D61), which Khan Academy's algorithm set.

Each rule flags a share of the events (**coverage**) and is wrong on a share of
what it flagged (**error share**: the learner then fails w). Those two move
together — a rule that flags nobody is never wrong — so the comparison is made
at **equal coverage**: τ is searched on the validation part until the
probabilistic rule covers as much as the rule it is compared with, and the
error shares are then read on the test part (D62, decision 8). Nothing is
tuned on test.

P(L) comes from BKT+IRT (λ=0) — H2's main model — with the per-skill
parameters fitted on train + validation and the item difficulties warmed
there, and r_s(w), R_s(w) and M are ``neuro_model.readiness``: the same
functions the platform calls in ``assessments.services.readiness``, not a
reimplementation (D62, decision 4). A prerequisite the learner never answered
enters with P(L) = 0 and M = False, exactly as it does in the prototype.

    python -m experiments.h1 --quick
    python -m experiments.h1

The reading rule was written before the run (D61): H1 is **supported** when,
at equal coverage, the probabilistic rule's error share is below both the
completeness and the pass-mark rule and the 95 % interval of each difference
excludes zero; **not supported** when an interval excludes zero the other way;
**undetermined** otherwise.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from experiments import metrics, splits, tables
from experiments.datasets import DatasetMismatch, DatasetMissing, junyi
from experiments.models.classical import CONSTANTS, BKTFamily
from experiments.provenance import GitState, Provenance, Source, results_dir
from neuro_model import readiness

# Chapter II's hysteresis width. ``settings.THESIS_MODEL["DELTA"]`` is the
# single source of truth; the experiments do not import Django, so it is
# restated here and a test asserts the two still agree (as for CONSTANTS).
CHAPTER_TWO_DELTA = 0.10

# Stage 8's sensitivity grid. τ is also the quantity the equal-coverage search
# moves, so chapter II's value (0.95) is one point of the grid rather than the
# whole of it.
TAU_GRID: tuple[float, ...] = (0.70, 0.80, 0.90, 0.95)
DELTA_GRID: tuple[float, ...] = (0.05, 0.10, 0.15)

# The platform's default pass mark: Topic.pass_mark_percentage = 60 %.
PASS_MARK = 0.60

# "Failed w" is read over the learner's first k answers at w, the same early
# window H2 reports (stage 8). k = 3 is the main column.
FIRST_K: tuple[int, ...] = (3, 5)
MAIN_K = 3
# Below half correct in that window is a failure (D62, decision 6).
FAILURE_SHARE = 0.5

PROBABILISTIC = "probabilistic"
CHAPTER_TWO = "chapter_two"
COMPLETENESS = "completeness"
PASS_MARK_RULE = "pass_mark"
PROFICIENCY = "earned_proficiency"

# The label each rule carries into the table, and whether it is one of
# chapter II's or a comparison. The order is the table's order.
RULES: tuple[tuple[str, str, str], ...] = (
    (PROBABILISTIC, "ehtimoliy (r ≥ τ)", "II bob"),
    (CHAPTER_TWO, "II bob R (M, δ bilan)", "II bob"),
    (COMPLETENESS, "bajarilganlik", "taqqoslash"),
    (PASS_MARK_RULE, "o‘tish bali", "taqqoslash"),
    (PROFICIENCY, "earned_proficiency", "platforma"),
)
# The rules the reading rule of D61 compares the probabilistic one with.
COMPARED_WITH: tuple[str, ...] = (COMPLETENESS, PASS_MARK_RULE)

QUICK_LEARNERS = 200
FULL_LEARNERS = 2000

SUPPORTED = "qo‘llab-quvvatlandi"
NOT_SUPPORTED = "qo‘llab-quvvatlanmadi"
UNDETERMINED = "aniqlanmadi"


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@dataclass
class Event:
    """
    One decision point: learner, exercise, and the state of Pre(w) before the
    learner's first answer at w.

    ``prerequisite_mastery`` is kept rather than only r, because the
    equal-coverage search re-reads r at many τ. ``ready`` holds R_s(w) per
    (τ, δ): M carries hysteresis, so it cannot be recomputed from a snapshot
    afterwards and is tracked along the stream instead.
    """

    user_id: str
    skill: str
    fold: int
    prerequisites: int
    prerequisite_mastery: tuple[float, ...]
    answered_prerequisites: int
    prerequisite_accuracy: float | None
    proficient_prerequisites: int
    ready: dict[tuple[float, float], bool] = field(default_factory=dict)
    correct_after: tuple[int, ...] = ()

    @property
    def readiness_score(self) -> float:
        """r_s(w), through ``neuro_model.readiness`` (D62, decision 4)."""
        return readiness.readiness_score(self.prerequisite_mastery)

    def failed(self, k: int) -> bool | None:
        """
        Did the learner fail w in the first ``k`` answers? None with no answer.

        The event itself is the first of those answers, so there is always at
        least one; None is kept for the degenerate case rather than scored as
        a success.
        """
        window = self.correct_after[:k]
        if not window:
            return None
        return (sum(window) / len(window)) < FAILURE_SHARE

    def flags(self, *, tau: float, delta: float) -> dict[str, bool]:
        """What each rule says about this event."""
        accuracy = self.prerequisite_accuracy
        return {
            PROBABILISTIC: self.readiness_score >= tau,
            CHAPTER_TWO: self.ready.get((tau, delta), False),
            COMPLETENESS: self.answered_prerequisites == self.prerequisites,
            PASS_MARK_RULE: accuracy is not None and accuracy >= PASS_MARK,
            PROFICIENCY: self.proficient_prerequisites == self.prerequisites,
        }


def collect_events(
    rows,
    *,
    model: BKTFamily,
    graph: junyi.JunyiGraph,
    fold: int,
    taus: tuple[float, ...] = TAU_GRID,
    deltas: tuple[float, ...] = DELTA_GRID,
) -> list[Event]:
    """
    Stream the answers through the fitted model and take one event per
    (learner, exercise) first attempt (D62, decision 5).

    The state is read **before** the answer is applied, which is what
    ``BKTFamily.stream`` yields. M is updated for every (τ, δ) of the grid as
    the stream goes, because the hysteresis of 3.4 is path-dependent: the flag
    at one answer depends on the flag at the one before.
    """
    prerequisites = graph.prerequisites
    settings = [(tau, delta) for tau in sorted(set(taus)) for delta in sorted(set(deltas))]

    seen: set[tuple[str, str]] = set()
    answered: dict[tuple[str, str], int] = {}
    correct: dict[tuple[str, str], int] = {}
    proficient: set[tuple[str, str]] = set()
    mastered: dict[tuple[float, float], dict[tuple[str, str], bool]] = {
        setting: {} for setting in settings
    }
    after: dict[tuple[str, str], list[int]] = {}
    events: list[Event] = []

    for row, state, _observation, result in model.stream(rows):
        key = (row.user_id, row.skill_id)
        pre = prerequisites.get(row.skill_id, ())
        if key not in seen:
            seen.add(key)
            answered_pre = sum(1 for u in pre if answered.get((row.user_id, u), 0) > 0)
            if pre and answered_pre:
                attempts = sum(answered.get((row.user_id, u), 0) for u in pre)
                hits = sum(correct.get((row.user_id, u), 0) for u in pre)
                event = Event(
                    user_id=row.user_id,
                    skill=row.skill_id,
                    fold=fold,
                    prerequisites=len(pre),
                    # The platform's own reading: a prerequisite the learner
                    # never answered has P(L) = 0 and M = False
                    # (assessments.services.readiness.readiness_at).
                    prerequisite_mastery=tuple(
                        state.mastery.get((row.user_id, u), 0.0) for u in pre
                    ),
                    answered_prerequisites=answered_pre,
                    prerequisite_accuracy=(hits / attempts) if attempts else None,
                    proficient_prerequisites=sum(
                        1 for u in pre if (row.user_id, u) in proficient
                    ),
                    ready={
                        setting: readiness.is_ready(
                            mastered[setting].get((row.user_id, u), False) for u in pre
                        )
                        for setting in settings
                    },
                )
                events.append(event)
                after[key] = []

        # The answer itself: counters first, then M for every (τ, δ).
        answered[key] = answered.get(key, 0) + 1
        correct[key] = correct.get(key, 0) + int(row.correct)
        if row.earned_proficiency:
            proficient.add(key)
        if key in after:
            after[key].append(int(row.correct))
        for setting in settings:
            tau, delta = setting
            mastered[setting][key] = readiness.mastered_flag(
                p_mastery=result.p_after,
                tau=tau,
                delta=delta,
                previous=mastered[setting].get(key, False),
            )

    for event in events:
        event.correct_after = tuple(after[(event.user_id, event.skill)])
    return events


# ---------------------------------------------------------------------------
# Coverage and the equal-coverage search
# ---------------------------------------------------------------------------

def coverage(events: list[Event], rule: str, *, tau: float, delta: float) -> float:
    if not events:
        return 0.0
    return sum(1 for event in events if event.flags(tau=tau, delta=delta)[rule]) / len(events)


def tau_for_coverage(events: list[Event], target: float) -> float:
    """
    The τ whose probabilistic coverage is closest to ``target``.

    Coverage falls monotonically in τ, so the candidates are the r values
    themselves: between two of them nothing changes. Ties go to the **higher**
    τ, i.e. to the stricter rule, so the search cannot buy coverage by
    accident.
    """
    if not events:
        return CONSTANTS.tau
    candidates = sorted({event.readiness_score for event in events} | {0.0, 1.0})
    best, best_gap = candidates[-1], None
    for candidate in candidates:
        gap = abs(
            sum(1 for event in events if event.readiness_score >= candidate) / len(events)
            - target
        )
        if best_gap is None or gap < best_gap - 1e-12:
            best, best_gap = candidate, gap
    return round(best, 6)


def rule_scores(events: list[Event], flags: list[dict[str, bool]], rule: str, k: int) -> dict:
    """Coverage and error share of one rule over the pooled events."""
    flagged = [
        event for event, decision in zip(events, flags)
        if decision[rule] and event.failed(k) is not None
    ]
    failed = sum(1 for event in flagged if event.failed(k))
    scored = [event for event in events if event.failed(k) is not None]
    return {
        "events": len(scored),
        "flagged": len(flagged),
        "failed": failed,
        "coverage": round(len(flagged) / len(scored), 6) if scored else None,
        "error_share": round(failed / len(flagged), 6) if flagged else None,
    }


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def fold_events(fold, rows, graph, params, *, log=print) -> tuple[list[Event], list[Event], dict]:
    """
    One fold: fit the items on train + validation, then the events of the
    validation part (where τ is searched) and of the test part (where
    everything is measured).
    """
    sets = {
        "fitting": splits.subset(rows, fold.fitting),
        "validation": splits.subset(rows, fold.validation),
        "test": splits.subset(rows, fold.test),
    }
    model = BKTFamily("BKT+IRT (λ=0)", use_irt=True, use_prereq_init=False, params=params)
    info = model.fit(sets["fitting"])
    validation = collect_events(
        sets["validation"], model=model, graph=graph, fold=fold.index,
    )
    test = collect_events(sets["test"], model=model, graph=graph, fold=fold.index)
    log(f"    {len(test)} test event(s), {len(validation)} validation event(s)")
    return validation, test, {
        "index": fold.index,
        "counts": fold.counts() | {
            "test_answers": len(sets["test"]),
            "test_events": len(test),
            "validation_events": len(validation),
        },
        "items_warmed": info["items_warmed"],
        "parameters": info["parameters"],
    }


def equal_coverage(
    folds_events: list[tuple[list[Event], list[Event]]],
    *,
    delta: float,
    k: int,
    replicates: int,
    seed: int,
) -> tuple[list[dict], dict[str, float], list[Event], dict[str, list[dict[str, bool]]]]:
    """
    For each compared rule, the τ that matches its coverage on validation —
    per fold — and the pooled test events with the resulting flags.

    Returns the per-rule entries, the τ chosen per fold, the pooled test
    events and, per compared rule, the flags of every pooled event.
    """
    from experiments import stats

    entries: list[dict] = []
    taus: dict[str, list[float]] = {}
    pooled: list[Event] = [event for _, test in folds_events for event in test]
    flags: dict[str, list[dict[str, bool]]] = {}

    for rule in COMPARED_WITH:
        per_fold: list[float] = []
        rule_flags: list[dict[str, bool]] = []
        for validation, test in folds_events:
            target = coverage(validation, rule, tau=CONSTANTS.tau, delta=delta)
            tau = tau_for_coverage(validation, target)
            per_fold.append(tau)
            rule_flags.extend(event.flags(tau=tau, delta=delta) for event in test)
        taus[rule] = per_fold
        flags[rule] = rule_flags

        probabilistic = rule_scores(pooled, rule_flags, PROBABILISTIC, k)
        compared = rule_scores(pooled, rule_flags, rule, k)
        difference = stats.bootstrap_statistic(
            _error_share_difference(pooled, rule_flags, rule, k),
            [event.user_id for event in pooled],
            replicates=replicates,
            seed=seed,
        )
        entries.append({
            "rule": rule,
            "tau_per_fold": per_fold,
            "k": k,
            "probabilistic": probabilistic,
            "compared": compared,
            "coverage_gap": (
                None if probabilistic["coverage"] is None or compared["coverage"] is None
                else round(probabilistic["coverage"] - compared["coverage"], 6)
            ),
            "difference": difference.payload(),
        })
    return entries, {rule: values[0] for rule, values in taus.items()}, pooled, flags


def _error_share_difference(events: list[Event], flags: list[dict[str, bool]], rule: str, k: int):
    """
    The statistic the bootstrap resamples: error share of the probabilistic
    rule minus that of ``rule``, over the drawn events.

    Negative is H1's direction — chapter II's rule is wrong less often.
    """
    def statistic(indices) -> float | None:
        counts = {PROBABILISTIC: [0, 0], rule: [0, 0]}
        for index in indices:
            event, decision = events[index], flags[index]
            failed = event.failed(k)
            if failed is None:
                continue
            for name in counts:
                if decision[name]:
                    counts[name][0] += 1
                    counts[name][1] += int(failed)
        if not counts[PROBABILISTIC][0] or not counts[rule][0]:
            return None
        return (
            counts[PROBABILISTIC][1] / counts[PROBABILISTIC][0]
            - counts[rule][1] / counts[rule][0]
        )

    return statistic


def sensitivity(events: list[Event], *, k: int) -> list[dict]:
    """
    τ × δ for chapter II's rule and for the plain threshold on r.

    δ reaches only M, so the probabilistic column is constant down each δ and
    that is the point of showing them together: it says where the hysteresis
    changes the decision at all.
    """
    out: list[dict] = []
    for tau in TAU_GRID:
        for delta in DELTA_GRID:
            flags = [event.flags(tau=tau, delta=delta) for event in events]
            out.append({
                "tau": tau,
                "delta": delta,
                "chapter_two": rule_scores(events, flags, CHAPTER_TWO, k),
                "probabilistic": rule_scores(events, flags, PROBABILISTIC, k),
            })
    return out


def readiness_auc(events: list[Event], *, k: int, replicates: int, seed: int) -> dict:
    """
    AUC of r_s(w) for "the learner does not fail w" (D61).

    A rule's own AUC would be the AUC of a binary flag; this is the score
    behind the rule, which is what the hypothesis is about.
    """
    from experiments import stats

    scored = [event for event in events if event.failed(k) is not None]
    labels = [0 if event.failed(k) else 1 for event in scored]
    scores = [event.readiness_score for event in scored]
    learners = [event.user_id for event in scored]
    interval = stats.bootstrap_auc(
        labels, scores, learners, replicates=replicates, seed=seed, by_learner=True,
    )
    return {
        "score": "r_s(w)",
        "k": k,
        "events": len(scored),
        "failures": sum(1 for label in labels if label == 0),
        "auc": metrics.auc(labels, scores),
        "auc_interval": interval.payload(),
    }


def reading(entries: list[dict]) -> dict:
    """
    D61's reading rule, applied to the two compared rules.

    Supported: both differences are negative with an interval that excludes
    zero. Not supported: an interval excludes zero on the positive side.
    Otherwise undetermined — and in every case the two numbers are reported.
    """
    verdicts: list[dict] = []
    for entry in entries:
        payload = entry["difference"]
        low, high = payload.get("ci_low"), payload.get("ci_high")
        if low is None or high is None:
            verdict = UNDETERMINED
        elif high < 0.0:
            verdict = SUPPORTED
        elif low > 0.0:
            verdict = NOT_SUPPORTED
        else:
            verdict = UNDETERMINED
        verdicts.append({
            "rule": entry["rule"],
            "difference": payload.get("estimate"),
            "ci_low": low,
            "ci_high": high,
            "verdict": verdict,
        })
    if verdicts and all(item["verdict"] == SUPPORTED for item in verdicts):
        status = SUPPORTED
    elif any(item["verdict"] == NOT_SUPPORTED for item in verdicts):
        status = NOT_SUPPORTED
    else:
        status = UNDETERMINED
    return {
        "status": status,
        "rule": (
            "teng qamrovda ehtimoliy qoidaning xato ulushi bajarilganlik va o‘tish "
            "bali qoidalaridan past bo‘lsa va farqlarning 95 % CI si nolni kesib "
            "o‘tmasa — qo‘llab-quvvatlandi (D61)"
        ),
        "per_rule": verdicts,
    }


def run(args, argv: list[str], *, loaded=None) -> tuple[dict, Provenance]:
    git_start = GitState.capture()
    learners_wanted = args.learners or (QUICK_LEARNERS if args.quick else FULL_LEARNERS)
    if loaded is None:
        graph, log_data, found = junyi.load(
            directory=args.data or None,
            exercise_table=args.exercise_table,
            problem_log=args.problem_log,
            learners=learners_wanted,
            seed=args.seed,
            verify=not args.no_verify,
        )
    else:
        graph, log_data, found = loaded

    rows = list(log_data.rows)
    learners = list(log_data.learners)
    folds = splits.learner_folds(
        learners, folds=args.folds, validation_fraction=args.validation_fraction, seed=args.seed,
    )

    from experiments import h2, stats

    workers = max(1, min(args.workers, len(folds)))
    print(f"  fitting the BKT parameters of {len(folds)} folds on {workers} worker(s)")
    fitted = h2.fit_parameters(folds, rows, workers=workers)

    folds_events: list[tuple[list[Event], list[Event]]] = []
    fold_reports: list[dict] = []
    for fold in folds:
        print(f"  fold {fold.index + 1}/{len(folds)}: {fold.counts()}")
        validation, test, report = fold_events(
            fold, rows, graph, fitted[fold.index][0],
        )
        folds_events.append((validation, test))
        fold_reports.append(report)

    pooled = [event for _, test in folds_events for event in test]
    print(f"  pooled {len(pooled)} event(s) from {len({e.user_id for e in pooled})} learner(s)")

    equal: dict[str, list[dict]] = {}
    taus: dict[str, dict[str, float]] = {}
    for k in FIRST_K:
        entries, chosen, pooled, _flags = equal_coverage(
            folds_events, delta=CHAPTER_TWO_DELTA, k=k,
            replicates=args.replicates, seed=args.seed,
        )
        equal[str(k)] = entries
        taus[str(k)] = chosen

    rules_table = []
    main_flags = [
        event.flags(tau=CONSTANTS.tau, delta=CHAPTER_TWO_DELTA) for event in pooled
    ]
    for key, label, family in RULES:
        entry = rule_scores(pooled, main_flags, key, MAIN_K)
        rules_table.append({"rule": key, "label": label, "family": family} | entry)

    document = {
        "report": "h1",
        "spec": "D61",
        "quick": bool(args.quick),
        "thesis_result": not args.quick,
        "dataset": _dataset_entry(graph, log_data, found, learners, rows),
        "graph": graph.metadata(),
        "log": log_data.metadata(),
        "inventory": None if found is None else found.metadata(),
        "split": splits.metadata(
            folds, seed=args.seed, validation_fraction=args.validation_fraction,
        ),
        "constants": {
            "tau": CONSTANTS.tau,
            "delta": CHAPTER_TWO_DELTA,
            "pass_mark": PASS_MARK,
            "failure_share": FAILURE_SHARE,
            "main_k": MAIN_K,
            "first_k": list(FIRST_K),
            "tau_grid": list(TAU_GRID),
            "delta_grid": list(DELTA_GRID),
        },
        "events": {
            "total": len(pooled),
            "learners": len({event.user_id for event in pooled}),
            "skills": len({event.skill for event in pooled}),
            "with_every_prerequisite_answered": sum(
                1 for event in pooled
                if event.answered_prerequisites == event.prerequisites
            ),
            "mean_prerequisites": round(
                sum(event.prerequisites for event in pooled) / len(pooled), 4,
            ) if pooled else None,
        },
        "rules": rules_table,
        "equal_coverage": equal,
        "tau_chosen": taus,
        "sensitivity": sensitivity(pooled, k=MAIN_K),
        "readiness_auc": {
            str(k): readiness_auc(pooled, k=k, replicates=args.replicates, seed=args.seed)
            for k in FIRST_K
        },
        "reading": reading(equal[str(MAIN_K)]),
        "folds": fold_reports,
        "replicates": args.replicates,
        # In the metrics so the table can print it without a literal (D48).
        "confidence_percent": int(round(stats.CONFIDENCE * 100)),
        "parameter_fit_workers": workers,
    }

    provenance = Provenance.capture(
        sources=(
            Source.of("junyi-exercise-table", graph.path),
            Source.of("junyi-problem-log", log_data.path),
        ),
        seeds={"split": args.seed, "sample": args.seed, "bootstrap": args.seed},
        argv=["python", "-m", "experiments.h1", *argv],
        packages=h2._packages(),
        git_start=git_start,
    )
    document["provenance"] = provenance.payload()
    document["dataset"]["source"] = provenance.payload()["sources"][1]
    return document, provenance


def _dataset_entry(graph, log_data, found, learners, rows) -> dict:
    return {
        "status": "ok",
        "name": "junyi",
        "label": "Junyi Academy (2015)",
        "licence": junyi.LICENCE,
        "citation": junyi.CITATION,
        "learners_used": len(learners),
        "answers_used": len(rows),
        "skills_used": len({row.skill_id for row in rows}),
        "log_rows_scanned": log_data.scanned_rows,
        "log_rows_total": None if found is None else found.rows,
        "log_learners_total": None if found is None else found.learners,
    }


def build_parser(prog: str = "python -m experiments.h1") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="H1 on Junyi Academy (D61). Takes paths; downloads nothing (D49).",
    )
    parser.add_argument("--data", default=None, help="Directory holding the Junyi files.")
    parser.add_argument("--exercise-table", default=None)
    parser.add_argument("--problem-log", default=None)
    parser.add_argument("--quick", action="store_true",
                        help=f"{QUICK_LEARNERS} learners, for CI.")
    parser.add_argument("--learners", type=int, default=None,
                        help=f"Learners to sample (default {FULL_LEARNERS}, D61).")
    parser.add_argument("--no-verify", action="store_true",
                        help="Skip the D61 count checks (fixtures only).")
    parser.add_argument("--folds", type=int, default=splits.DEFAULT_FOLDS)
    parser.add_argument("--validation-fraction", type=float,
                        default=splits.DEFAULT_VALIDATION_FRACTION)
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument(
        "--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2)),
        help="Processes for the folds' BKT grid searches; the result does not depend on it.",
    )
    parser.add_argument("--seed", type=int, default=splits.DEFAULT_SEED)
    parser.add_argument("--out", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    given = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(given)

    print("h1 (D61) — Junyi Academy (2015): readiness rules")
    try:
        document, provenance = run(args, given)
    except DatasetMissing as missing:
        print(f"h1: {missing}", file=sys.stderr)
        return 2
    except DatasetMismatch as mismatch:
        print(f"h1: {mismatch}", file=sys.stderr)
        return 3

    directory = (
        Path(args.out).expanduser() if args.out
        else results_dir("junyi-h1-quick" if args.quick else "junyi-h1")
    )
    written = tables.write(
        directory, document, provenance.env_txt(), renderer=tables.render_h1_report,
    )
    print(f"\nwritten to {directory}")
    for path in written.values():
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
