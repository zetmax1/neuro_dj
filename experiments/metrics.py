"""
experiments/metrics.py — AUC, RMSE and accuracy (stage 8, "Metrikalar").

Each is computed over all predictions and again over each learner's first
k ∈ {3, 5} answers. The early attempts are reported separately on purpose: by
the tenth answer on a topic the evidence has outweighed any prior, so an
average over the whole sequence hides the one place where a prerequisite-aware
prior could show an effect.

AUC is implemented here rather than taken from scikit-learn, for one reason:
the DeLong test in ``stats.py`` needs the mid-ranks of the scores, so the
ranking is computed once and both the AUC and the variance are derived from
it. Two implementations of the same ranking would be two things to keep in
agreement. The test checks this AUC against scikit-learn's.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Scores:
    """One model's predictions on one evaluation set."""
    auc: float | None
    rmse: float
    accuracy: float
    n: int
    positives: int

    def payload(self) -> dict:
        return {
            "auc": None if self.auc is None else round(self.auc, 6),
            "rmse": round(self.rmse, 6),
            "accuracy": round(self.accuracy, 6),
            "n": self.n,
            "positives": self.positives,
        }


def mid_ranks(values: Sequence[float]) -> list[float]:
    """
    Ranks 1..n with ties sharing their average rank.

    Shared by ``auc`` and by the DeLong variance, so there is exactly one
    definition of "how these scores are ordered".
    """
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        average = (position + end) / 2.0 + 1.0
        for index in range(position, end + 1):
            ranks[order[index]] = average
        position = end + 1
    return ranks


def auc(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    """
    The area under the ROC curve, by the rank-sum identity:

        AUC = (R₁ − n₁(n₁ + 1)/2) / (n₁ n₀)

    where R₁ is the sum of the mid-ranks of the positive scores. Ties
    contribute 0.5, which is what mid-ranks give for free.

    None when one class is absent: AUC is undefined there, and returning 0.5
    would report a result that was not measured.
    """
    if len(labels) != len(scores):
        raise ValueError(f"{len(labels)} labels against {len(scores)} scores")
    positives = sum(1 for label in labels if label)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    ranks = mid_ranks(scores)
    rank_sum = sum(rank for rank, label in zip(ranks, labels) if label)
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def rmse(labels: Sequence[int], scores: Sequence[float]) -> float:
    if not labels:
        return float("nan")
    total = sum((score - label) ** 2 for label, score in zip(labels, scores))
    return math.sqrt(total / len(labels))


def accuracy(labels: Sequence[int], scores: Sequence[float], *, threshold: float = 0.5) -> float:
    if not labels:
        return float("nan")
    correct = sum(1 for label, score in zip(labels, scores) if (score >= threshold) == bool(label))
    return correct / len(labels)


def score(labels: Sequence[int], scores: Sequence[float]) -> Scores:
    return Scores(
        auc=auc(labels, scores),
        rmse=rmse(labels, scores),
        accuracy=accuracy(labels, scores),
        n=len(labels),
        positives=sum(1 for label in labels if label),
    )


def by_first_k(
    labels: Sequence[int],
    scores: Sequence[float],
    learners: Sequence[str],
    *,
    ks: Sequence[int] = (3, 5),
) -> dict[str, dict]:
    """
    ``score`` over everything, and over each learner's first k answers.

    ``learners`` is parallel to the predictions and must already be in the
    order the answers were given, which is what the loader guarantees.
    """
    out = {"all": score(labels, scores).payload()}
    for k in ks:
        seen: dict[str, int] = {}
        picked = []
        for index, learner in enumerate(learners):
            count = seen.get(learner, 0)
            if count < k:
                seen[learner] = count + 1
                picked.append(index)
        out[f"first_{k}"] = score(
            [labels[index] for index in picked],
            [scores[index] for index in picked],
        ).payload()
    return out
