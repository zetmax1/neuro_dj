"""
assessments/services/base.py — Abstract Strategy Interface for Student Models.

This module defines the contract that every pluggable cognitive estimation
engine must satisfy. The Strategy Pattern decouples the orchestration layer
from the specific mathematical model used to estimate student mastery.

How to add a new algorithm:
    1. Create a new file in `assessments/services/engines/` (e.g., `irt.py`).
    2. Subclass `BaseStudentModel` and implement `calculate_new_mastery()`.
    3. Add a new entry to `AlgorithmChoice` in `assessments/models.py`.
    4. Register the engine in `assessments/services/engines/__init__.py`.
    5. Set `STUDENT_MODEL_ENGINE` in `config/settings.py` to the new key.

The orchestrator (`assessments/services/orchestrator.py`) handles engine
resolution, transactional guarantees, and history logging — individual
engines should contain ONLY pure estimation logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from assessments.services.ledger import ModelTrace

if TYPE_CHECKING:
    from assessments.models import Question, UserKnowledgeState


@dataclass(frozen=True)
class EngineUpdate:
    """New mastery estimate plus the quantities used to compute it (for the ledger)."""
    mastery: float
    trace: ModelTrace = field(default_factory=ModelTrace)


class BaseStudentModel(ABC):
    """
    Abstract base class defining the contract for student mastery estimation.

    Every concrete engine must implement `calculate_new_mastery()`, which
    receives the current learner state and the latest interaction, then
    returns a float representing the new mastery estimate.

    The returned float is interpreted as follows:
        - For discrete models (e.g., streak-based): a value from the
          MasteryLevel enum cast to float (0.0, 1.0, 2.0, 3.0, 4.0).
        - For probabilistic models (e.g., BKT, IRT): a probability
          in [0.0, 1.0] representing P(mastery | observations).

    The orchestrator logs this value in UserKnowledgeHistory and maps
    it back to a MasteryLevel integer for UserKnowledgeState.
    """

    # Recorded as AssessmentAttempt.engine_version. "/0" marks the engines that
    # predate the chapter II model (replaced in stage 3).
    version: str = ""

    def update(
        self,
        *,
        user,
        topic,
        current_state: UserKnowledgeState,
        question: Question,
        is_correct: bool,
    ) -> EngineUpdate:
        """
        Same as ``calculate_new_mastery`` but also returns the intermediate
        quantities for the answer ledger. Engines that do not override it
        report only the new estimate.
        """
        return EngineUpdate(
            mastery=self.calculate_new_mastery(
                user=user,
                topic=topic,
                current_state=current_state,
                question=question,
                is_correct=is_correct,
            ),
        )

    @abstractmethod
    def calculate_new_mastery(
        self,
        user,
        topic,
        current_state: UserKnowledgeState,
        question: Question,
        is_correct: bool,
    ) -> float:
        """
        Calculate the updated mastery estimate after a single interaction.

        Args:
            user: The Django user instance.
            topic: The curriculum Topic being assessed.
            current_state: The locked UserKnowledgeState row (select_for_update).
            question: The Question that was just answered.
            is_correct: Whether the user's selected choice was correct.

        Returns:
            A float representing the new mastery value. Interpretation
            depends on the engine type (see class docstring).

        Note:
            This method must be side-effect-free with respect to the database.
            All DB writes (state update, history log) are handled by the
            orchestrator to maintain transactional atomicity.
        """
        ...
