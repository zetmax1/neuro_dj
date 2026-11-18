"""
neuro_model/elo.py — the Elo update of ability and item difficulty (3.3).

- p = σ(θ_s − b_q);
- θ_s += K(n_s)(x − p);
- b_q −= K(n_q)(x − p);
- K(n) = ELO_ALPHA / (1 + ELO_BETA·n).

n_s and n_q are the answers counted so far for the learner (per course) and
for the item, so both step sizes shrink as evidence accumulates. The learner
and the item move by the same residual in opposite directions: a correct
answer raises θ and makes the item look easier.

θ is clamped to ±THETA_CLAMP. That bound is a numerical safeguard and not part
of chapter II, so it is recorded as a deviation in docs/THESIS_MAPPING.md (D6).

All functions are pure.
"""

from __future__ import annotations

from dataclasses import dataclass

from neuro_model.irt import sigma

__all__ = ["EloStep", "expected", "k_factor", "update"]


@dataclass(frozen=True)
class EloStep:
    """The prediction and the new (θ, b) pair."""
    p: float
    theta: float
    b: float


def expected(*, theta: float, b: float) -> float:
    """p = σ(θ_s − b_q): the Rasch probability of a correct answer."""
    return sigma(theta - b)


def k_factor(n: int, *, alpha: float, beta: float) -> float:
    """K(n) = ELO_ALPHA / (1 + ELO_BETA·n); n is the number of answers so far."""
    if n < 0:
        raise ValueError("the number of answers cannot be negative.")
    return alpha / (1.0 + beta * float(n))


def update(
    *,
    theta: float,
    b: float,
    is_correct: bool,
    k_student: float,
    k_question: float,
    theta_clamp: float,
) -> EloStep:
    """One Elo step. ``k_student`` and ``k_question`` come from ``k_factor``."""
    p = expected(theta=theta, b=b)
    residual = (1.0 if is_correct else 0.0) - p
    new_theta = theta + k_student * residual
    new_b = b - k_question * residual
    return EloStep(
        p=p,
        theta=min(theta_clamp, max(-theta_clamp, new_theta)),
        b=new_b,
    )
