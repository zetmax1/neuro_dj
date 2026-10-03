"""
assessments/services/engines/streak.py — Streak-based Estimation Engine.

This is the refactored extraction of the original state-machine logic from
the monolithic `services.py`. The algorithm is deterministic and uses
consecutive-correct-answer streaks to decide mastery promotions.

State-machine rules:
    1. Correct answer → increment streak.
       - streak >= 3 on HARD difficulty → promote to MASTERED.
       - streak >= 2 on current difficulty → promote mastery_level by 1.
    2. Incorrect answer → reset streak to 0 (no demotion).

The returned float is the new MasteryLevel cast to float for compatibility
with the unified history ledger (e.g., 4.0 = MASTERED).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from assessments.models import DifficultyLevel, MasteryLevel
from assessments.services.base import BaseStudentModel

if TYPE_CHECKING:
    from assessments.models import Question, UserKnowledgeState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tuneable thresholds (preserved from the original implementation)
# ---------------------------------------------------------------------------
STREAK_TO_PROMOTE: int = 2        # Consecutive correct answers to advance
STREAK_TO_MASTER_HARD: int = 3    # Streak on HARD to trigger mastery cascade


class StreakEstimationEngine(BaseStudentModel):
    """
    Concrete strategy: deterministic streak-based mastery estimation.

    This engine mirrors the original state-machine logic that was embedded
    in ``services.py``. It operates on streak counters and difficulty
    thresholds — no probabilistic math involved.

    The engine mutates ``current_state.streak`` and ``current_state.mastery_level``
    in-memory (the orchestrator persists these changes transactionally).
    """

    version = "streak/0"

    def calculate_new_mastery(
        self,
        user,
        topic,
        current_state: UserKnowledgeState,
        question: Question,
        is_correct: bool,
    ) -> float:
        """
        Apply streak-based promotion rules and return the new mastery level.

        Side-effects on ``current_state`` (in-memory only):
            - ``streak`` is incremented or reset.
            - ``mastery_level`` may be promoted.

        Returns:
            The new mastery level as a float (e.g., 4.0 for MASTERED).
        """
        if is_correct:
            current_state.streak += 1
            self._maybe_promote(current_state, question.difficulty)
        else:
            current_state.streak = 0

        return float(current_state.mastery_level)

    # -------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _maybe_promote(state: UserKnowledgeState, difficulty: int) -> None:
        """
        Apply state-machine promotion rules.

        Rule A: streak >= STREAK_TO_MASTER_HARD on HARD → jump to MASTERED.
        Rule B: streak >= STREAK_TO_PROMOTE → advance one mastery level.
        """
        if state.mastery_level >= MasteryLevel.MASTERED:
            return  # Already at ceiling

        # Rule A: fast-track mastery on hard questions
        if (
            difficulty == DifficultyLevel.HARD
            and state.streak >= STREAK_TO_MASTER_HARD
        ):
            state.mastery_level = MasteryLevel.MASTERED
            logger.info(
                "User %s MASTERED topic %s (hard streak=%d)",
                state.user_id, state.topic_id, state.streak,
            )
            return

        # Rule B: gradual promotion
        if state.streak >= STREAK_TO_PROMOTE:
            state.mastery_level = min(
                state.mastery_level + 1,
                MasteryLevel.MASTERED,
            )
            state.streak = 0  # Reset after promotion
            logger.info(
                "User %s promoted to level %d on topic %s",
                state.user_id, state.mastery_level, state.topic_id,
            )
