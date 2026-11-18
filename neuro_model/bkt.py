"""
neuro_model/bkt.py — the Bayesian knowledge-tracing update (chapter II, 3.3).

One observation x ∈ {0, 1} on a topic whose mastery probability is P(L):

- p̂ = P(L)(1 − P(S)) + (1 − P(L))P(G)      — the prediction, recorded as it was;
- P(L|1) = P(L)(1 − P(S)) / p̂              — correct answer;
- P(L|0) = P(L)·P(S) / (1 − p̂)             — wrong answer;
- P(L)′ = P(L|x) + (1 − P(L|x))·PT          — the learning transition.

``transition`` and ``step`` take an optional ceiling ``p_max`` (default 1.0,
at which nothing changes); see ``transition`` and D72.

``step`` returns both the posterior (before the transition) and P(L)′, because
the 2.5 assertion is stated for the posterior: if P(G) + P(S) < 1 then
P(L|1) > P(L) and P(L|0) < P(L). After the PT transition P(L) can rise even on
a wrong answer — classical BKT behaviour, documented by a test rather than
corrected.

Both the posterior and P(L)′ are clamped to [0, 1] (D65a, a numerical
safeguard like θ's clamp, F6). Once P(L) has rounded to exactly 1.0, a wrong
answer gives P·S / (1 − fl(1 − S)) = 1 + O(1e-15); the transition already
mapped that back to 1.0, so the clamp changes no P(L)′ — checked bit for bit
over H2 (``experiments/clamp_count.py``).

All functions are pure.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["BKTStep", "predict", "posterior", "transition", "step"]

# Below this, p̂ (or 1 − p̂) is treated as degenerate and the prior is kept.
# With valid parameters (P(G) > 0, P(S) < 1) neither denominator can vanish.
_EPSILON = 1e-12


@dataclass(frozen=True)
class BKTStep:
    """One observation: the prediction, the posterior and P(L) after PT."""
    p_hat: float
    posterior: float
    p_after: float


def predict(*, p_l: float, guess: float, slip: float) -> float:
    """p̂ = P(L)(1 − P(S)) + (1 − P(L))P(G)."""
    return p_l * (1.0 - slip) + (1.0 - p_l) * guess


def posterior(*, p_l: float, guess: float, slip: float, is_correct: bool) -> float:
    """P(L | x) by Bayes' rule, before the learning transition, clamped to [0, 1]."""
    p_hat = predict(p_l=p_l, guess=guess, slip=slip)
    if is_correct:
        numerator, denominator = p_l * (1.0 - slip), p_hat
    else:
        numerator, denominator = p_l * slip, 1.0 - p_hat
    if denominator < _EPSILON:
        return p_l
    return min(1.0, max(0.0, numerator / denominator))


def transition(*, posterior: float, pt: float, p_max: float = 1.0) -> float:
    """
    P(L)′ = min(p_max, P(L|x) + (1 − P(L|x))·PT), clamped to [0, 1].

    ``p_max`` is a deployment policy, not part of chapter II: at the default
    1.0 the expression is the chapter's transition bit for bit. Below 1.0 it
    stops P(L) from saturating, so that a few wrong answers can still bring
    the topic back under τ − δ (D72). The posterior is **not** capped: the
    2.5 assertion is stated for it.
    """
    updated = posterior + (1.0 - posterior) * pt
    return min(1.0, max(0.0, min(p_max, updated)))


def step(
    *,
    p_l: float,
    guess: float,
    slip: float,
    pt: float,
    is_correct: bool,
    p_max: float = 1.0,
) -> BKTStep:
    """One full observation; ``p_hat`` is the value predicted before the update."""
    p_hat = predict(p_l=p_l, guess=guess, slip=slip)
    post = posterior(p_l=p_l, guess=guess, slip=slip, is_correct=is_correct)
    return BKTStep(
        p_hat=p_hat,
        posterior=post,
        p_after=transition(posterior=post, pt=pt, p_max=p_max),
    )
