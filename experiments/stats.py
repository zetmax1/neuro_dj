"""
experiments/stats.py — confidence intervals and the comparison test (stage 8).

Three things, and the first two measure different quantities on purpose.

**Bootstrap over learners** (1000 replicates, 95% percentile interval) is what
the reported interval is. Answers are clustered inside a learner — one
learner's answers are a sequence, not 300 independent draws — so resampling
learners is the only resampling that reflects how the data were produced.

**Fast DeLong** (Sun & Xu, 2014) is the test for "is model A better than model
B on the same answers". It is a paired test and it is cheap, which matters
because the comparison is repeated for every pair of six models on every fold.
Its variance is the *unclustered* one: DeLong assumes independent
observations. So the two numbers are not interchangeable, and
``bootstrap_auc(by_learner=False)`` exists for exactly one reason — to check
DeLong against a bootstrap that estimates the same thing, which is what the
specification asks for.

**Holm** corrects the family of pairwise comparisons. With six models there
are fifteen pairs, and at α = 0.05 roughly one of them is expected to look
significant by chance.

numpy is required here. The 8b-1 modules are standard library only so that
they run in the Django environment; from this module onwards the pipeline
needs ``experiments/.venv`` (see experiments/README.md).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

try:
    import numpy as np
except ModuleNotFoundError as missing:  # pragma: no cover - environment guard
    raise ModuleNotFoundError(
        "experiments.stats needs numpy. Install the pipeline environment: "
        "python -m venv experiments/.venv && "
        "experiments/.venv/bin/pip install -r experiments/requirements.txt"
    ) from missing

DEFAULT_REPLICATES = 1000
DEFAULT_SEED = 20261006
CONFIDENCE = 0.95


@dataclass(frozen=True)
class Interval:
    """A point estimate with a percentile bootstrap interval."""
    estimate: float | None
    low: float | None
    high: float | None
    replicates: int
    by_learner: bool

    def payload(self) -> dict:
        return {
            "estimate": _round(self.estimate),
            "ci_low": _round(self.low),
            "ci_high": _round(self.high),
            "replicates": self.replicates,
            "clustered_by_learner": self.by_learner,
        }


@dataclass(frozen=True)
class Comparison:
    """One pairwise DeLong test, before and after the Holm correction."""
    a: str
    b: str
    auc_a: float
    auc_b: float
    difference: float
    z: float
    p: float
    p_holm: float | None = None
    significant: bool | None = None

    def payload(self) -> dict:
        return {
            "a": self.a,
            "b": self.b,
            "auc_a": _round(self.auc_a),
            "auc_b": _round(self.auc_b),
            "difference": _round(self.difference),
            "z": _round(self.z),
            "p": _round(self.p, 8),
            "p_holm": _round(self.p_holm, 8),
            "significant": self.significant,
        }


def _round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


# ---------------------------------------------------------------------------
# Mid-ranks and the structural components of the AUC
# ---------------------------------------------------------------------------

def midrank(values: np.ndarray) -> np.ndarray:
    """Ranks 1..n with ties sharing their average rank (vectorised)."""
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(len(values), dtype=float)
    index = 0
    position = 1.0
    while index < len(sorted_values):
        end = index
        while end + 1 < len(sorted_values) and sorted_values[end + 1] == sorted_values[index]:
            end += 1
        average = position + (end - index) / 2.0
        ranks[order[index:end + 1]] = average
        position += end - index + 1
        index = end + 1
    return ranks


def structural_components(
    labels: np.ndarray, scores: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    """
    (AUC, V_positives, V_negatives) of Sun & Xu (2014).

    ``V_positives[i]`` is the fraction of negatives that positive *i* beats
    (ties counting a half), and ``V_negatives[j]`` the fraction of positives
    that negative *j* loses to. The mean of either is the AUC, and their
    variances give its variance — which is what makes DeLong fast: no pairwise
    comparison is ever formed.
    """
    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    m, n = len(positives), len(negatives)
    if m == 0 or n == 0:
        raise ValueError("the AUC is undefined when one class is absent")

    tx = midrank(positives)
    ty = midrank(negatives)
    tz = midrank(np.concatenate([positives, negatives]))

    v_pos = (tz[:m] - tx) / n
    v_neg = 1.0 - (tz[m:] - ty) / m
    auc = float(v_pos.mean())
    return auc, v_pos, v_neg


def delong_variance(labels: Sequence[int], scores: Sequence[float]) -> tuple[float, float]:
    """(AUC, its variance) for one model, by fast DeLong."""
    auc, v_pos, v_neg = structural_components(
        np.asarray(labels, dtype=int), np.asarray(scores, dtype=float),
    )
    m, n = len(v_pos), len(v_neg)
    variance = v_pos.var(ddof=1) / m + v_neg.var(ddof=1) / n
    return auc, float(variance)


def delong_test(
    labels: Sequence[int],
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    *,
    name_a: str = "A",
    name_b: str = "B",
) -> Comparison:
    """
    The paired DeLong test on two models' predictions for the same answers.

    Paired is the point: both models saw the same test set, so the correlation
    between their AUCs has to be subtracted or the difference looks less
    certain than it is.
    """
    labels_array = np.asarray(labels, dtype=int)
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    if not (len(labels_array) == len(a) == len(b)):
        raise ValueError("the two models must be scored on the same answers")

    auc_a, v_pos_a, v_neg_a = structural_components(labels_array, a)
    auc_b, v_pos_b, v_neg_b = structural_components(labels_array, b)
    m, n = len(v_pos_a), len(v_neg_a)

    cov_pos = np.cov(np.vstack([v_pos_a, v_pos_b]), ddof=1)
    cov_neg = np.cov(np.vstack([v_neg_a, v_neg_b]), ddof=1)
    sigma = cov_pos / m + cov_neg / n
    variance = sigma[0, 0] + sigma[1, 1] - 2.0 * sigma[0, 1]

    difference = auc_a - auc_b
    if variance <= 0:
        # Identical predictions: the difference is exactly zero and there is
        # nothing to test. Reported as p = 1 rather than as a division by zero.
        return Comparison(name_a, name_b, auc_a, auc_b, difference, 0.0, 1.0)

    z = difference / float(np.sqrt(variance))
    return Comparison(name_a, name_b, auc_a, auc_b, difference, z, two_sided_p(z))


def two_sided_p(z: float) -> float:
    """Φ-based two-sided p value; scipy is not needed for one normal CDF."""
    from math import erfc, sqrt

    return float(erfc(abs(z) / sqrt(2.0)))


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def bootstrap_auc(
    labels: Sequence[int],
    scores: Sequence[float],
    learners: Sequence[str] | None = None,
    *,
    replicates: int = DEFAULT_REPLICATES,
    seed: int = DEFAULT_SEED,
    by_learner: bool = True,
    confidence: float = CONFIDENCE,
) -> Interval:
    """
    A percentile bootstrap interval for the AUC.

    ``by_learner`` resamples learners, which is the interval the results
    report: a learner's answers are one cluster, not independent draws. With
    ``by_learner=False`` observations are resampled instead, which estimates
    the same quantity as DeLong and exists to check it.

    A replicate in which one class is absent is dropped rather than scored as
    0.5, and the count of usable replicates is reported.
    """
    labels_array = np.asarray(labels, dtype=int)
    scores_array = np.asarray(scores, dtype=float)
    if len(labels_array) == 0 or labels_array.min() == labels_array.max():
        return Interval(None, None, None, 0, by_learner)

    point = _auc(labels_array, scores_array)
    rng = np.random.default_rng(seed)

    if by_learner:
        if learners is None:
            raise ValueError("by_learner=True needs the learner of each answer")
        groups = _group_indices(learners)
        draws = _bootstrap_clustered(labels_array, scores_array, groups, replicates, rng)
    else:
        draws = _bootstrap_flat(labels_array, scores_array, replicates, rng)

    if not draws:
        return Interval(point, None, None, 0, by_learner)
    alpha = (1.0 - confidence) / 2.0
    low, high = np.quantile(draws, [alpha, 1.0 - alpha])
    return Interval(point, float(low), float(high), len(draws), by_learner)


def _auc(labels: np.ndarray, scores: np.ndarray) -> float | None:
    positives = int((labels == 1).sum())
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    ranks = midrank(scores)
    rank_sum = float(ranks[labels == 1].sum())
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def _group_indices(learners: Sequence[str]) -> list[np.ndarray]:
    """Row indices per learner, in first-appearance order (deterministic)."""
    buckets: dict[str, list[int]] = {}
    for index, learner in enumerate(learners):
        buckets.setdefault(learner, []).append(index)
    return [np.asarray(rows, dtype=int) for rows in buckets.values()]


def _bootstrap_clustered(
    labels: np.ndarray,
    scores: np.ndarray,
    groups: list[np.ndarray],
    replicates: int,
    rng: np.random.Generator,
) -> list[float]:
    draws: list[float] = []
    count = len(groups)
    for _ in range(replicates):
        chosen = rng.integers(0, count, size=count)
        rows = np.concatenate([groups[index] for index in chosen])
        value = _auc(labels[rows], scores[rows])
        if value is not None:
            draws.append(value)
    return draws


def bootstrap_auc_difference(
    labels: Sequence[int],
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    learners: Sequence[str],
    *,
    replicates: int = DEFAULT_REPLICATES,
    seed: int = DEFAULT_SEED,
    confidence: float = CONFIDENCE,
) -> Interval:
    """
    AUC(a) − AUC(b) with a percentile interval, resampling **learners** and
    keeping the pair together (D55).

    DeLong's variance treats answers as independent, so its p value for a
    difference is optimistic on clustered data. This is the interval that
    respects the clustering: in each replicate the same learners are drawn for
    both models, so the correlation between them is kept, as in DeLong, and
    the learner is the unit, as in ``bootstrap_auc``.
    """
    labels_array = np.asarray(labels, dtype=int)
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    if not (len(labels_array) == len(a) == len(b) == len(learners)):
        raise ValueError("the two models must be scored on the same answers")
    if len(labels_array) == 0 or labels_array.min() == labels_array.max():
        return Interval(None, None, None, 0, True)

    point = _auc(labels_array, a) - _auc(labels_array, b)
    rng = np.random.default_rng(seed)
    groups = _group_indices(learners)
    draws: list[float] = []
    count = len(groups)
    for _ in range(replicates):
        chosen = rng.integers(0, count, size=count)
        rows = np.concatenate([groups[index] for index in chosen])
        left, right = _auc(labels_array[rows], a[rows]), _auc(labels_array[rows], b[rows])
        if left is not None and right is not None:
            draws.append(left - right)
    if not draws:
        return Interval(point, None, None, 0, True)
    alpha = (1.0 - confidence) / 2.0
    low, high = np.quantile(draws, [alpha, 1.0 - alpha])
    return Interval(point, float(low), float(high), len(draws), True)


def _bootstrap_flat(
    labels: np.ndarray,
    scores: np.ndarray,
    replicates: int,
    rng: np.random.Generator,
) -> list[float]:
    draws: list[float] = []
    size = len(labels)
    for _ in range(replicates):
        rows = rng.integers(0, size, size=size)
        value = _auc(labels[rows], scores[rows])
        if value is not None:
            draws.append(value)
    return draws


# ---------------------------------------------------------------------------
# Holm
# ---------------------------------------------------------------------------

def holm(comparisons: Sequence[Comparison], *, alpha: float = 0.05) -> list[Comparison]:
    """
    Holm's step-down correction over a family of comparisons.

    Sorted by p ascending, the i-th (0-based) is compared against
    α / (k − i); the adjusted p is the running maximum of (k − i)·p, so the
    sequence is monotone. Once one fails, every later one fails too.
    """
    if not comparisons:
        return []
    order = sorted(range(len(comparisons)), key=lambda index: comparisons[index].p)
    count = len(comparisons)
    adjusted: list[float] = []
    running = 0.0
    for position, index in enumerate(order):
        running = max(running, min(1.0, (count - position) * comparisons[index].p))
        adjusted.append(running)

    out = list(comparisons)
    for position, index in enumerate(order):
        out[index] = Comparison(
            **{
                **comparisons[index].__dict__,
                "p_holm": adjusted[position],
                "significant": adjusted[position] < alpha,
            }
        )
    return out
