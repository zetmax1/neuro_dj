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

from assessments.models import DifficultyLevel, UserKnowledgeHistory
from assessments.services.base import BaseStudentModel

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


class BayesianKnowledgeTracingEngine(BaseStudentModel):
    """
    Concrete strategy: Bayesian Knowledge Tracing (BKT).

    Estimates P(mastery) as a continuous probability in [0.0, 1.0] using
    the standard Hidden Markov Model update rule with optional
    difficulty-aware parameter adjustment.

    The engine is stateless between calls — the prior is retrieved from
    the most recent ``UserKnowledgeHistory`` entry for the (user, topic)
    pair, falling back to ``p_init`` when no history exists.

    Usage:
        Set ``STUDENT_MODEL_ENGINE = "bkt"`` in ``config/settings.py``.
    """

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
        """
        Calculate the posterior P(mastery) using Bayesian Knowledge Tracing.

        Args:
            user: The Django user instance.
            topic: The curriculum Topic being assessed.
            current_state: The locked UserKnowledgeState row.
            question: The Question that was just answered.
            is_correct: Whether the user's selected choice was correct.

        Returns:
            A float in [0.0, 1.0] representing P(mastery | observations),
            clamped to prevent degenerate boundary values.
        """
        # ──────────────────────────────────────────────────────────────
        # Step 0: Retrieve the prior P(L) from the most recent history
        # entry for this (user, topic) pair.  If no history exists (the
        # student's first attempt), fall back to the baseline P(L₀).
        # ──────────────────────────────────────────────────────────────
        p_learned_prior: float = self._retrieve_prior(user, topic)

        # ──────────────────────────────────────────────────────────────
        # Step 1: Compute difficulty-adjusted P(S) and P(G).
        # Harder questions increase slip probability (even a knower may
        # err) and decrease guess probability (harder to guess correctly).
        #   modifier = (difficulty - 1) × scale
        #   P(S)_adj = P(S) + modifier      (capped at 0.40)
        #   P(G)_adj = P(G) - modifier      (floored at 0.05)
        # ──────────────────────────────────────────────────────────────
        difficulty_value: int = question.difficulty  # 1=EASY, 2=MEDIUM, 3=HARD
        modifier: float = (difficulty_value - DifficultyLevel.EASY) * DIFFICULTY_MODIFIER_SCALE

        p_slip_adj: float = min(self.p_slip + modifier, 0.40)
        p_guess_adj: float = max(self.p_guess - modifier, 0.05)

        # ──────────────────────────────────────────────────────────────
        # Step 2: Bayesian posterior update given the observation.
        #
        # Using Bayes' rule to compute P(L | observation):
        #
        #   P(correct | L)     = 1 - P(S)    (knows it, doesn't slip)
        #   P(correct | ¬L)    = P(G)         (doesn't know, guesses right)
        #   P(incorrect | L)   = P(S)         (knows it, but slips)
        #   P(incorrect | ¬L)  = 1 - P(G)    (doesn't know, guesses wrong)
        #
        # Posterior:
        #   P(L | obs) = P(obs | L) × P(L) / P(obs)
        # where
        #   P(obs) = P(obs | L) × P(L) + P(obs | ¬L) × (1 - P(L))
        # ──────────────────────────────────────────────────────────────
        if is_correct:
            # Numerator:   P(correct | learned) × P(learned)
            numerator: float = p_learned_prior * (1.0 - p_slip_adj)
            # Denominator: P(correct) via total probability
            denominator: float = (
                p_learned_prior * (1.0 - p_slip_adj)
                + (1.0 - p_learned_prior) * p_guess_adj
            )
        else:
            # Numerator:   P(incorrect | learned) × P(learned)
            numerator = p_learned_prior * p_slip_adj
            # Denominator: P(incorrect) via total probability
            denominator = (
                p_learned_prior * p_slip_adj
                + (1.0 - p_learned_prior) * (1.0 - p_guess_adj)
            )

        # Guard against division by zero (theoretically impossible with
        # valid parameters, but defensive coding for production safety).
        if denominator < 1e-12:
            p_learned_posterior: float = p_learned_prior
        else:
            p_learned_posterior = numerator / denominator

        # ──────────────────────────────────────────────────────────────
        # Step 3: Learning transition.
        # Even if the student didn't demonstrate knowledge on this attempt,
        # the act of practicing may have caused learning.  The transition
        # probability P(T) captures this:
        #
        #   P(Lₙ) = P(Lₙ | obs) + (1 - P(Lₙ | obs)) × P(T)
        #
        # This ensures P(L) is monotonically non-decreasing per the
        # standard BKT assumption (no forgetting within a session).
        # ──────────────────────────────────────────────────────────────
        p_learned_updated: float = (
            p_learned_posterior
            + (1.0 - p_learned_posterior) * self.p_transit
        )

        # ──────────────────────────────────────────────────────────────
        # Step 4: Clamp the result to [0.0, 1.0] to prevent floating-
        # point drift from producing out-of-range probabilities.
        # ──────────────────────────────────────────────────────────────
        p_learned_clamped: float = max(0.0, min(1.0, p_learned_updated))

        logger.info(
            "BKT update: user=%s topic=%s correct=%s | "
            "prior=%.4f → posterior=%.4f → after_transit=%.4f "
            "(P(S)=%.3f P(G)=%.3f diff=%d)",
            user.pk,
            topic.pk,
            is_correct,
            p_learned_prior,
            p_learned_posterior,
            p_learned_clamped,
            p_slip_adj,
            p_guess_adj,
            difficulty_value,
        )

        return p_learned_clamped

    # -------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------

    def _retrieve_prior(self, user, topic) -> float:
        """
        Fetch the most recent P(L) from UserKnowledgeHistory.

        If no prior history exists for this (user, topic) pair, returns
        the baseline ``self.p_init``.  The query uses the composite
        index ``idx_history_user_topic_ts`` for O(1) lookup.
        """
        latest_entry = (
            UserKnowledgeHistory.objects
            .filter(user=user, topic=topic)
            .order_by("-created_at")
            .values_list("calculated_mastery", flat=True)
            .first()
        )

        if latest_entry is not None:
            return float(latest_entry)

        return self.p_init
