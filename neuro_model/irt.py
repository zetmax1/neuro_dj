"""
neuro_model/irt.py — bounded guess and slip (chapter II, 3.3).

The item parameters move P(G) and P(S) away from their base values without
ever leaving their admissible range:

- γ_G = ln(G0 / (G_MAX − G0)), γ_S = ln(S0 / (S_MAX − S0));
- P(G) = G_MAX · σ(γ_G + a_q(θ_s − b_q));
- P(S) = S_MAX · σ(γ_S − a_q(θ_s − b_q)).

Two consequences are relied on elsewhere:

- with a_q = 0 the logistic terms collapse and P(G) = G0, P(S) = S0 exactly,
  which is the classical-BKT branch of the ablation (``use_irt=False``);
- P(G) and P(S) never pass G_MAX and S_MAX — strictly below them over the
  working range of θ (clamped to ±THETA_CLAMP), and equal to them only where
  the logistic saturates in floating point — so the 2.5 assertion
  (P(G) + P(S) < 1) holds whenever G_MAX + S_MAX ≤ 1.

The base values must satisfy 0 < G0 < G_MAX and 0 < S0 < S_MAX; γ is not
defined at the bounds.

All functions are pure.
"""

from __future__ import annotations

import math

__all__ = ["sigma", "gamma", "guess", "slip"]


def sigma(z: float) -> float:
    """The logistic function, written so that large |z| cannot overflow."""
    if z >= 0.0:
        return 1.0 / (1.0 + math.exp(-z))
    exp_z = math.exp(z)
    return exp_z / (1.0 + exp_z)


def gamma(base: float, bound: float) -> float:
    """
    γ = ln(base / (bound − base)): the logit that reproduces ``base`` at a
    zero logistic argument, i.e. σ(γ) = base / bound.
    """
    if not 0.0 < base < bound:
        raise ValueError(f"a base value must satisfy 0 < {base} < {bound}.")
    return math.log(base / (bound - base))


def guess(*, g0: float, g_max: float, a_q: float, theta: float, b_q: float) -> float:
    """P(G) = G_MAX · σ(γ_G + a_q(θ_s − b_q)); an easier item guesses higher."""
    return g_max * sigma(gamma(g0, g_max) + a_q * (theta - b_q))


def slip(*, s0: float, s_max: float, a_q: float, theta: float, b_q: float) -> float:
    """P(S) = S_MAX · σ(γ_S − a_q(θ_s − b_q)); a harder item slips more."""
    return s_max * sigma(gamma(s0, s_max) - a_q * (theta - b_q))
