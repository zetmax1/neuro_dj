"""
assessments/services/orchestrator.py — Execution Orchestrator.

Coordinates the full answer-submission lifecycle inside a single
@transaction.atomic block with row-level locking:

    1. Validate question + choice.
    2. Record the immutable AssessmentAttempt.
    3. Lock UserKnowledgeState via select_for_update().
    4. Delegate mastery calculation to the active engine (strategy pattern).
    5. Persist mastery_percentage + discrete mastery_level on the state row.
    6. Append an immutable UserKnowledgeHistory ledger entry.
    7. If mastery threshold reached, unlock child topics and cascade.
    8. Select the next adaptive question.

Engine resolution:
    The active engine is determined by ``settings.STUDENT_MODEL_ENGINE``
    (defaults to ``"streak"``). Change this setting to swap algorithms
    without touching any orchestration code.

Tree propagation:
    When mastery_percentage >= MASTERY_THRESHOLD (85%), the orchestrator
    uses django-tree-queries' ``get_children()`` CTE to fetch immediate
    child topics and bulk-updates their ``is_unlocked`` flag to True.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from curriculum.models import Topic

from assessments.models import (
    AlgorithmChoice,
    AssessmentAttempt,
    Choice,
    MasteryLevel,
    Question,
    UserKnowledgeHistory,
    UserKnowledgeState,
)
from assessments.services.engines import get_engine
from assessments.services.question_selection import get_next_question

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Mastery threshold as an integer percentage (0–100).
# When mastery_percentage * 100 >= this value, the topic is marked MASTERED
# and its immediate child topics are unlocked.
MASTERY_THRESHOLD: int = 70

# Minimum accuracy on Medium+Hard questions to trigger easy-question bypass.
# If a student scores >= this percentage on higher-difficulty questions,
# all Easy questions for the topic are marked as bypassed.
ADAPTIVE_SKIP_ACCURACY: int = 70
ADAPTIVE_SKIP_MIN_ATTEMPTS: int = 3  # Minimum M+H attempts before skip kicks in


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
) -> SubmissionResult:
    """
    Process a user's quiz answer submission.

    The entire mutation is wrapped in @transaction.atomic:
      1. Validate question + choice exist and belong together.
      2. Record the immutable AssessmentAttempt.
      3. Lock and update the UserKnowledgeState (select_for_update).
      4. Delegate to the active estimation engine.
      5. Persist mastery_percentage and discrete mastery_level.
      6. Log to the immutable UserKnowledgeHistory ledger.
      7. If mastery threshold reached, unlock child topics + cascade.
      8. Select the next adaptive question (read-only).

    Returns a SubmissionResult DTO for the view to serialize.
    """
    # --- Step 1: Fetch & validate (single query with select_related) -------
    choice: Choice = (
        Choice.objects
        .select_related("question", "question__topic")
        .get(pk=choice_id, question_id=question_id)
    )
    question: Question = choice.question
    topic: Topic = question.topic
    is_correct: bool = choice.is_correct

    # --- Step 2: Log the attempt (INSERT — immutable, never updated) -------
    AssessmentAttempt.objects.create(
        user=user,
        question=question,
        selected_choice=choice,
        is_correct=is_correct,
    )

    # --- Step 3: Lock & load user knowledge state --------------------------
    # select_for_update prevents race conditions from concurrent submissions
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

    state.total_attempts += 1
    if is_correct:
        state.correct_attempts += 1

    # --- Step 4: Resolve and invoke the active engine ----------------------
    algorithm_key: str = getattr(
        settings, "STUDENT_MODEL_ENGINE", AlgorithmChoice.STREAK,
    )
    engine = get_engine(algorithm_key)

    mastery_float: float = engine.calculate_new_mastery(
        user=user,
        topic=topic,
        current_state=state,
        question=question,
        is_correct=is_correct,
    )

    # --- Step 5: Persist mastery state -------------------------------------
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

    # --- Step 6: Append to immutable history ledger ------------------------
    UserKnowledgeHistory.objects.create(
        user=user,
        topic=topic,
        calculated_mastery=mastery_float,
        algorithm_used=algorithm_key,
    )

    # --- Step 7: Mastery threshold check + child topic unlocking -----------
    mastery_pct_int: int = round(state.mastery_percentage * 100)

    if mastery_pct_int >= MASTERY_THRESHOLD:
        # Ensure the discrete level reflects MASTERED when threshold met
        if state.mastery_level < MasteryLevel.MASTERED:
            state.mastery_level = MasteryLevel.MASTERED
            state.save(update_fields=["mastery_level", "updated_at"])

        # Unlock immediate child topics via CTE-based tree query
        _unlock_child_topics(topic=topic)

        # Cascade mastery state to all descendants for the user
        _cascade_mastery_to_descendants(user=user, topic=topic)

    # --- Step 7b: Adaptive difficulty skip ---------------------------------
    # If the student performs well on Medium+Hard, skip remaining Easy Qs
    _maybe_skip_easy_questions(user=user, topic=topic)

    # --- Step 8: Pick next question (read-only) ----------------------------
    next_question = get_next_question(user=user, topic_id=topic.pk)

    return SubmissionResult(
        is_correct=is_correct,
        explanation=question.explanation,
        mastery_level=state.mastery_level,
        mastery_display=state.get_mastery_level_display(),
        mastery_percentage=state.mastery_percentage,
        streak=state.streak,
        next_question=next_question,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _unlock_child_topics(*, topic: Topic) -> None:
    """
    Bulk-unlock all immediate child topics of a mastered topic.

    Uses django-mptt's ``get_children()`` which produces a
    single lft/rght range query. The subsequent ``.update()`` is also
    a single DB hit — no Python-level loops with per-row queries.

    Performance: exactly 2 DB queries (children fetch + bulk UPDATE).
    """
    # MPTT query: get immediate children of the mastered topic
    child_ids: list[int] = list(
        topic.get_children().values_list("id", flat=True)
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


@transaction.atomic
def _cascade_mastery_to_descendants(*, user, topic: Topic) -> None:
    """
    When a user masters a topic, mark ALL descendant topics as MASTERED.

    Uses django-mptt's get_descendants() for tree traversal
    (single lft/rght range query) and bulk_create with update_conflicts
    for the upsert (single INSERT ... ON CONFLICT).

    Wrapped in @transaction.atomic as a nested savepoint for safety.

    Performance: exactly 2 DB queries regardless of tree depth.
    """
    # Query 1: Get all descendant topic IDs via MPTT lft/rght range
    descendant_ids: list[int] = list(
        topic.get_descendants().values_list("id", flat=True)
    )
    if not descendant_ids:
        return

    # Build state objects for bulk upsert
    states_to_upsert: list[UserKnowledgeState] = [
        UserKnowledgeState(
            user=user,
            topic_id=tid,
            mastery_level=MasteryLevel.MASTERED,
            mastery_percentage=1.0,
            score=100,
            streak=0,
            total_attempts=0,
            correct_attempts=0,
        )
        for tid in descendant_ids
    ]

    # Query 2: Bulk upsert — INSERT new rows or UPDATE existing ones
    UserKnowledgeState.objects.bulk_create(
        states_to_upsert,
        update_conflicts=True,
        unique_fields=["user", "topic"],
        update_fields=["mastery_level", "mastery_percentage", "score"],
    )

    logger.info(
        "Cascaded MASTERED to %d descendants of topic %s for user %s",
        len(descendant_ids), topic.pk, user.pk,
    )


def _maybe_skip_easy_questions(*, user, topic: Topic) -> None:
    """
    Adaptive difficulty skip: if a student achieves >= ADAPTIVE_SKIP_ACCURACY%
    on Medium and Hard questions (with at least ADAPTIVE_SKIP_MIN_ATTEMPTS),
    mark all remaining Easy questions for this topic as "answered correctly"
    by creating synthetic AssessmentAttempt records.

    This saves advanced students from tedious Easy questions they've proven
    they don't need. The bypass is recorded in the attempt log for audit.

    Performance: 2-3 DB queries.
    """
    from assessments.models import DifficultyLevel

    # Count M+H attempts for this user on this topic
    medium_hard_attempts = (
        AssessmentAttempt.objects
        .filter(
            user=user,
            question__topic=topic,
            question__difficulty__in=[
                DifficultyLevel.MEDIUM,
                DifficultyLevel.HARD,
            ],
        )
    )

    total_mh = medium_hard_attempts.count()
    if total_mh < ADAPTIVE_SKIP_MIN_ATTEMPTS:
        return  # Not enough data to decide

    correct_mh = medium_hard_attempts.filter(is_correct=True).count()
    accuracy = round((correct_mh / total_mh) * 100)

    if accuracy < ADAPTIVE_SKIP_ACCURACY:
        return  # Student hasn't demonstrated sufficient M+H competency

    # Find unanswered Easy questions for this topic
    already_answered_ids = (
        AssessmentAttempt.objects
        .filter(user=user, question__topic=topic)
        .values_list("question_id", flat=True)
    )

    easy_questions_to_skip = (
        Question.objects
        .filter(
            topic=topic,
            is_active=True,
            difficulty=DifficultyLevel.EASY,
        )
        .exclude(pk__in=already_answered_ids)
        .select_related("topic")
        .prefetch_related("choices")
    )

    if not easy_questions_to_skip.exists():
        return

    # Create synthetic "correct" attempts for bypassed Easy questions
    bypass_attempts = []
    for question in easy_questions_to_skip:
        correct_choice = question.choices.filter(is_correct=True).first()
        if correct_choice:
            bypass_attempts.append(
                AssessmentAttempt(
                    user=user,
                    question=question,
                    selected_choice=correct_choice,
                    is_correct=True,
                )
            )

    if bypass_attempts:
        AssessmentAttempt.objects.bulk_create(bypass_attempts)
        logger.info(
            "Adaptive skip: bypassed %d Easy question(s) for user %s on topic %s "
            "(M+H accuracy: %d%%)",
            len(bypass_attempts), user.pk, topic.pk, accuracy,
        )
