"""
assessments/services/orchestrator.py — Execution Orchestrator.

Coordinates the full answer-submission lifecycle inside a single
@transaction.atomic block:

    1. Validate question + choice (archived topics are not answerable).
    2. Lock the learner's (user, topic) ledger key, then the state row.
    3. Classify the answer: a repeat of a question answered within the
       review window is logged as ``review_repeat`` and changes nothing (D25).
    4. Delegate the mastery calculation to the active engine (strategy pattern).
    5. Persist mastery_percentage + discrete mastery_level on the state row.
    6. Append the answer to the ledger (``ledger.record_attempt``) together
       with the quantities the engine used, and link the history entry to it.
    7. If the legacy threshold is reached, set the global unlock flag of the
       child topics (removed with the readiness service in stage 4).
    8. Select the next adaptive question.

The orchestrator never writes anything for topics or questions the learner
did not answer (D8): the descendant cascade and the easy-question skip that
fabricated answers were removed in stage 1.

Engine resolution:
    The active engine is determined by ``settings.STUDENT_MODEL_ENGINE``.
    Change this setting to swap algorithms without touching any
    orchestration code.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

from django.conf import settings
from django.db import transaction

from curriculum.models import Topic

from assessments.models import (
    AlgorithmChoice,
    AttemptSource,
    Choice,
    MasteryLevel,
    Question,
    UserKnowledgeHistory,
    UserKnowledgeState,
)
from assessments.services import ledger
from assessments.services.engines import get_engine
from assessments.services.question_selection import get_next_question

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Legacy mastery threshold as an integer percentage (0–100), replaced by
# τ/δ hysteresis in stage 4. When mastery_percentage * 100 >= this value,
# the topic is marked MASTERED and its child topics are unlocked.
MASTERY_THRESHOLD: int = 70

# Sources ``process_submission`` accepts. Seeds and the simulator go through
# the same engine path but are labelled so experiments can exclude them (D13).
SUBMISSION_SOURCES: frozenset[str] = frozenset({
    AttemptSource.ADAPTIVE,
    AttemptSource.SEED,
    AttemptSource.SIMULATED,
})


# ---------------------------------------------------------------------------
# Data Transfer Object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubmissionResult:
    """Returned to the view layer after processing an answer."""
    is_correct: bool
    explanation: str
    mastery_level: int
    mastery_display: str
    mastery_percentage: float
    streak: int
    next_question: Optional[Question]
    source: str
    attempt_id: int
    attempt_no: int


# ---------------------------------------------------------------------------
# Mastery float → MasteryLevel mapping (for probabilistic engines)
# ---------------------------------------------------------------------------

_PROBABILITY_THRESHOLDS: list[tuple[float, int]] = [
    (0.90, MasteryLevel.MASTERED),
    (0.70, MasteryLevel.ADVANCED),
    (0.45, MasteryLevel.INTERMEDIATE),
    (0.20, MasteryLevel.BEGINNER),
]


def _mastery_float_to_level(value: float, algorithm: str) -> int:
    """
    Convert a raw engine output to a discrete MasteryLevel.

    For streak-based engines the float is already an integer-mapped
    level (0.0–4.0). For probabilistic engines the float is P(mastery)
    in [0.0, 1.0] and we apply threshold binning.
    """
    if algorithm == AlgorithmChoice.STREAK:
        return int(value)

    # Probabilistic engine: threshold binning
    for threshold, level in _PROBABILITY_THRESHOLDS:
        if value >= threshold:
            return level
    return MasteryLevel.NOT_STARTED


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@transaction.atomic
def process_submission(
    *,
    user,
    question_id: int,
    choice_id: int,
    source: str = AttemptSource.ADAPTIVE,
    answered_at: datetime | None = None,
) -> SubmissionResult:
    """
    Process one answer and return a SubmissionResult DTO for the view.

    ``source`` is ``adaptive`` for learners; seed and simulator commands pass
    ``seed``/``simulated`` (and may back-date with ``answered_at``).
    Everything runs in one transaction: the ledger row, the state update and
    the history entry commit or roll back together.
    """
    if source not in SUBMISSION_SOURCES:
        raise ValueError(f"process_submission does not accept source={source!r}.")

    # --- Step 1: Fetch & validate (single query with select_related) -------
    choice: Choice = (
        Choice.objects
        .select_related("question", "question__topic")
        .get(pk=choice_id, question_id=question_id, question__topic__is_archived=False)
    )
    question: Question = choice.question
    topic: Topic = question.topic
    is_correct: bool = choice.is_correct

    # --- Step 2: Serialise this learner's answers on this topic ------------
    # The advisory lock is taken before the state row lock (same order as the
    # test-session path), so classification, attempt_no and the state update
    # all see one consistent ledger.
    ledger.lock_learner_topics(user.pk, [topic.pk])

    # --- Step 3: D25 — a repeat within the review window updates nothing ---
    source = ledger.classify_source(user=user, question=question, requested=source)
    if source == AttemptSource.REVIEW_REPEAT:
        attempt = ledger.record_attempt(user=user, choice=choice, source=source)
        state = UserKnowledgeState.objects.filter(user=user, topic=topic).first()
        return SubmissionResult(
            is_correct=is_correct,
            explanation=question.explanation,
            mastery_level=state.mastery_level if state else MasteryLevel.NOT_STARTED,
            mastery_display=(
                state.get_mastery_level_display() if state else MasteryLevel.NOT_STARTED.label
            ),
            mastery_percentage=state.mastery_percentage if state else 0.0,
            streak=state.streak if state else 0,
            next_question=get_next_question(user=user, topic_id=topic.pk),
            source=attempt.source,
            attempt_id=attempt.pk,
            attempt_no=attempt.attempt_no,
        )

    # --- Step 4: Lock & load user knowledge state --------------------------
    state, _created = (
        UserKnowledgeState.objects
        .select_for_update()
        .get_or_create(
            user=user,
            topic=topic,
            defaults={
                "mastery_level": MasteryLevel.NOT_STARTED,
                "mastery_percentage": 0.0,
                "score": 0,
                "total_attempts": 0,
                "correct_attempts": 0,
                "streak": 0,
            },
        )
    )

    # --- Step 5: Resolve and invoke the active engine ----------------------
    # The engine reads its prior from the state *before* the counters below
    # are incremented.
    algorithm_key: str = getattr(
        settings, "STUDENT_MODEL_ENGINE", AlgorithmChoice.STREAK,
    )
    engine = get_engine(algorithm_key)
    update = engine.update(
        user=user,
        topic=topic,
        current_state=state,
        question=question,
        is_correct=is_correct,
    )
    mastery_float: float = update.mastery

    # --- Step 6: Persist mastery state -------------------------------------
    state.total_attempts += 1
    if is_correct:
        state.correct_attempts += 1

    # Map the engine output to a discrete MasteryLevel for backward compat
    state.mastery_level = _mastery_float_to_level(
        mastery_float, algorithm_key,
    )

    # Store the raw probability (0.0–1.0) for BKT/IRT precision.
    # For streak engines, normalise the level to [0.0, 1.0] range.
    if algorithm_key == AlgorithmChoice.STREAK:
        state.mastery_percentage = float(state.mastery_level) / float(MasteryLevel.MASTERED)
    else:
        state.mastery_percentage = mastery_float

    # Recalculate running accuracy
    state.score = round(
        (state.correct_attempts / state.total_attempts) * 100
    )

    state.save(update_fields=[
        "mastery_level", "mastery_percentage", "score",
        "total_attempts", "correct_attempts", "streak", "updated_at",
    ])

    # --- Step 7: Append to the ledger and the history ----------------------
    attempt = ledger.record_attempt(
        user=user,
        choice=choice,
        source=source,
        trace=replace(update.trace, engine_version=engine.version),
        answered_at=answered_at,
    )
    UserKnowledgeHistory.objects.create(
        user=user,
        topic=topic,
        calculated_mastery=mastery_float,
        algorithm_used=algorithm_key,
        attempt=attempt,
        created_at=attempt.answered_at,
    )

    # --- Step 8: Legacy threshold → global unlock of child topics ----------
    mastery_pct_int: int = round(state.mastery_percentage * 100)

    if mastery_pct_int >= MASTERY_THRESHOLD:
        # Ensure the discrete level reflects MASTERED when threshold met
        if state.mastery_level < MasteryLevel.MASTERED:
            state.mastery_level = MasteryLevel.MASTERED
            state.save(update_fields=["mastery_level", "updated_at"])

        _unlock_child_topics(topic=topic)

    # --- Step 9: Pick next question (read-only) ----------------------------
    next_question = get_next_question(user=user, topic_id=topic.pk)

    return SubmissionResult(
        is_correct=is_correct,
        explanation=question.explanation,
        mastery_level=state.mastery_level,
        mastery_display=state.get_mastery_level_display(),
        mastery_percentage=state.mastery_percentage,
        streak=state.streak,
        next_question=next_question,
        source=attempt.source,
        attempt_id=attempt.pk,
        attempt_no=attempt.attempt_no,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _unlock_child_topics(*, topic: Topic) -> None:
    """
    Bulk-unlock all immediate child topics of a mastered topic.

    One query for the children and one bulk UPDATE of the legacy global
    flag (not a structural field, so the KB guard allows it).

    Performance: exactly 2 DB queries (children fetch + bulk UPDATE).
    """
    child_ids: list[int] = list(
        Topic.objects.filter(parent=topic).values_list("id", flat=True)
    )

    if not child_ids:
        return

    # Bulk UPDATE — single query, no loops
    updated_count: int = (
        Topic.objects
        .filter(pk__in=child_ids, is_unlocked=False)
        .update(is_unlocked=True)
    )

    if updated_count > 0:
        logger.info(
            "Unlocked %d child topic(s) of topic %s (pk=%d)",
            updated_count, topic.name, topic.pk,
        )
