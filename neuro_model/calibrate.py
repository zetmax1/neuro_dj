"""
neuro_model/calibrate.py — fitting P0, PT, G0, S0 from observed answers (D36).

The default method is a bounded grid search, written here rather than taken
from a library so that calibration has no hard external dependency. pyBKT's
EM stays available as an option in the management command; when it is not
installed the command falls back to this.

The likelihood is the plain BKT one. For a learner's sequence x_1..x_n on one
topic, starting from P(L) = P0:

    p̂_i = P(L_i)(1 − S) + (1 − P(L_i))G
    L   = Σ_i log p̂_i          if x_i = 1
          Σ_i log(1 − p̂_i)     if x_i = 0

and P(L) advances by the same Bayes step and PT transition the live model
uses, so the fitted parameters are the ones that explain the answers under
exactly the deployed update rule.

The search is bounded by G0 < G_MAX and S0 < S_MAX, the condition γ needs
(``neuro_model.irt.gamma``): without it a fitted "guess" could exceed the
ceiling the bounded guess/slip model is built on. It is also what keeps the
2.5 assertion true.

The grid is explicit and the candidates are visited in sorted order, so the
result is deterministic and ties resolve to the first (lowest) candidate.

All functions are pure.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import product

from neuro_model import bkt

__all__ = ["Candidate", "Grid", "log_likelihood", "grid_search", "DEFAULT_GRID"]

# Below this probability the log is clipped, so a single impossible answer
# cannot turn the whole likelihood into -inf.
_FLOOR = 1e-12

Sequences = Sequence[Sequence[bool]]


@dataclass(frozen=True)
class Candidate:
    """One parameter set and the log-likelihood it achieves."""
    p0: float
    pt: float
    g0: float
    s0: float
    log_likelihood: float


@dataclass(frozen=True)
class Grid:
    """The values each parameter is tried at; bounds are applied by the search."""
    p0: tuple[float, ...]
    pt: tuple[float, ...]
    g0: tuple[float, ...]
    s0: tuple[float, ...]

    def candidates(self, *, g_max: float, s_max: float) -> list[tuple[float, float, float, float]]:
        """Every admissible combination, in ascending order (deterministic)."""
        return sorted(
            product(
                sorted(v for v in self.p0 if 0.0 < v < 1.0),
                sorted(v for v in self.pt if 0.0 <= v <= 1.0),
                sorted(v for v in self.g0 if 0.0 < v < g_max),
                sorted(v for v in self.s0 if 0.0 < v < s_max),
            )
        )


# The grid has to span the admissible region, not a corner of it. P0 runs to
# 0.90 because a topic's prior is not capped by chapter II; the top G0 and S0
# sit just under G_MAX and S_MAX because on real data the likelihood keeps
# rising towards the bound. With the earlier ceilings (P0 0.50, G0 0.25,
# S0 0.09) every busy ASSISTments 2009 skill landed on that corner, 2–3.5 %
# of log-likelihood below the bounded L-BFGS-B optimum; this grid is within
# 0.7 % of it. γ stays moderate at the top: ln(0.29/0.01) ≈ 3.4,
# ln(0.097/0.003) ≈ 3.5.
DEFAULT_GRID = Grid(
    p0=(0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90),
    pt=(0.05, 0.10, 0.15, 0.20, 0.30, 0.40),
    g0=(0.05, 0.10, 0.15, 0.20, 0.25, 0.29),
    s0=(0.01, 0.03, 0.05, 0.07, 0.09, 0.097),
)


def log_likelihood(sequences: Sequences, *, p0: float, pt: float, g0: float, s0: float) -> float:
    """Total log-likelihood of the observed answers under these parameters."""
    total = 0.0
    for sequence in sequences:
        p_l = p0
        for is_correct in sequence:
            p_hat = bkt.predict(p_l=p_l, guess=g0, slip=s0)
            probability = p_hat if is_correct else 1.0 - p_hat
            total += math.log(max(probability, _FLOOR))
            p_l = bkt.step(
                p_l=p_l, guess=g0, slip=s0, pt=pt, is_correct=is_correct,
            ).p_after
    return total


def grid_search(
    sequences: Sequences,
    *,
    g_max: float,
    s_max: float,
    grid: Grid = DEFAULT_GRID,
) -> Candidate | None:
    """
    The admissible parameter set with the highest likelihood.

    Returns None when there is nothing to fit (no answers) or when the bounds
    admit no candidate at all; the caller then keeps the defaults.
    """
    observations = sum(len(sequence) for sequence in sequences)
    if observations == 0:
        return None

    best: Candidate | None = None
    for p0, pt, g0, s0 in grid.candidates(g_max=g_max, s_max=s_max):
        value = log_likelihood(sequences, p0=p0, pt=pt, g0=g0, s0=s0)
        if best is None or value > best.log_likelihood:
            best = Candidate(p0=p0, pt=pt, g0=g0, s0=s0, log_likelihood=value)
    return best


def count_observations(sequences: Iterable[Sequence[bool]]) -> int:
    """How many answers the sequences hold in total (the data-sufficiency test)."""
    return sum(len(sequence) for sequence in sequences)
