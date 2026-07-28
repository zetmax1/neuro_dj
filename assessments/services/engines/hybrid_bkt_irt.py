"""
assessments/services/engines/hybrid_bkt_irt.py — Hybrid BKT-IRT Student Model.

Academic Methodology:
This hybrid engine unifies Bayesian Knowledge Tracing (BKT) and 2-Parameter Logistic
Item Response Theory (2PL IRT) into a dual-layer cognitive architecture.

1. Longitudinal Mastery Layer (BKT Core):
   BKT serves as the primary longitudinal state estimator, tracking the latent binary
   mastery probability P(L) of a learner over time using Hidden Markov Model updates
   with parameter set {P(L₀), P(T), P(S), P(G)}.

2. Continuous Item Characteristic Layer (IRT Integration):
   Rather than binning questions into discrete difficulty buckets (Easy/Medium/Hard),
   the engine computes an online 2PL IRT latent ability estimate θ (theta) for the learner
   via per-item stochastic gradient updates.

3. Hybrid Parameter Adaptation:
   The continuous distance between item difficulty b (question.irt_difficulty) and user
   ability θ (UserAbility.theta), Δ = b - θ, modulates BKT's slip P(S) and guess P(G)
   probabilities dynamically:
       modifier = (question.irt_difficulty - θ) * scale
       P(S)_adj = min(P(S) + modifier, 0.40)
       P(G)_adj = max(P(G) - modifier, 0.05)

   When item difficulty exceeds learner ability (b > θ), slip probability increases while
   guess probability decreases. Conversely, when learner ability exceeds item difficulty
   (θ > b), slip probability decreases while guess probability increases. This replaces
   coarse discrete difficulty tiers with fine-grained item-level adaptation while
   preserving the probabilistic guarantees of BKT.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from assessments.models import UserAbility
from assessments.services.base import BaseStudentModel
from assessments.services.engines.bayesian import (
    DIFFICULTY_MODIFIER_SCALE,
    BayesianKnowledgeTracingEngine,
)
from assessments.services.engines.irt import IRTEngine

if TYPE_CHECKING:
    from curriculum.models import Topic
    from assessments.models import Question, UserKnowledgeState

logger = logging.getLogger(__name__)


class HybridBKTIRTEngine(BaseStudentModel):
    """
    Concrete strategy: Hybrid BKT + IRT Student Modeling Engine.

    Combines BKT longitudinal mastery tracking with IRT continuous ability (theta)
    estimation for fine-grained difficulty adjustments.
    """

    def __init__(self) -> None:
        self.bkt_engine = BayesianKnowledgeTracingEngine()
        self.irt_engine = IRTEngine()

    def calculate_new_mastery(
        self,
        user,
        topic: Topic,
        current_state: UserKnowledgeState,
        question: Question,
        is_correct: bool,
    ) -> float:
        """
        Calculate updated BKT mastery probability with continuous IRT-based difficulty adjustment.
        """
        # Step 1: Update IRT latent ability theta
        theta_new = self.irt_engine.update_ability(user, question, is_correct)

        # Step 2: Retrieve prior BKT P(L)
        p_learned_prior = self.bkt_engine._retrieve_prior(user, topic)

        # Step 3: Compute continuous difficulty modifier using (irt_difficulty - theta)
        b = question.irt_difficulty
        delta = b - theta_new
        modifier = delta * DIFFICULTY_MODIFIER_SCALE

        p_slip_adj = max(0.01, min(0.40, self.bkt_engine.p_slip + modifier))
        p_guess_adj = max(0.05, min(0.50, self.bkt_engine.p_guess - modifier))

        # Step 4: Bayesian update given observation
        if is_correct:
            numerator = p_learned_prior * (1.0 - p_slip_adj)
            denominator = (
                p_learned_prior * (1.0 - p_slip_adj)
                + (1.0 - p_learned_prior) * p_guess_adj
            )
        else:
            numerator = p_learned_prior * p_slip_adj
            denominator = (
                p_learned_prior * p_slip_adj
                + (1.0 - p_learned_prior) * (1.0 - p_guess_adj)
            )

        if denominator < 1e-12:
            p_learned_posterior = p_learned_prior
        else:
            p_learned_posterior = numerator / denominator

        # Step 5: Learning transition
        p_learned_updated = (
            p_learned_posterior
            + (1.0 - p_learned_posterior) * self.bkt_engine.p_transit
        )

        p_learned_clamped = max(0.0, min(1.0, p_learned_updated))

        logger.info(
            "Hybrid BKT-IRT update: user=%s topic=%s correct=%s | "
            "theta=%.3f b=%.2f delta=%.2f → P(S)=%.3f P(G)=%.3f | "
            "prior=%.4f → mastery=%.4f",
            user.pk,
            topic.pk,
            is_correct,
            theta_new,
            b,
            delta,
            p_slip_adj,
            p_guess_adj,
            p_learned_prior,
            p_learned_clamped,
        )

        return p_learned_clamped
