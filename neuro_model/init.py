"""
neuro_model/init.py — the prior P(L0) of a topic (chapter II, 3.3).

The first attempt on a topic does not start from the topic's base value alone:
what the learner already knows about the prerequisites of w is evidence about
w itself.

- m̄_s(w) is the ω-weighted mean of P(L_{s,u}) over Pre(w), the immediate
  predecessors of w in G_L. Where the learner has no estimate for a
  prerequisite, that prerequisite's own P0 stands in for it.
- P(L0)_{s,w} = min{(1 − λ)·P0(w) + λ·m̄_s(w), τ − C_OFFSET}.
- Pre(w) = ∅ gives P(L0)_{s,w} = P0(w).

The cap keeps a prior strictly below the mastery threshold τ, so no topic can
be considered mastered before it has been answered even once. λ = 0 reduces
the whole expression to P0(w), which is the classical-BKT branch of the
ablation (``use_prereq_init=False``).

All functions are pure.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

__all__ = ["Prerequisite", "mean_prerequisite_mastery", "initial_mastery"]


@dataclass(frozen=True)
class Prerequisite:
    """
    One element of Pre(w).

    ``p_l`` is the learner's mastery probability for this prerequisite, or None
    when they have never answered it; ``p0`` is that prerequisite's own base
    value, which then stands in for it.
    """
    weight: float
    p_l: float | None
    p0: float

    @property
    def value(self) -> float:
        return self.p0 if self.p_l is None else self.p_l


def mean_prerequisite_mastery(prerequisites: Sequence[Prerequisite]) -> float | None:
    """m̄_s(w), the ω-weighted mean; None when Pre(w) is empty."""
    if not prerequisites:
        return None
    total_weight = sum(p.weight for p in prerequisites)
    if total_weight <= 0.0:
        raise ValueError("prerequisite weights must be positive (ω ∈ (0, 1]).")
    return sum(p.weight * p.value for p in prerequisites) / total_weight


def initial_mastery(
    *,
    p0: float,
    prerequisites: Sequence[Prerequisite],
    lam: float,
    cap: float,
) -> float:
    """
    P(L0)_{s,w}. ``cap`` is τ − C_OFFSET and applies only when Pre(w) is
    non-empty: a topic with no prerequisites keeps its base value as given.
    """
    mean = mean_prerequisite_mastery(prerequisites)
    if mean is None:
        return p0
    blended = (1.0 - lam) * p0 + lam * mean
    return min(blended, cap)
