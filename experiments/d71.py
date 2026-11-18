"""
experiments/d71.py — D71: post-hoc, descriptive analyses of H1 and H3 on Junyi.

    python -m experiments.d71 --quick
    python -m experiments.d71 --workers 5

**Post-hoc and descriptive.** D61/D62 fixed the reading rules of H1 and H3
before their results, and those verdicts stand; nothing here has a reading
rule or a verdict, and both result documents say so (``posthoc``,
``descriptive``). What the final verification found (K-1, K-2) is what these
two analyses describe:

- **H1** — r_s(w) = min P(L) with an unanswered prerequisite at P(L) = 0
  (D62-4) puts r = 0 on every event whose prerequisites are not all answered,
  so the equal-coverage search against the pass mark could only reach τ = 0.
  (i) On the subset S of events whose every prerequisite was answered before
  the event, each rule's coverage and error share, and the equal-coverage
  differences against the pass mark and ``earned_proficiency`` with a 95 %
  interval; (ii) on the full set, r_s(w)'s error–coverage curve over a τ grid,
  with the other rules as points in the same plane.
- **H3** — λ chose the lowest grid value (0.25) everywhere, so the original
  graph is run at fixed λ ∈ :data:`LAMBDAS` (λ = 0 is the graph-free model),
  first-k AUC with an interval on the test part.

**Same everything.** The data, the sample, the split and the parameter fit are
H1's and H3's (``h2.fit_parameters``'s tasks, ``DEFAULT_GRID``, chapter II's
constants); both parts share one fit, because H1 and H3 fit the same folds of
the same rows. A **reproduction gate** compares the run with the committed H1
and H3 before anything is written (:func:`gate`); a run that does not
reproduce them writes nothing.

**Interruptions.** Each fold's fit is checkpointed under
``experiments/.runs/checkpoints/d71-<digest>/`` with H2's own mechanism, so a
restarted run fits only the folds that were not finished (D71). A dirty tree
turns the checkpoint off (D54).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from experiments import h1, h2, h3, metrics, splits, tables
from experiments.datasets import DatasetMismatch, DatasetMissing, junyi
from experiments.models.classical import CONSTANTS
from experiments.provenance import GitState, Provenance, Source, results_dir

SPEC = "D71"
TAU_CURVE: tuple[float, ...] = (
    0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99,
)
LAMBDAS: tuple[float, ...] = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)
# The rules the probabilistic one is compared with on the subset. Completeness
# flags every event of the subset by definition, so its comparison is "all
# ready" against "all ready" and is reported as such, not computed.
SUBSET_COMPARED: tuple[str, ...] = (h1.PASS_MARK_RULE, h1.PROFICIENCY)
CURVE_POINTS: tuple[str, ...] = (h1.COMPLETENESS, h1.PASS_MARK_RULE, h1.PROFICIENCY)
QUICK_REPLICATES = 100
CHECKPOINTS = "experiments/.runs/checkpoints"

REFERENCE_H1 = "experiments/results/junyi-h1/20261019-102526"
REFERENCE_H3 = "experiments/results/junyi-h3/20261019-122423"
REFERENCE_H1_QUICK = "experiments/results/junyi-h1-quick/20261019-092712"
REFERENCE_H3_QUICK = "experiments/results/junyi-h3-quick/20261019-094724"

# The full run starts only on a quiet machine (D71, as D63c/D68a).
MIN_AVAILABLE_KB = 6 * 1024 * 1024
MAX_SWAP_USED_KB = 200 * 1024

POSTHOC = "post-hoc, tavsifiy — D61/D62 ning o‘qish qoidasi va hukmi o‘zgarmaydi"


class NotReproduced(RuntimeError):
    """The run does not reproduce the committed H1/H3 it is a post-hoc of."""


# ---------------------------------------------------------------------------
# Memory condition and the shared fit
# ---------------------------------------------------------------------------

def memory_condition(meminfo: str | None = None) -> dict:
    """MemAvailable and swap in use, and whether the full run may start."""
    text = meminfo if meminfo is not None else Path("/proc/meminfo").read_text(encoding="utf-8")
    values = {}
    for line in text.splitlines():
        name, _, rest = line.partition(":")
        if rest.strip():
            values[name] = int(rest.split()[0])
    available = values.get("MemAvailable", 0)
    swap_used = values.get("SwapTotal", 0) - values.get("SwapFree", 0)
    return {
        "mem_available_kb": available,
        "swap_used_kb": swap_used,
        "ok": available >= MIN_AVAILABLE_KB and swap_used < MAX_SWAP_USED_KB,
    }


def fit_checkpoint(root, key: dict, *, enabled: bool, log=print):
    """H2's checkpoint (``h2_bounds.Checkpoint``), in a ``d71-<digest>`` directory."""
    from experiments.h2_bounds import Checkpoint

    checkpoint = Checkpoint(root, key, enabled=enabled, log=log)
    checkpoint.directory = Path(root) / f"d71-{checkpoint.digest}"
    return checkpoint


def checkpoint_key(git_start: GitState, graph, log_data, args) -> dict:
    return {
        "spec": SPEC,
        "commit": git_start.commit,
        "exercise_sha256": graph.sha256,
        "log_sha256": log_data.sha256,
        "seed": args.seed,
        "learners": len(log_data.learners),
        "folds": args.folds,
        "validation_fraction": args.validation_fraction,
        "quick": bool(args.quick),
    }


def fit(folds, rows, *, workers: int, checkpoint, log=print) -> tuple[dict, int]:
    """
    ``h2.fit_parameters``'s tasks, with finished folds read back from the
    checkpoint. Returns the fits by fold and how many came from the checkpoint.
    """
    from experiments.h2_bounds import SETTINGS, fit_all

    main = next(setting for setting in SETTINGS if setting.main)
    fitted: dict[int, tuple] = {}
    tasks = []
    for fold in folds:
        stored = checkpoint.load_fit(0, fold.index)
        if stored is not None:
            fitted[fold.index] = stored
        else:
            tasks.append((0, main, fold.index, splits.subset(rows, fold.fitting)))
    resumed = len(fitted)
    if resumed:
        log(f"  {resumed} fold fit(s) read from {checkpoint.directory}")
    if tasks:
        log(f"  fitting the BKT parameters of {len(tasks)} fold(s) on "
            f"{max(1, min(workers, len(tasks)))} worker(s)")
        fits = fit_all(
            tasks, workers=max(1, min(workers, len(tasks))), log=log,
            on_fit=lambda s, f, params, meta, seconds: checkpoint.save_fit(s, f, params, meta, seconds),
        )
        fitted.update({fold_index: fit_ for (_, fold_index), fit_ in fits.items()})
    return fitted, resumed


# ---------------------------------------------------------------------------
# (a) H1
# ---------------------------------------------------------------------------

def complete(event: h1.Event) -> bool:
    """Every prerequisite answered at least once before the event."""
    return event.answered_prerequisites == event.prerequisites


def subset_rules(events: list[h1.Event], k: int) -> list[dict]:
    """Each rule's coverage and error share at chapter II's τ and δ."""
    flags = [event.flags(tau=CONSTANTS.tau, delta=h1.CHAPTER_TWO_DELTA) for event in events]
    return [
        {"rule": key, "label": label} | h1.rule_scores(events, flags, key, k)
        for key, label, _family in h1.RULES
    ]


def subset_equal_coverage(
    folds_events: list[tuple[list[h1.Event], list[h1.Event]]], *, k: int, replicates: int, seed: int,
) -> list[dict]:
    """
    H1's equal-coverage comparison (D62-8: τ on validation, measured on test),
    restricted to the subset S of both parts.
    """
    from experiments import stats

    folds_s = [([e for e in v if complete(e)], [e for e in t if complete(e)]) for v, t in folds_events]
    pooled = [event for _, test in folds_s for event in test]
    out = []
    for rule in SUBSET_COMPARED:
        per_fold, rule_flags = [], []
        for validation, test in folds_s:
            target = h1.coverage(validation, rule, tau=CONSTANTS.tau, delta=h1.CHAPTER_TWO_DELTA)
            tau = h1.tau_for_coverage(validation, target)
            per_fold.append(tau)
            rule_flags.extend(event.flags(tau=tau, delta=h1.CHAPTER_TWO_DELTA) for event in test)
        probabilistic = h1.rule_scores(pooled, rule_flags, h1.PROBABILISTIC, k)
        compared = h1.rule_scores(pooled, rule_flags, rule, k)
        difference = stats.bootstrap_statistic(
            h1._error_share_difference(pooled, rule_flags, rule, k),
            [event.user_id for event in pooled],
            replicates=replicates, seed=seed,
        )
        out.append({
            "rule": rule,
            "tau_per_fold": per_fold,
            "probabilistic": probabilistic,
            "compared": compared,
            "coverage_gap": (
                None if probabilistic["coverage"] is None or compared["coverage"] is None
                else round(probabilistic["coverage"] - compared["coverage"], 6)
            ),
            "difference": difference.payload(),
        })
    return out


def curve(events: list[h1.Event], k: int) -> dict:
    """r_s(w)'s error–coverage points over :data:`TAU_CURVE`, and the other rules' points."""
    points = []
    for tau in TAU_CURVE:
        flags = [event.flags(tau=tau, delta=h1.CHAPTER_TWO_DELTA) for event in events]
        points.append({"tau": tau} | h1.rule_scores(events, flags, h1.PROBABILISTIC, k))
    main_flags = [event.flags(tau=CONSTANTS.tau, delta=h1.CHAPTER_TWO_DELTA) for event in events]
    rules = [{"rule": rule} | h1.rule_scores(events, main_flags, rule, k) for rule in CURVE_POINTS]
    return {"k": k, "points": points, "rules": rules}


def h1_part(folds, rows, graph, fitted, *, replicates: int, seed: int, log=print) -> dict:
    folds_events, fold_reports = [], []
    for fold in folds:
        log(f"  H1 fold {fold.index + 1}/{len(folds)}")
        validation, test, report = h1.fold_events(fold, rows, graph, fitted[fold.index][0], log=log)
        folds_events.append((validation, test))
        fold_reports.append({"index": report["index"], "counts": report["counts"]})
    pooled = [event for _, test in folds_events for event in test]
    subset = [event for event in pooled if complete(event)]
    main_flags = [event.flags(tau=CONSTANTS.tau, delta=h1.CHAPTER_TWO_DELTA) for event in pooled]

    return {
        "events": {
            "total": len(pooled),
            "subset": len(subset),
            "subset_learners": len({event.user_id for event in subset}),
            "subset_share": round(len(subset) / len(pooled), 6) if pooled else None,
            "with_zero_readiness": sum(1 for event in pooled if event.readiness_score == 0.0),
        },
        "full_rules": [
            {"rule": key} | h1.rule_scores(pooled, main_flags, key, h1.MAIN_K)
            for key, _label, _family in h1.RULES
        ],
        "subset": {
            str(k): {
                "rules": subset_rules(subset, k),
                "equal_coverage": subset_equal_coverage(
                    folds_events, k=k, replicates=replicates, seed=seed,
                ),
                "readiness_auc": h1.readiness_auc(subset, k=k, replicates=replicates, seed=seed),
            }
            for k in h1.FIRST_K
        },
        "curve": {str(k): curve(pooled, k) for k in h1.FIRST_K},
        "folds": fold_reports,
    }


# ---------------------------------------------------------------------------
# (b) H3
# ---------------------------------------------------------------------------

def lambda_name(lam: float) -> str:
    return "grafsiz" if lam == 0.0 else f"λ={tables.fmt(lam)}"


def h3_part(folds, rows, graph, fitted, *, replicates: int, seed: int, log=print) -> dict:
    """The original graph at each fixed λ; λ = 0 is H3's graph-free arm."""
    from experiments import stats

    arm_list, _ = h3.arms(graph, seeds=0)
    by_name = {arm["name"]: arm for arm in arm_list}
    original, graph_free = by_name[h3.ORIGINAL], by_name[h3.NO_GRAPH]

    outputs = []
    for fold in folds:
        sets = h3.fold_sets(fold, rows)
        predictions = {}
        for lam in LAMBDAS:
            arm = graph_free if lam == 0.0 else original
            model = h3.model_for(arm, fitted[fold.index][0], lam=lam)
            model.fit(sets["fitting"])
            predictions[lambda_name(lam)] = model.predict(sets["test"])
        log(f"  H3 fold {fold.index + 1}/{len(folds)}: {len(LAMBDAS)} λ")
        outputs.append({
            "predictions": predictions,
            "labels": [int(row.correct) for row in sets["test"]],
            "learners": [row.user_id for row in sets["test"]],
            "keys": h3.skill_keys(sets["test"]),
        })
    pooled = h3.pool(outputs)

    out: dict = {"lambdas": list(LAMBDAS), "by_k": {}}
    for k in h3.FIRST_K:
        picked = h3.first_k_indices(pooled["keys"], k)
        labels = [pooled["labels"][index] for index in picked]
        learners = [pooled["learners"][index] for index in picked]
        rows_k = []
        for lam in LAMBDAS:
            name = lambda_name(lam)
            scores = [pooled["predictions"][name][index] for index in picked]
            rows_k.append({
                "lambda": lam,
                "arm": name,
                "scores": metrics.score(labels, scores).payload(),
                "scores_all": metrics.score(pooled["labels"], pooled["predictions"][name]).payload(),
                "auc_interval": stats.bootstrap_auc(
                    labels, scores, learners, replicates=replicates, seed=seed, by_learner=True,
                ).payload(),
            })
            log(f"  H3 k={k} {name}: AUC {rows_k[-1]['scores']['auc']}")
        out["by_k"][str(k)] = {"k": k, "answers": len(labels), "learners": len(set(learners)), "rows": rows_k}
    return out


# ---------------------------------------------------------------------------
# The reproduction gate (D71)
# ---------------------------------------------------------------------------

def gate(h1_doc: dict, h3_doc: dict, *, reference_h1: dict, reference_h3: dict) -> list[dict]:
    """
    The run against the committed H1/H3 it is a post-hoc of. Raises
    :class:`NotReproduced` on the first difference; returns what was compared.
    """
    checks: list[dict] = []

    def check(name: str, ours, theirs) -> None:
        checks.append({"check": name, "ours": ours, "reference": theirs, "equal": ours == theirs})
        if ours != theirs:
            raise NotReproduced(f"{name}: {ours!r} ≠ {theirs!r}")

    events = reference_h1["events"]
    check("h1 events", h1_doc["events"]["total"], events["total"])
    check("h1 subset (every prerequisite answered)", h1_doc["events"]["subset"],
          events["with_every_prerequisite_answered"])
    ours_rules = {r["rule"]: (r["flagged"], r["failed"]) for r in h1_doc["full_rules"]}
    for rule in reference_h1["rules"]:
        check(f"h1 rule {rule['rule']} (flagged, failed)", ours_rules[rule["rule"]],
              (rule["flagged"], rule["failed"]))

    # H3: an arm is comparable at the λ the reference ran it at in every fold.
    for name, reference_arm in ((h3.ORIGINAL, h3.ORIGINAL), ("grafsiz", h3.NO_GRAPH)):
        lambdas = {fold["arms"][reference_arm]["lambda"] for fold in reference_h3["folds"]}
        if len(lambdas) != 1 or next(iter(lambdas)) not in LAMBDAS:
            checks.append({"check": f"h3 {reference_arm}", "skipped": f"reference λ per fold {sorted(lambdas)}"})
            continue
        ours_name = lambda_name(next(iter(lambdas)))
        for k in h3.FIRST_K:
            ours = next(r for r in h3_doc["by_k"][str(k)]["rows"] if r["arm"] == ours_name)
            theirs = reference_h3["pooled"][str(k)]["arms"][reference_arm]["scores"]
            # metrics.json stores the AUC at six decimals: compare at that precision.
            check(f"h3 {reference_arm} at λ={next(iter(lambdas))}, first {k} AUC",
                  round(ours["scores"]["auc"], 6), theirs["auc"])
            check(f"h3 {reference_arm}, first {k} answers", ours["scores"]["n"], theirs["n"])
    return checks


def _load_reference(path: str) -> dict:
    return json.loads((Path(path) / "metrics.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def run(args, argv: list[str], *, loaded=None, references=None) -> tuple[dict, dict, Provenance]:
    git_start = GitState.capture()
    learners_wanted = args.learners or (h1.QUICK_LEARNERS if args.quick else h1.FULL_LEARNERS)
    if loaded is None:
        graph, log_data, found = junyi.load(
            directory=args.data or None, exercise_table=args.exercise_table,
            problem_log=args.problem_log, learners=learners_wanted, seed=args.seed,
            verify=not args.no_verify,
        )
    else:
        graph, log_data, found = loaded
    rows = list(log_data.rows)
    learners = list(log_data.learners)
    folds = splits.learner_folds(
        learners, folds=args.folds, validation_fraction=args.validation_fraction, seed=args.seed,
    )
    replicates = args.replicates or (QUICK_REPLICATES if args.quick else 1000)

    checkpoint = fit_checkpoint(
        args.checkpoint_dir, checkpoint_key(git_start, graph, log_data, args),
        enabled=bool(git_start.dirty is False and not args.no_checkpoint),
    )
    fitted, resumed = fit(folds, rows, workers=args.workers, checkpoint=checkpoint)

    h1_doc = h1_part(folds, rows, graph, fitted, replicates=replicates, seed=args.seed)
    h3_doc = h3_part(folds, rows, graph, fitted, replicates=replicates, seed=args.seed)

    if references is None and not args.no_gate:
        references = (
            _load_reference(args.reference_h1 or (REFERENCE_H1_QUICK if args.quick else REFERENCE_H1)),
            _load_reference(args.reference_h3 or (REFERENCE_H3_QUICK if args.quick else REFERENCE_H3)),
        )
    checks = [] if references is None else gate(
        h1_doc, h3_doc, reference_h1=references[0], reference_h3=references[1],
    )

    common = {
        "spec": SPEC,
        "posthoc": True,
        "descriptive": True,
        "status_note": POSTHOC,
        "quick": bool(args.quick),
        "thesis_result": not args.quick,
        "dataset": h1._dataset_entry(graph, log_data, found, learners, rows),
        "log": log_data.metadata(),
        "split": splits.metadata(folds, seed=args.seed, validation_fraction=args.validation_fraction),
        "replicates": replicates,
        "confidence_percent": 95,
        "checkpoint": checkpoint.payload() | {"resumed_folds": resumed},
        "reproduction_gate": checks,
        "parameter_fit_workers": args.workers,
    }
    h1_document = {"report": "h1_posthoc"} | common | {
        "constants": {
            "tau": CONSTANTS.tau, "delta": h1.CHAPTER_TWO_DELTA, "pass_mark": h1.PASS_MARK,
            "failure_share": h1.FAILURE_SHARE, "first_k": list(h1.FIRST_K),
            "main_k": h1.MAIN_K, "tau_curve": list(TAU_CURVE),
        },
        "labels": {key: label for key, label, _family in h1.RULES},
        "reference": args.reference_h1 or (REFERENCE_H1_QUICK if args.quick else REFERENCE_H1),
    } | h1_doc
    h3_document = {"report": "h3_lambda"} | common | {
        "first_k": list(h3.FIRST_K),
        "reference": args.reference_h3 or (REFERENCE_H3_QUICK if args.quick else REFERENCE_H3),
    } | h3_doc

    provenance = Provenance.capture(
        sources=(
            Source.of("junyi-exercise-table", graph.path),
            Source.of("junyi-problem-log", log_data.path),
        ),
        seeds={"split": args.seed, "sample": args.seed, "bootstrap": args.seed},
        argv=["python", "-m", "experiments.d71", *argv],
        packages=h2._packages(),
        git_start=git_start,
    )
    for document in (h1_document, h3_document):
        document["provenance"] = provenance.payload()
        document["dataset"]["source"] = provenance.payload()["sources"][1]
    return h1_document, h3_document, provenance


# ---------------------------------------------------------------------------
# Tables (D48: every number from metrics.json, through tables.fmt)
# ---------------------------------------------------------------------------

def _share(value) -> str:
    return "—" if value is None else tables.fmt(value)


def _ci(entry: dict) -> str:
    if entry.get("estimate") is None:
        return "—"
    low, high = entry.get("ci_low"), entry.get("ci_high")
    return f"{tables.fmt(entry['estimate'])} [{_share(low)}; {_share(high)}]"


def _banner(metrics_doc: dict) -> list[str]:
    lines = [f"> **{metrics_doc['status_note']}.** ({metrics_doc['spec']})"]
    if metrics_doc["quick"]:
        lines += ["", "> **`--quick` ishga tushirish — dissertatsiya natijasi emas.**"]
    return lines + [""]


def _source(metrics_doc: dict) -> list[str]:
    prov = metrics_doc["provenance"]
    lines = ["## Manba va takrorlanish", "", f"- buyruq: `{prov['command']}`",
             f"- commit: `{prov['code_commit']}`; asl natija: `{metrics_doc['reference']}`",
             f"- checkpoint: `{json.dumps(metrics_doc['checkpoint'], ensure_ascii=False)}`", ""]
    if metrics_doc["reproduction_gate"]:
        lines += ["| Darvoza | Bu run | Asl run | Teng |", "|---|---|---|---|"]
        for check in metrics_doc["reproduction_gate"]:
            if "skipped" in check:
                lines.append(f"| {check['check']} | — | {check['skipped']} | — |")
            else:
                lines.append(f"| {check['check']} | {_value(check['ours'])} | "
                             f"{_value(check['reference'])} | {tables.fmt(check['equal'])} |")
    return lines + [""]


def _value(value) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(tables.fmt(v) for v in value)
    return tables.fmt(value)


def render_h1_posthoc(m: dict) -> str:
    labels = m["labels"]
    events = m["events"]
    lines = ["# H1 — post-hoc, tavsifiy tahlil (D71)", ""] + _banner(m) + [
        "## 1. Qism-to‘plam S: barcha prerekvizitlari voqeadan oldin ishlangan voqealar", "",
        f"Voqealar: S = {tables.fmt(events['subset'])} / {tables.fmt(events['total'])} "
        f"(ulush {_share(events['subset_share'])}), talabalar {tables.fmt(events['subset_learners'])}; "
        f"r_s(w) = 0 bo‘lgan voqealar (to‘liq to‘plam): {tables.fmt(events['with_zero_readiness'])}.",
        "",
    ]
    for key, block in m["subset"].items():
        lines += [f"### k = {key}", "", "| Qoida | Voqea | Belgilangan | Xato | Qamrov | Xato ulushi |",
                  "|---|---|---|---|---|---|"]
        for rule in block["rules"]:
            lines.append(f"| {rule['label']} | {tables.fmt(rule['events'])} | {tables.fmt(rule['flagged'])} | "
                         f"{tables.fmt(rule['failed'])} | {_share(rule['coverage'])} | {_share(rule['error_share'])} |")
        lines += ["", f"Teng qamrov S da (τ validatsiyaning S qismida). Farq = ehtimoliy − qoida, "
                      f"{tables.fmt(m['confidence_percent'])} % CI (talaba bo‘yicha bootstrap, "
                      f"{tables.fmt(m['replicates'])} replika).", "",
                  "| Taqqoslash | τ (fold'lar) | Ehtimoliy qamrov | Qoida qamrovi | Ehtimoliy xato ulushi | "
                  "Qoida xato ulushi | Farq [CI] |", "|---|---|---|---|---|---|---|"]
        for entry in block["equal_coverage"]:
            lines.append(
                f"| {labels[entry['rule']]} | {', '.join(tables.fmt(t) for t in entry['tau_per_fold'])} | "
                f"{_share(entry['probabilistic']['coverage'])} | {_share(entry['compared']['coverage'])} | "
                f"{_share(entry['probabilistic']['error_share'])} | {_share(entry['compared']['error_share'])} | "
                f"{_ci(entry['difference'])} |")
        lines.append(f"| {labels['completeness']} | — | — | — | — | — | S da hamma voqeani belgilaydi: "
                     f"taqqoslash “hamma tayyor” bilan bir xil, hisoblanmadi |")
        auc = block["readiness_auc"]
        lines += ["", f"S da r_s(w) bo‘yicha AUC: {_ci(auc['auc_interval'])} "
                      f"({tables.fmt(auc['events'])} voqea, {tables.fmt(auc['failures'])} muvaffaqiyatsiz).", ""]
    lines += ["## 2. To‘liq to‘plam: r_s(w) bo‘yicha xato–qamrov egri chizig‘i", "",
              "Nuqtaviy (CI siz). Qatorlar — τ; oxirgi qatorlar — boshqa qoidalar nuqtalari.", ""]
    keys = list(m["curve"])
    header = "| τ / qoida | " + " | ".join(f"Qamrov (k = {k}) | Xato ulushi (k = {k})" for k in keys) + " |"
    lines += [header, "|---|" + "---|---|" * len(keys)]
    for index, tau in enumerate(m["constants"]["tau_curve"]):
        cells = []
        for k in keys:
            point = m["curve"][k]["points"][index]
            cells += [_share(point["coverage"]), _share(point["error_share"])]
        lines.append(f"| {tables.fmt(tau)} | " + " | ".join(cells) + " |")
    for index, rule in enumerate(m["curve"][keys[0]]["rules"]):
        cells = []
        for k in keys:
            point = m["curve"][k]["rules"][index]
            cells += [_share(point["coverage"]), _share(point["error_share"])]
        lines.append(f"| {labels[rule['rule']]} | " + " | ".join(cells) + " |")
    return "\n".join(lines + [""] + _source(m)) + "\n"


def render_h3_lambda(m: dict) -> str:
    lines = ["# H3 — λ egri chizig‘i, asl graf (D71)", ""] + _banner(m) + [
        f"λ qat’iy (validatsiyada tanlanmaydi); grafsiz — BKT+IRT (λ = 0). AUC — test qismi, "
        f"mavzudagi dastlabki k urinish; {tables.fmt(m['confidence_percent'])} % CI — talaba bo‘yicha "
        f"bootstrap, {tables.fmt(m['replicates'])} replika.", "",
        "| λ | " + " | ".join(f"AUC, k = {k} [CI]" for k in m["by_k"]) + " | Butun to‘plam AUC |",
        "|---|" + "---|" * len(m["by_k"]) + "---|",
    ]
    keys = list(m["by_k"])
    for index, lam in enumerate(m["lambdas"]):
        cells = [_ci(m["by_k"][k]["rows"][index]["auc_interval"]) for k in keys]
        all_auc = m["by_k"][keys[0]]["rows"][index]["scores_all"]["auc"]
        lines.append(f"| {m['by_k'][keys[0]]['rows'][index]['arm']} | " + " | ".join(cells) + f" | {_share(all_auc)} |")
    lines += ["", "Javoblar: " + "; ".join(
        f"k = {k}: {tables.fmt(block['answers'])} ({tables.fmt(block['learners'])} talaba)"
        for k, block in m["by_k"].items()) + ".", ""]
    return "\n".join(lines + _source(m)) + "\n"


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def build_parser(prog: str = "python -m experiments.d71") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description="D71: post-hoc H1 subset/curve and H3 λ curve.")
    parser.add_argument("--data", default=None)
    parser.add_argument("--exercise-table", default=None)
    parser.add_argument("--problem-log", default=None)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--learners", type=int, default=None)
    parser.add_argument("--no-verify", action="store_true")
    parser.add_argument("--folds", type=int, default=splits.DEFAULT_FOLDS)
    parser.add_argument("--validation-fraction", type=float, default=splits.DEFAULT_VALIDATION_FRACTION)
    parser.add_argument("--replicates", type=int, default=None)
    parser.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2)))
    parser.add_argument("--seed", type=int, default=splits.DEFAULT_SEED)
    parser.add_argument("--reference-h1", default=None)
    parser.add_argument("--reference-h3", default=None)
    parser.add_argument("--no-gate", action="store_true", help="Fixtures only: skip the reproduction gate.")
    parser.add_argument("--no-memory-gate", action="store_true", help="Fixtures only.")
    parser.add_argument("--checkpoint-dir", default=CHECKPOINTS)
    parser.add_argument("--no-checkpoint", action="store_true")
    parser.add_argument("--out", default=None, help="A root holding both result directories.")
    return parser


def main(argv: list[str] | None = None) -> int:
    given = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(given)
    print("d71 — post-hoc, descriptive: H1 subset and curve, H3 λ curve (Junyi)")

    if not args.quick and not args.no_memory_gate:
        condition = memory_condition()
        if not condition["ok"]:
            print(f"d71: not a quiet machine — MemAvailable {condition['mem_available_kb'] // 1024} MB, "
                  f"swap used {condition['swap_used_kb'] // 1024} MB (need ≥ 6144 and < 200)", file=sys.stderr)
            return 4
    try:
        h1_document, h3_document, provenance = run(args, given)
    except DatasetMissing as missing:
        print(f"d71: {missing}", file=sys.stderr)
        return 2
    except DatasetMismatch as mismatch:
        print(f"d71: {mismatch}", file=sys.stderr)
        return 3
    except NotReproduced as failed:
        print(f"d71: the run does not reproduce the committed H1/H3 — nothing written: {failed}", file=sys.stderr)
        return 5

    suffix = "-quick" if args.quick else ""
    root = Path(args.out).expanduser() if args.out else None
    stamp = None
    for name, document, renderer in (
        (f"junyi-h1-posthoc{suffix}", h1_document, render_h1_posthoc),
        (f"junyi-h3-lambda{suffix}", h3_document, render_h3_lambda),
    ):
        directory = results_dir(name, root=root, timestamp=stamp)
        stamp = directory.name
        tables.write(directory, document, provenance.env_txt(), renderer=renderer)
        print(f"written to {directory}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
