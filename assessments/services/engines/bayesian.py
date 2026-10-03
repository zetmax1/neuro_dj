"""
assessments/services/engines/bayesian.py — Bayesian Knowledge Tracing Engine.

Production implementation of the BKT algorithm using a Hidden Markov Model
with four canonical parameters. This class satisfies the ``BaseStudentModel``
interface and can be activated via ``STUDENT_MODEL_ENGINE = "bkt"`` in
Django settings.

Bayesian Knowledge Tracing (BKT) models student mastery as a latent binary
variable (learned / not-learned) and updates the posterior probability of
mastery after each observed interaction using Bayes' rule.

Model Parameters:
    - P(L₀)  : Prior probability the student already knows the skill
                before any practice (baseline = 0.15).
    - P(T)   : Probability the student transitions from not-learned to
                learned after a single opportunity (learning rate = 0.20).
    - P(G)   : Probability of a correct response despite NOT knowing the
                skill (guessing = 0.25).
    - P(S)   : Probability of an incorrect response despite KNOWING the
                skill (slipping = 0.10).

Update Equations:
    Step 1 — Posterior given the observation:

        If answer is CORRECT:
            P(Lₙ | correct) =         P(Lₙ₋₁) × (1 - P(S))
                               ─────────────────────────────────────
                               P(Lₙ₋₁) × (1 - P(S)) + (1 - P(Lₙ₋₁)) × P(G)

        If answer is INCORRECT:
            P(Lₙ | incorrect) =       P(Lₙ₋₁) × P(S)
                                ────────────────────────────────────────
                                P(Lₙ₋₁) × P(S) + (1 - P(Lₙ₋₁)) × (1 - P(G))

    Step 2 — Learning transition (accounts for learning during the attempt):
        P(Lₙ) = P(Lₙ | obs) + (1 - P(Lₙ | obs)) × P(T)

    Step 3 — Difficulty modifier (optional, applied to P(S) and P(G)):
        For harder questions, slipping is more likely and guessing less so.
        difficulty_modifier adjusts P(S) upward and P(G) downward by a
        scaled factor tied to the question's DifficultyLevel (1–3).

References:
    Corbett, A. T., & Anderson, J. R. (1994). Knowledge tracing: Modeling
    the acquisition of procedural knowledge. User Modeling and User-Adapted
    Interaction, 4(4), 253–278.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from assessments.models import DifficultyLevel
from assessments.services.base import BaseStudentModel, EngineUpdate
from assessments.services.ledger import ModelTrace

if TYPE_CHECKING:
    from assessments.models import Question, UserKnowledgeState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default BKT hyper-parameters (research-calibrated baselines)
# ---------------------------------------------------------------------------
DEFAULT_P_INIT: float = 0.15    # P(L₀) — prior probability of mastery
DEFAULT_P_TRANSIT: float = 0.20  # P(T)  — learning rate per opportunity
DEFAULT_P_GUESS: float = 0.25   # P(G)  — guessing probability
DEFAULT_P_SLIP: float = 0.10    # P(S)  — slip probability

# Per-difficulty adjustment scale for P(S) and P(G).
# EASY (1) → no adjustment; MEDIUM (2) → moderate; HARD (3) → strong.
DIFFICULTY_MODIFIER_SCALE: float = 0.05


def prior_from_state(state: UserKnowledgeState, p_init: float) -> float:
    """
    P(L) before this answer, read from the learner's current state row
    (stage 1: the knowledge history is no longer consulted).

    A row carries an engine estimate only if it has answers and holds a
    probability in (0, 1]. Otherwise P(L0) is used: new rows, rows written by
    the removed descendant cascade (no answers), rows touched only by test
    sessions, and legacy rows holding a 0-100 test grade. With P(T) > 0 a BKT
    posterior is never exactly 0, so 0.0 means "never estimated".
    """
    p = float(state.mastery_percentage)
    if state.total_attempts > 0 and 0.0 < p <= 1.0:
        return p
    return p_init


def bkt_step(
    prior: float,
    p_guess: float,
    p_slip: float,
    p_transit: float,
    is_correct: bool,
) -> tuple[float, float]:
    """
    One BKT observation: returns (p_hat, P(L) after the learning transition).

        p_hat     = P(L)(1 - P(S)) + (1 - P(L)) P(G)
        P(L | 1)  = P(L)(1 - P(S)) / p_hat
        P(L | 0)  = P(L) P(S) / (1 - p_hat)
        P(L)'     = P(L | x) + (1 - P(L | x)) P(T)
    """
    p_hat = prior * (1.0 - p_slip) + (1.0 - prior) * p_guess
    if is_correct:
        numerator, denominator = prior * (1.0 - p_slip), p_hat
    else:
        numerator, denominator = prior * p_slip, 1.0 - p_hat

    # Guard against division by zero (impossible with valid parameters).
    posterior = prior if denominator < 1e-12 else numerator / denominator
    updated = posterior + (1.0 - posterior) * p_transit
    return p_hat, max(0.0, min(1.0, updated))


class BayesianKnowledgeTracingEngine(BaseStudentModel):
    """
    Concrete strategy: Bayesian Knowledge Tracing (BKT).

    Estimates P(mastery) as a continuous probability in [0.0, 1.0] using
    the standard Hidden Markov Model update rule with optional
    difficulty-aware parameter adjustment.

    The prior is the learner's current state (see ``prior_from_state``),
    falling back to ``p_init`` when the state holds no estimate yet.

    Usage:
        Set ``STUDENT_MODEL_ENGINE = "bkt"`` in ``config/settings.py``.
    """

    version = "bkt/0"

    def __init__(
        self,
        p_init: float = DEFAULT_P_INIT,
        p_transit: float = DEFAULT_P_TRANSIT,
        p_guess: float = DEFAULT_P_GUESS,
        p_slip: float = DEFAULT_P_SLIP,
    ) -> None:
        self.p_init: float = p_init
        self.p_transit: float = p_transit
        self.p_guess: float = p_guess
        self.p_slip: float = p_slip

    def calculate_new_mastery(
        self,
        user,
        topic,
        current_state: UserKnowledgeState,
        question: Question,
        is_correct: bool,
    ) -> float:
        """Return the posterior P(mastery) in [0.0, 1.0] (see ``update``)."""
        return self.update(
            user=user,
            topic=topic,
            current_state=current_state,
            question=question,
            is_correct=is_correct,
        ).mastery

    def update(
        self,
        *,
        user,
        topic,
        current_state: UserKnowledgeState,
        question: Question,
        is_correct: bool,
    ) -> EngineUpdate:
        prior: float = prior_from_state(current_state, self.p_init)

        # Harder questions increase slip probability (even a knower may err)
        # and decrease guess probability (harder to guess correctly):
        #   modifier = (difficulty - 1) x scale
        #   P(S)_adj = min(P(S) + modifier, 0.40)
        #   P(G)_adj = max(P(G) - modifier, 0.05)
        difficulty_value: int = question.difficulty  # 1=EASY, 2=MEDIUM, 3=HARD
        modifier: float = (difficulty_value - DifficultyLevel.EASY) * DIFFICULTY_MODIFIER_SCALE
        p_slip_adj: float = min(self.p_slip + modifier, 0.40)
        p_guess_adj: float = max(self.p_guess - modifier, 0.05)

        p_hat, p_new = bkt_step(prior, p_guess_adj, p_slip_adj, self.p_transit, is_correct)

        logger.info(
            "BKT update: user=%s topic=%s correct=%s | prior=%.4f p_hat=%.4f -> %.4f "
            "(P(S)=%.3f P(G)=%.3f diff=%d)",
            user.pk, topic.pk, is_correct, prior, p_hat, p_new,
            p_slip_adj, p_guess_adj, difficulty_value,
        )

        return EngineUpdate(
            mastery=p_new,
            trace=ModelTrace(
                p_before=prior,
                p_hat=p_hat,
                p_after=p_new,
                guess_used=p_guess_adj,
                slip_used=p_slip_adj,
            ),
        )
