"""
Independent oracle for the student model (group A).

Written from NEUROLEARN_REMEDIATION.md §3.3-3.4 — the chapter II formulas —
and not from ``neuro_model``: the point of V-A2 is that two independent
transcriptions of the same formulas agree. Where the specification is silent
and the prototype adds a numerical safeguard (the θ clamp), the safeguard is
reproduced here and named as such, so that the differential test compares
formulas rather than guard rails.

Every function takes plain floats and returns plain floats; nothing here
imports Django or the prototype.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

# ---------------------------------------------------------------------------
# §3.3 — coefficients, guess and slip
# ---------------------------------------------------------------------------


def sigma(z: float) -> float:
    """σ(z) = 1 / (1 + e^-z), written so that large |z| cannot overflow."""
    if z >= 0.0:
        return 1.0 / (1.0 + math.exp(-z))
    moved = math.exp(z)
    return moved / (1.0 + moved)


def gamma(base: float, bound: float) -> float:
    """γ = ln(base / (bound − base)); defined for 0 < base < bound."""
    if not 0.0 < base < bound:
        raise ValueError("base must lie strictly between 0 and bound")
    return math.log(base / (bound - base))


def guess(*, g0: float, g_max: float, a_q: float, theta: float, b_q: float) -> float:
    """P(G) = G_MAX · σ(γ_G + a_q(θ_s − b_q))."""
    return g_max * sigma(gamma(g0, g_max) + a_q * (theta - b_q))


def slip(*, s0: float, s_max: float, a_q: float, theta: float, b_q: float) -> float:
    """P(S) = S_MAX · σ(γ_S − a_q(θ_s − b_q))."""
    return s_max * sigma(gamma(s0, s_max) - a_q * (theta - b_q))


# ---------------------------------------------------------------------------
# §3.3 — prediction, Bayes update, learning transition
# ---------------------------------------------------------------------------


def predict(*, p_l: float, guess: float, slip: float) -> float:
    """p̂ = P(L)(1 − P(S)) + (1 − P(L))P(G)."""
    return p_l * (1.0 - slip) + (1.0 - p_l) * guess


def posterior(*, p_l: float, guess: float, slip: float, is_correct: bool) -> float:
    """P(L|1) = P(L)(1 − P(S)) / p̂ and P(L|0) = P(L)·P(S) / (1 − p̂)."""
    p_hat = predict(p_l=p_l, guess=guess, slip=slip)
    if is_correct:
        return p_l * (1.0 - slip) / p_hat
    return p_l * slip / (1.0 - p_hat)


def transition(*, post: float, pt: float) -> float:
    """P(L)′ = P(L|x) + (1 − P(L|x))·PT."""
    return post + (1.0 - post) * pt


# ---------------------------------------------------------------------------
# §3.3 — Elo
# ---------------------------------------------------------------------------


def elo_expected(*, theta: float, b: float) -> float:
    """p = σ(θ_s − b_q)."""
    return sigma(theta - b)


def k_factor(n: int, *, alpha: float, beta: float) -> float:
    """K(n) = ELO_ALPHA / (1 + ELO_BETA·n)."""
    return alpha / (1.0 + beta * n)


def elo_update(
    *,
    theta: float,
    b: float,
    is_correct: bool,
    k_student: float,
    k_question: float,
    theta_clamp: float | None = None,
) -> tuple[float, float]:
    """
    θ_s += K(n_s)(x − p) and b_q −= K(n_q)(x − p).

    ``theta_clamp`` is the prototype's numerical safeguard (|θ| ≤ THETA_CLAMP),
    not part of chapter II; pass None to see the unguarded formula.
    """
    p = elo_expected(theta=theta, b=b)
    x = 1.0 if is_correct else 0.0
    moved_theta = theta + k_student * (x - p)
    moved_b = b - k_question * (x - p)
    if theta_clamp is not None:
        moved_theta = min(theta_clamp, max(-theta_clamp, moved_theta))
    return moved_theta, moved_b


# ---------------------------------------------------------------------------
# §3.3 — P(L0) from the prerequisites
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Pre:
    """One element of Pre(w): its weight ω, the learner's P(L), and its own P0."""

    weight: float
    p_l: float | None
    p0: float

    @property
    def value(self) -> float:
        """The learner's P(L), or this prerequisite's P0 when never answered."""
        return self.p0 if self.p_l is None else self.p_l


def mean_prerequisite_mastery(prerequisites: Sequence[Pre]) -> float | None:
    """m̄_s(w), the ω-weighted mean over Pre(w); None when Pre(w) is empty."""
    if not prerequisites:
        return None
    weight = sum(p.weight for p in prerequisites)
    if weight <= 0.0:
        raise ValueError("ω must be positive")
    return sum(p.weight * p.value for p in prerequisites) / weight


def initial_mastery(
    *, p0: float, prerequisites: Sequence[Pre], lam: float, cap: float
) -> float:
    """P(L0)_{s,w} = min{(1 − λ)·P0(w) + λ·m̄_s(w), c}; P0(w) when Pre(w) is empty."""
    mean = mean_prerequisite_mastery(prerequisites)
    if mean is None:
        return p0
    return min((1.0 - lam) * p0 + lam * mean, cap)


# ---------------------------------------------------------------------------
# §3.4 — mastery flag, readiness, counters
# ---------------------------------------------------------------------------


def mastered_flag(*, p_mastery: float, tau: float, delta: float, previous: bool) -> bool:
    """M = 1 for P ≥ τ, M = 0 for P < τ − δ, otherwise M keeps its old value."""
    if p_mastery >= tau:
        return True
    if p_mastery < tau - delta:
        return False
    return previous


def is_ready(flags: Sequence[bool]) -> bool:
    """R_s(w) = 1 exactly when every u ∈ Pre(w) has M_s(u) = 1; empty Pre ⇒ 1."""
    return all(flags)


def readiness_score(prerequisite_mastery: Sequence[float]) -> float:
    """r_s(w) = min over Pre(w) of P(L); 1 when Pre(w) is empty."""
    return min(prerequisite_mastery) if prerequisite_mastery else 1.0


def missing_count(flags: Sequence[bool]) -> int:
    """How many direct prerequisites have M = 0."""
    return sum(1 for flag in flags if not flag)


# ---------------------------------------------------------------------------
# §3.3 — Algorithm 2.4, one answer end to end
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Step:
    """What one answer produces, in the order algorithm 2.4 fixes."""

    p_before: float
    p_hat: float
    posterior: float
    p_after: float
    guess: float
    slip: float
    theta_after: float
    b_after: float


def observe(
    *,
    p0: float,
    pt: float,
    g0: float,
    s0: float,
    g_max: float,
    s_max: float,
    a_q: float,
    elo_alpha: float,
    elo_beta: float,
    lam: float,
    cap: float,
    theta_clamp: float | None,
    is_correct: bool,
    p_l: float | None,
    theta: float,
    b_q: float,
    n_student: int = 0,
    n_question: int = 0,
    prerequisites: Sequence[Pre] = (),
    use_irt: bool = True,
    use_prereq_init: bool = True,
) -> Step:
    """
    Algorithm 2.4 in the order the specification fixes:

    1. first attempt ⇒ P(L) ← P(L0);
    2. P(G), P(S) from the OLD θ and b;
    3. p̂;
    4. Bayes update;
    5. PT transition;
    6. Elo moves θ and b.

    The ablation flags follow §3.3: ``use_irt=False`` sets a_q = 0 and leaves
    θ and b untouched, ``use_prereq_init=False`` sets λ = 0.
    """
    effective_a = a_q if use_irt else 0.0
    effective_lam = lam if use_prereq_init else 0.0

    if p_l is None:
        p_before = initial_mastery(
            p0=p0, prerequisites=prerequisites, lam=effective_lam, cap=cap
        )
    else:
        p_before = p_l

    g = guess(g0=g0, g_max=g_max, a_q=effective_a, theta=theta, b_q=b_q)
    s = slip(s0=s0, s_max=s_max, a_q=effective_a, theta=theta, b_q=b_q)
    p_hat = predict(p_l=p_before, guess=g, slip=s)
    post = posterior(p_l=p_before, guess=g, slip=s, is_correct=is_correct)
    p_after = transition(post=post, pt=pt)

    if use_irt:
        theta_after, b_after = elo_update(
            theta=theta,
            b=b_q,
            is_correct=is_correct,
            k_student=k_factor(n_student, alpha=elo_alpha, beta=elo_beta),
            k_question=k_factor(n_question, alpha=elo_alpha, beta=elo_beta),
            theta_clamp=theta_clamp,
        )
    else:
        theta_after, b_after = theta, b_q

    return Step(
        p_before=p_before,
        p_hat=p_hat,
        posterior=post,
        p_after=p_after,
        guess=g,
        slip=s,
        theta_after=theta_after,
        b_after=b_after,
    )
