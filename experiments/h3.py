"""
experiments/h3.py — H3: does the prerequisite graph earn its place (D61, D62)?

BKT+IRT+Pre differs from BKT+IRT (λ=0) in one place: the prior of a learner's
**first** attempt at a topic, P(L0) = min{(1 − λ)·P0(w) + λ·m̄_s(w), τ − c},
where m̄ is the ω-weighted mean of P(L) over Pre(w). So if the graph carries
information, the model that reads it should predict the earliest attempts
better — and if it does not, the same model with a wrong graph should do just
as well. That is the experiment: one model, four graphs.

    asl        — the platform's knowledge map (833 topics, 976 edges, D61)
    teskari    — every edge reversed
    tasodifiy  — the degree sequence kept, the edges rewired at random,
                 20 seeds (``networkx.directed_edge_swap``, D62 decision 11)
    grafsiz    — λ = 0, which is BKT+IRT (λ=0) exactly

The reversed and the random arms are the null models that matter. A graph-aware
model can look better than a graph-blind one simply by having a smoother
prior — the reversed graph has the same density, the random ones the same
degree at every node, so a gain that survives them is a gain from the
*relations*, not from the shape.

λ is chosen on the **validation** part, per fold and per arm, from
{0.25, 0.50, 0.75} (chapter II's 0.5 is one of them, D62 decision 10). Per
arm, not once: a λ tuned on the real graph and imposed on the null arms would
hand the hypothesis the answer. The 19 further random seeds reuse the first
one's λ, because their graphs differ only in which edges were drawn.

The metric is AUC over the **first k attempts at a topic** (k ∈ {3, 5}), which
is where a prior can act at all; H2's per-learner first-k and the whole-set
AUC are reported beside it. Contrasts: asl − teskari, asl − tasodifiy (the 20
seeds' mean), asl − grafsiz, each with a learner-clustered bootstrap interval
(1 000 replicates), DeLong where it is defined, and Holm over the family.

    python -m experiments.h3 --quick
    python -m experiments.h3

The reading rule, written before the run (D61): H3 is **supported** when the
original graph beats all three and every interval excludes zero; **not
supported** when an interval excludes zero the other way; **undetermined**
otherwise. Whatever comes out is a statement about *this* graph — the
platform's own knowledge map, with its one merged cycle and its 11 % of
exercises without prerequisites (D61) — and not about prerequisite graphs in
general.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import sys
import time
from pathlib import Path

from experiments import metrics, splits, tables
from experiments.datasets import DatasetMismatch, DatasetMissing, junyi
from experiments.models.classical import CONSTANTS, BKTFamily
from experiments.provenance import GitState, Provenance, Source, results_dir

ORIGINAL = "asl"
REVERSED = "teskari"
RANDOM = "tasodifiy"
NO_GRAPH = "grafsiz"

LAMBDA_GRID: tuple[float, ...] = (0.25, 0.50, 0.75)
RANDOM_SEEDS = 20
# Swaps per edge for the rewiring; the mixing of a degree-preserving swap
# chain is judged by swaps per edge, not by swaps.
SWAPS_PER_EDGE = 10

FIRST_K: tuple[int, ...] = (3, 5)
MAIN_K = 3

SUPPORTED = "qo‘llab-quvvatlandi"
NOT_SUPPORTED = "qo‘llab-quvvatlanmadi"
UNDETERMINED = "aniqlanmadi"
NOT_COMPUTED = "hisoblanmadi"

QUICK_LEARNERS = 200
FULL_LEARNERS = 2000
QUICK_RANDOM_SEEDS = 3

# The three differences H3 is stated in, in the direction the hypothesis reads
# them: the real graph minus the arm it is compared with.
CONTRASTS: tuple[tuple[str, str], ...] = (
    (ORIGINAL, REVERSED),
    (ORIGINAL, RANDOM),
    (ORIGINAL, NO_GRAPH),
)


# ---------------------------------------------------------------------------
# The four graphs
# ---------------------------------------------------------------------------

def reverse(prerequisites: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    """Every edge the other way round."""
    out: dict[str, list[str]] = {skill: [] for skill in prerequisites}
    for skill, pre in prerequisites.items():
        for prerequisite in pre:
            out[prerequisite].append(skill)
    return {skill: tuple(sorted(values)) for skill, values in out.items()}


def randomise(
    prerequisites: dict[str, tuple[str, ...]], *, seed: int,
) -> tuple[dict[str, tuple[str, ...]], dict]:
    """
    Rewire the edges at random, keeping every node's in- and out-degree
    (``networkx.directed_edge_swap``).

    networkx is used here as a null-model generator, not as an oracle for a
    chapter II computation: nothing it returns is compared with this package's
    own graph code. It is already in ``requirements.lock``.
    """
    import networkx as nx

    graph = nx.DiGraph()
    graph.add_nodes_from(sorted(prerequisites))
    edges = [
        (prerequisite, skill)
        for skill, pre in prerequisites.items()
        for prerequisite in pre
    ]
    graph.add_edges_from(edges)

    # Each swap needs a three-edge pattern to rotate, so a sparse or layered
    # graph can refuse the full count. The request is halved until it is
    # accepted rather than the arm quietly becoming the original graph: an arm
    # called "random" that is the real graph would read as "no difference"
    # when it means "no randomisation".
    requested = SWAPS_PER_EDGE * len(edges)
    target = requested
    swapped = 0
    while target >= 1:
        candidate = graph.copy()
        try:
            nx.directed_edge_swap(candidate, nswap=target, max_tries=100 * target, seed=seed)
        except (nx.NetworkXError, nx.NetworkXException):
            target //= 2
            continue
        graph = candidate
        swapped = target
        break

    out: dict[str, list[str]] = {skill: [] for skill in prerequisites}
    for prerequisite, skill in graph.edges():
        out[skill].append(prerequisite)
    rewired = {skill: tuple(sorted(values)) for skill, values in out.items()}
    return rewired, {
        "seed": seed,
        "swaps_requested": requested,
        "swaps_made": swapped,
        "edges": sum(len(pre) for pre in rewired.values()),
        "degree_preserved": _degrees(prerequisites) == _degrees(rewired),
        "distinct_from_original": rewired != prerequisites,
    }


def _degrees(prerequisites: dict[str, tuple[str, ...]]) -> dict[str, tuple[int, int]]:
    """(in-degree, out-degree) per node, which the rewiring must not change."""
    out_degree: dict[str, int] = {skill: 0 for skill in prerequisites}
    for pre in prerequisites.values():
        for prerequisite in pre:
            out_degree[prerequisite] = out_degree.get(prerequisite, 0) + 1
    return {
        skill: (len(prerequisites[skill]), out_degree.get(skill, 0))
        for skill in prerequisites
    }


def arms(graph: junyi.JunyiGraph, *, seeds: int) -> tuple[list[dict], list[dict]]:
    """
    The arms of the experiment, in table order: original, reversed, the random
    ones, and the graph-free control. Returns ``(arms, skipped rewirings)``.

    Each entry carries the Pre(w) mapping the model is given and the metadata
    that says what it is; ``family`` is what the contrasts group on.
    """
    weight = graph.WEIGHT
    original = graph.prerequisites

    def weighted(prerequisites: dict[str, tuple[str, ...]]):
        return {
            skill: tuple((prerequisite, weight) for prerequisite in pre)
            for skill, pre in prerequisites.items()
        }

    out: list[dict] = [
        {
            "name": ORIGINAL,
            "family": ORIGINAL,
            "label": "asl graf (platformaning bilim xaritasi)",
            "graph": weighted(original),
            "edges": sum(len(pre) for pre in original.values()),
            "choose_lambda": True,
        },
        {
            "name": REVERSED,
            "family": REVERSED,
            "label": "teskari graf (barcha qirralar aylantirilgan)",
            "graph": weighted(reverse(original)),
            "edges": sum(len(pre) for pre in original.values()),
            "choose_lambda": True,
        },
    ]
    skipped: list[dict] = []
    for index in range(seeds):
        seed = splits.DEFAULT_SEED + index
        rewired, info = randomise(original, seed=seed)
        if not info["distinct_from_original"]:
            # Nothing was rewired, so this is not a null model. Recorded and
            # left out; the contrast then says "hisoblanmadi" rather than
            # reporting a difference of zero against the graph itself (D48).
            skipped.append(info)
            continue
        out.append({
            "name": f"{RANDOM}-{index + 1}",
            "family": RANDOM,
            "label": f"daraja saqlangan tasodifiy graf (seed {seed})",
            "graph": weighted(rewired),
            "edges": info["edges"],
            "rewiring": info,
            # Only the first random graph picks its own λ; the rest differ
            # only in which edges were drawn (D62, decision 10).
            "choose_lambda": index == 0,
        })
    out.append({
        "name": NO_GRAPH,
        "family": NO_GRAPH,
        "label": "grafsiz (λ = 0) — BKT+IRT (λ=0)",
        "graph": None,
        "edges": 0,
        "choose_lambda": False,
    })
    return out, skipped


# ---------------------------------------------------------------------------
# One arm on one fold
# ---------------------------------------------------------------------------

def model_for(arm: dict, params: dict, *, lam: float) -> BKTFamily:
    """BKT+IRT+Pre with this arm's graph and λ, or BKT+IRT (λ=0) without one."""
    if arm["graph"] is None:
        return BKTFamily(
            "BKT+IRT (λ=0)", use_irt=True, use_prereq_init=False, params=params,
        )
    return BKTFamily(
        "BKT+IRT+Pre",
        use_irt=True,
        use_prereq_init=True,
        params=params,
        constants=dataclasses.replace(CONSTANTS, lam=lam),
        graph=arm["graph"],
    )


def choose_lambda(
    arm: dict, params: dict, sets: dict[str, list], *, keys: list[str], k: int, log=print,
) -> dict:
    """
    λ on the validation part: fit on train, predict validation, keep the λ with
    the best first-k AUC. Never on test.
    """
    if not arm["choose_lambda"]:
        return {"lambda": None, "candidates": []}
    labels = [int(row.correct) for row in sets["validation"]]
    candidates: list[dict] = []
    for lam in LAMBDA_GRID:
        model = model_for(arm, params, lam=lam)
        model.fit(sets["train"])
        scores = model.predict(sets["validation"])
        measured = metrics.by_first_k(labels, scores, keys, ks=(k,))
        candidates.append({
            "lambda": lam,
            "auc": measured[f"first_{k}"]["auc"],
            "auc_all": measured["all"]["auc"],
        })
    best = max(candidates, key=lambda item: (item["auc"] is not None, item["auc"] or -1.0))
    log(f"      λ = {best['lambda']} chosen on validation "
        f"(first-{k} AUC {best['auc']})")
    return {"lambda": best["lambda"], "candidates": candidates}


def fold_sets(fold, rows) -> dict[str, list]:
    return {
        "train": splits.subset(rows, fold.train),
        "validation": splits.subset(rows, fold.validation),
        "test": splits.subset(rows, fold.test),
        "fitting": splits.subset(rows, fold.fitting),
    }


def skill_keys(rows) -> list[str]:
    """
    The key the first-k metric groups on: one learner's answers **at one
    topic**, which is where P(L0) acts (see the module docstring).
    """
    return [f"{row.user_id}|{row.skill_id}" for row in rows]


def run_fold(fold, rows, *, arm_list: list[dict], params: dict, log=print) -> tuple[dict, dict]:
    """Every arm on one fold. Returns (report, per-arm test predictions)."""
    sets = fold_sets(fold, rows)
    labels = [int(row.correct) for row in sets["test"]]
    learners = [row.user_id for row in sets["test"]]
    keys = skill_keys(sets["test"])
    validation_keys = skill_keys(sets["validation"])

    report: dict = {"index": fold.index, "counts": fold.counts() | {
        "test_answers": len(sets["test"]),
    }, "arms": {}}
    predictions: dict[str, list[float]] = {}
    lambdas: dict[str, float | None] = {}

    for arm in arm_list:
        started = time.perf_counter()
        chosen = choose_lambda(arm, params, sets, keys=validation_keys, k=MAIN_K, log=log)
        lam = chosen["lambda"]
        if lam is None and arm["graph"] is not None:
            # A random arm that reuses the first one's λ.
            lam = lambdas.get(f"{RANDOM}-1", CONSTANTS.lam)
        if arm["graph"] is None:
            lam = 0.0
        lambdas[arm["name"]] = lam

        model = model_for(arm, params, lam=lam)
        model.fit(sets["fitting"])
        scores = model.predict(sets["test"])
        if len(scores) != len(sets["test"]):
            raise RuntimeError(f"{arm['name']} returned {len(scores)} of {len(sets['test'])}")
        predictions[arm["name"]] = scores
        report["arms"][arm["name"]] = {
            "status": "ok",
            "lambda": lam,
            "lambda_choice": chosen,
            "edges": arm["edges"],
            "scores": metrics.by_first_k(labels, scores, keys, ks=FIRST_K),
            "scores_by_learner": metrics.by_first_k(labels, scores, learners, ks=FIRST_K),
            "seconds": round(time.perf_counter() - started, 1),
        }
        auc = report["arms"][arm["name"]]["scores"][f"first_{MAIN_K}"]["auc"]
        log(f"    {arm['name']:16s} first-{MAIN_K} auc="
            f"{'—' if auc is None else f'{auc:.4f}'} ({report['arms'][arm['name']]['seconds']:.0f}s)")

    return report, {
        "predictions": predictions,
        "labels": labels,
        "learners": learners,
        "keys": keys,
    }


def pool(outputs: list[dict]) -> dict:
    """The folds' test predictions, concatenated. Every learner is in one fold."""
    names = list(outputs[0]["predictions"]) if outputs else []
    pooled: dict[str, list[float]] = {name: [] for name in names}
    labels: list[int] = []
    learners: list[str] = []
    keys: list[str] = []
    for output in outputs:
        missing = [name for name in names if name not in output["predictions"]]
        if missing:
            raise RuntimeError(f"arms missing from a fold, cannot pool: {missing}")
        labels.extend(output["labels"])
        learners.extend(output["learners"])
        keys.extend(output["keys"])
        for name in names:
            pooled[name].extend(output["predictions"][name])
    return {"predictions": pooled, "labels": labels, "learners": learners, "keys": keys}


def first_k_indices(keys: list[str], k: int) -> list[int]:
    """Indices of each (learner, topic)'s first ``k`` answers, in order."""
    seen: dict[str, int] = {}
    picked: list[int] = []
    for index, key in enumerate(keys):
        count = seen.get(key, 0)
        if count < k:
            seen[key] = count + 1
            picked.append(index)
    return picked


# ---------------------------------------------------------------------------
# The pooled analysis
# ---------------------------------------------------------------------------

def analyse(pooled: dict, arm_list: list[dict], *, replicates: int, seed: int, k: int) -> dict:
    """
    Per-arm AUC with an interval, the random family's spread, and the three
    contrasts of :data:`CONTRASTS` with Holm over them.
    """
    from experiments import stats

    picked = first_k_indices(pooled["keys"], k)
    labels = [pooled["labels"][index] for index in picked]
    learners = [pooled["learners"][index] for index in picked]
    scores = {
        name: [values[index] for index in picked]
        for name, values in pooled["predictions"].items()
    }

    families: dict[str, list[str]] = {}
    for arm in arm_list:
        families.setdefault(arm["family"], []).append(arm["name"])

    out: dict = {
        "k": k,
        "answers": len(labels),
        "learners": len(set(learners)),
        "replicates": replicates,
        "confidence_percent": int(round(stats.CONFIDENCE * 100)),
        "arms": {},
        "families": {},
    }
    for arm in arm_list:
        name = arm["name"]
        entry = {
            "family": arm["family"],
            "label": arm["label"],
            "edges": arm["edges"],
            "scores": metrics.score(labels, scores[name]).payload(),
            "scores_all": metrics.score(pooled["labels"], pooled["predictions"][name]).payload(),
        }
        # The 20 random graphs get point estimates only: 20 clustered
        # bootstraps would multiply the run time for a spread that min /
        # median / max already describes (D61).
        if arm["family"] != RANDOM or name == f"{RANDOM}-1":
            entry["auc_interval"] = stats.bootstrap_auc(
                labels, scores[name], learners,
                replicates=replicates, seed=seed, by_learner=True,
            ).payload()
        out["arms"][name] = entry

    for family, names in families.items():
        values = [
            out["arms"][name]["scores"]["auc"] for name in names
            if out["arms"][name]["scores"]["auc"] is not None
        ]
        ordered = sorted(values)
        out["families"][family] = {
            "arms": len(names),
            "auc_min": ordered[0] if ordered else None,
            "auc_median": ordered[len(ordered) // 2] if ordered else None,
            "auc_max": ordered[-1] if ordered else None,
            "auc_mean": round(sum(ordered) / len(ordered), 6) if ordered else None,
        }

    out["contrasts"] = contrasts(
        out, scores, labels, learners, families, replicates=replicates, seed=seed,
    )
    out["reading"] = reading(out["contrasts"])
    return out


def contrasts(
    analysis: dict,
    scores: dict[str, list[float]],
    labels: list[int],
    learners: list[str],
    families: dict[str, list[str]],
    *,
    replicates: int,
    seed: int,
) -> list[dict]:
    """
    AUC(asl) − AUC(arm) for the three comparisons, clustered by learner.

    For the random family the statistic is the **mean over its seeds**, so one
    replicate scores the real graph against the average null graph; DeLong
    cannot express that mean, so it is reported against the family's median
    arm and labelled as such.
    """
    from experiments import stats

    out: list[dict] = []
    comparisons: list[stats.Comparison] = []
    for left, right in CONTRASTS:
        entry: dict = {"a": left, "b": right}
        left_names, right_names = families.get(left, []), families.get(right, [])
        if not left_names or not right_names:
            entry |= {"status": "unavailable", "reason": f"{right} arm did not run"}
            out.append(entry)
            continue

        interval = stats.bootstrap_statistic(
            _mean_auc_difference(labels, scores, left_names, right_names),
            learners, replicates=replicates, seed=seed,
        )
        # The arm DeLong is run against: the family's median AUC.
        ranked = sorted(
            right_names,
            key=lambda name: analysis["arms"][name]["scores"]["auc"] or 0.0,
        )
        median_arm = ranked[len(ranked) // 2]
        comparison = stats.delong_test(
            labels, scores[left_names[0]], scores[median_arm],
            name_a=left, name_b=median_arm,
        )
        comparisons.append(comparison)
        entry |= {
            "status": "ok",
            "arms_in_b": len(right_names),
            "delong_against": median_arm,
            "difference": interval.payload()["estimate"],
            "ci_low": interval.payload()["ci_low"],
            "ci_high": interval.payload()["ci_high"],
            "replicates": interval.replicates,
            "clustered_by_learner": True,
        }
        out.append(entry)

    corrected = stats.holm(comparisons)
    for entry in out:
        if entry.get("status") != "ok":
            continue
        match = next(
            (item for item in corrected
             if item.a == entry["a"] and item.b == entry["delong_against"]), None,
        )
        entry["delong_p"] = None if match is None else match.payload()["p"]
        entry["p_holm"] = None if match is None else match.payload()["p_holm"]
    return out


def _mean_auc_difference(labels, scores, left_names, right_names):
    """AUC of the left arm minus the mean AUC of the right family's arms."""
    import numpy as np

    label_array = np.asarray(labels, dtype=int)
    arrays = {name: np.asarray(values, dtype=float) for name, values in scores.items()}

    def statistic(indices):
        from experiments.stats import _auc

        drawn_labels = label_array[indices]
        left = _auc(drawn_labels, arrays[left_names[0]][indices])
        if left is None:
            return None
        values = [_auc(drawn_labels, arrays[name][indices]) for name in right_names]
        values = [value for value in values if value is not None]
        if not values:
            return None
        return left - sum(values) / len(values)

    return statistic


def reading(entries: list[dict]) -> dict:
    """D61's reading rule for H3, over the three contrasts."""
    verdicts = []
    for entry in entries:
        if entry.get("status") != "ok":
            verdict = NOT_COMPUTED
        elif entry.get("ci_low") is None or entry.get("ci_high") is None:
            verdict = UNDETERMINED
        elif entry["ci_low"] > 0.0:
            verdict = SUPPORTED
        elif entry["ci_high"] < 0.0:
            verdict = NOT_SUPPORTED
        else:
            verdict = UNDETERMINED
        verdicts.append({
            "b": entry["b"],
            "difference": entry.get("difference"),
            "ci_low": entry.get("ci_low"),
            "ci_high": entry.get("ci_high"),
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
            "asl graf uchtasidan ham yuqori va har uch farqning 95 % CI si nolni "
            "kesib o‘tmasa — qo‘llab-quvvatlandi (D61)"
        ),
        "scope": (
            "natija shu graf uchun o‘qiladi — platformaning 2015-yil yanvardagi "
            "bilim xaritasi, bitta birlashtirilgan sikl va prerekvizitsiz "
            "mashqlar bilan (D61)"
        ),
        "per_contrast": verdicts,
    }


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def run(args, argv: list[str], *, loaded=None) -> tuple[dict, Provenance]:
    git_start = GitState.capture()
    learners_wanted = args.learners or (QUICK_LEARNERS if args.quick else FULL_LEARNERS)
    seeds = args.random_graphs or (QUICK_RANDOM_SEEDS if args.quick else RANDOM_SEEDS)
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
    arm_list, skipped = arms(graph, seeds=seeds)
    print(f"  {len(arm_list)} arm(s): {', '.join(arm['name'] for arm in arm_list[:3])}, …")
    if skipped:
        print(f"  {len(skipped)} rewiring(s) left no edge moved; those arms do not run")

    from experiments import h2

    workers = max(1, min(args.workers, len(folds)))
    print(f"  fitting the BKT parameters of {len(folds)} folds on {workers} worker(s)")
    fitted = h2.fit_parameters(folds, rows, workers=workers)

    fold_reports: list[dict] = []
    outputs: list[dict] = []
    for fold in folds:
        print(f"  fold {fold.index + 1}/{len(folds)}: {fold.counts()}")
        report, output = run_fold(
            fold, rows, arm_list=arm_list, params=fitted[fold.index][0],
        )
        fold_reports.append(report)
        outputs.append(output)

    pooled = pool(outputs)
    print(f"  pooled {len(pooled['labels'])} answers from {len(set(pooled['learners']))} learners")
    analysis = {
        str(k): analyse(pooled, arm_list, replicates=args.replicates, seed=args.seed, k=k)
        for k in FIRST_K
    }

    document = {
        "report": "h3",
        "spec": "D61",
        "quick": bool(args.quick),
        "thesis_result": not args.quick,
        "dataset": {
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
        },
        "graph": graph.metadata(),
        "log": log_data.metadata(),
        "inventory": None if found is None else found.metadata(),
        "split": splits.metadata(
            folds, seed=args.seed, validation_fraction=args.validation_fraction,
        ),
        "constants": {
            "lambda_grid": list(LAMBDA_GRID),
            "lambda_chapter_two": CONSTANTS.lam,
            "random_seeds": seeds,
            "random_graphs_used": sum(
                1 for arm in arm_list if arm["family"] == RANDOM
            ),
            "random_graphs_skipped": skipped,
            "swaps_per_edge": SWAPS_PER_EDGE,
            "first_k": list(FIRST_K),
            "main_k": MAIN_K,
        },
        "arms": [
            {
                "name": arm["name"],
                "family": arm["family"],
                "label": arm["label"],
                "edges": arm["edges"],
                "rewiring": arm.get("rewiring"),
            }
            for arm in arm_list
        ],
        "pooled": analysis,
        "main_k": str(MAIN_K),
        "folds": fold_reports,
        "replicates": args.replicates,
        "parameter_fit_workers": workers,
    }

    provenance = Provenance.capture(
        sources=(
            Source.of("junyi-exercise-table", graph.path),
            Source.of("junyi-problem-log", log_data.path),
        ),
        seeds={"split": args.seed, "sample": args.seed, "bootstrap": args.seed,
               "graphs": args.seed},
        argv=["python", "-m", "experiments.h3", *argv],
        packages=h2._packages(),
        git_start=git_start,
    )
    document["provenance"] = provenance.payload()
    document["dataset"]["source"] = provenance.payload()["sources"][1]
    return document, provenance


def build_parser(prog: str = "python -m experiments.h3") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="H3 on Junyi Academy (D61). Takes paths; downloads nothing (D49).",
    )
    parser.add_argument("--data", default=None, help="Directory holding the Junyi files.")
    parser.add_argument("--exercise-table", default=None)
    parser.add_argument("--problem-log", default=None)
    parser.add_argument("--quick", action="store_true",
                        help=f"{QUICK_LEARNERS} learners and {QUICK_RANDOM_SEEDS} random graphs.")
    parser.add_argument("--learners", type=int, default=None)
    parser.add_argument("--random-graphs", type=int, default=None,
                        help=f"Degree-preserving random graphs (default {RANDOM_SEEDS}, D61).")
    parser.add_argument("--no-verify", action="store_true",
                        help="Skip the D61 count checks (fixtures only).")
    parser.add_argument("--folds", type=int, default=splits.DEFAULT_FOLDS)
    parser.add_argument("--validation-fraction", type=float,
                        default=splits.DEFAULT_VALIDATION_FRACTION)
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument(
        "--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2)),
    )
    parser.add_argument("--seed", type=int, default=splits.DEFAULT_SEED)
    parser.add_argument("--out", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    given = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(given)

    print("h3 (D61) — Junyi Academy (2015): graph controls")
    try:
        document, provenance = run(args, given)
    except DatasetMissing as missing:
        print(f"h3: {missing}", file=sys.stderr)
        return 2
    except DatasetMismatch as mismatch:
        print(f"h3: {mismatch}", file=sys.stderr)
        return 3

    directory = (
        Path(args.out).expanduser() if args.out
        else results_dir("junyi-h3-quick" if args.quick else "junyi-h3")
    )
    written = tables.write(
        directory, document, provenance.env_txt(), renderer=tables.render_h3_report,
    )
    print(f"\nwritten to {directory}")
    for path in written.values():
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
