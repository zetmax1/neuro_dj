"""
assessments/services/engines/irt.py — 2-Parameter Logistic (2PL) Item Response Theory Engine.

Implements the 2PL IRT model for adaptive student modeling as a concrete
strategy satisfying the ``BaseStudentModel`` interface.

2PL IRT Model:
    P(correct | θ, a, b) = 1 / (1 + exp(-a * (θ - b)))

    Where:
        - θ (theta): Latent student ability estimate.
        - a (discrimination): Sensitivity of the question to ability differences.
        - b (difficulty): Ability level where probability of correct response is 0.5.

Online Ability Estimation:
    Full maximum likelihood estimation (MLE) or marginal maximum likelihood
    estimation (MMLE) requires iterative optimization over the entire response
    history, which is computationally expensive for real-time API requests.

    Instead, we employ an online stochastic gradient update (Elo-style adaptation):
        θ_new = θ_old + K * (y - P(correct | θ_old, a, b))
    where K is the learning-rate constant (default K=0.3) and y ∈ {0, 1}.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from assessments.models import UserAbility
from assessments.services.base import BaseStudentModel

if TYPE_CHECKING:
    from curriculum.models import Topic
    from assessments.models import Question, UserKnowledgeState

logger = logging.getLogger(__name__)

DEFAULT_K_LEARNING_RATE: float = 0.3


def probability_correct(theta: float, a: float, b: float) -> float:
    """
    Calculate probability of a correct response under the 2PL IRT model.

    P(θ, a, b) = 1 / (1 + exp(-a * (θ - b)))
    """
    # Guard against exponent overflow
    val = -a * (theta - b)
    val_clamped = max(-50.0, min(50.0, val))
    return 1.0 / (1.0 + math.exp(val_clamped))


class IRTEngine(BaseStudentModel):
    """
    Concrete strategy: Item Response Theory (2PL IRT).

    Tracks continuous latent ability (theta) per user/topic and updates it
    online after each attempt.
    """

    version = "irt/0"

    def __init__(self, k_factor: float = DEFAULT_K_LEARNING_RATE) -> None:
        self.k_factor: float = k_factor

    def update_ability(self, user, question: Question, is_correct: bool) -> float:
        """
        Lightweight online update for user's latent ability (theta).

        Computationally cheap per-request approximation:
            theta_new = theta_old + K * (y - P(correct | theta_old, a, b))

        Persists the updated theta to the UserAbility table and returns it.
        """
        return self.update_ability_pair(user, question, is_correct)[1]

    def update_ability_pair(self, user, question: Question, is_correct: bool) -> tuple[float, float]:
        """Same as ``update_ability`` but returns ``(theta_old, theta_new)``."""
        topic = question.topic
        ability_obj, _ = UserAbility.objects.get_or_create(
            user=user,
            topic=topic,
            defaults={"theta": 0.0},
        )

        theta_old = ability_obj.theta
        a = question.irt_discrimination
        b = question.irt_difficulty

        p_hat = probability_correct(theta_old, a, b)
        y = 1.0 if is_correct else 0.0

        # Online gradient / stochastic update
        theta_new = theta_old + self.k_factor * (y - p_hat)

        ability_obj.theta = theta_new
        ability_obj.save(update_fields=["theta", "theta_updated_at"])

        logger.info(
            "IRT update: user=%s topic=%s correct=%s | "
            "theta_old=%.3f → theta_new=%.3f (a=%.2f b=%.2f P=%.3f)",
            user.pk,
            topic.pk,
            is_correct,
            theta_old,
            theta_new,
            a,
            b,
            p_hat,
        )

        return theta_old, theta_new

    def calculate_new_mastery(
        self,
        user,
        topic: Topic,
        current_state: UserKnowledgeState,
        question: Question,
        is_correct: bool,
    ) -> float:
        """
        Calculates updated theta and maps it to a continuous mastery probability in [0.0, 1.0].
        """
        theta_new = self.update_ability(user, question, is_correct)
        # Map latent ability theta to mastery probability using logistic function
        mastery_prob = 1.0 / (1.0 + math.exp(-theta_new))
        return max(0.0, min(1.0, mastery_prob))
