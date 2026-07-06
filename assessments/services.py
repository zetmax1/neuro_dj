"""
assessments/services.py — Adaptive learning business logic.

All "fat" logic lives here, not in views. Views only route HTTP and serialize.

Cross-app access:
  This module imports `curriculum.models.Topic` directly — this is the
  ALLOWED direction (assessments → curriculum). The reverse direction
  (curriculum → assessments) is never permitted.

Transaction strategy:
  - process_submission() wraps the entire state mutation (attempt log,
    state update, mastery cascade) in a single transaction.atomic() block.
  - select_for_update() is used on the UserKnowledgeState read to prevent
    race conditions from concurrent submissions on the same user+topic.
  - _cascade_mastery_to_descendants() runs inside the same transaction,
    using bulk_create with update_conflicts for an atomic upsert.

State-machine rules:
  1. Correct answer → increment streak.
     - streak >= 3 on HARD difficulty → promote to MASTERED and cascade
       mastery to all descendant topics (via tree_queries get_descendants).
     - streak >= 2 on current difficulty → promote mastery_level by 1.
  2. Incorrect answer → reset streak to 0, do NOT demote.
  3. Next question selection → pick from the topic matching the user's
     current mastery difficulty, excluding recently answered questions.

Performance guarantees:
  - All bulk state updates use bulk_create / bulk_update (single DB hit).
  - No queries inside loops.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from django.db import transaction
from django.db.models import QuerySet

# One-way dependency: assessments → curriculum (ALLOWED)
from curriculum.models import Topic

from assessments.models import (
    AssessmentAttempt,
    Choice,
    DifficultyLevel,
    MasteryLevel,
    Question,
    UserKnowledgeState,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — tuneable thresholds
# ---------------------------------------------------------------------------
STREAK_TO_PROMOTE: int = 2        # Consecutive correct answers to advance
STREAK_TO_MASTER_HARD: int = 3    # Streak on HARD to trigger mastery cascade

# Mapping: mastery level → question difficulty the engine should serve
MASTERY_TO_DIFFICULTY: dict[int, int] = {
    MasteryLevel.NOT_STARTED: DifficultyLevel.EASY,
    MasteryLevel.BEGINNER: DifficultyLevel.EASY,
    MasteryLevel.INTERMEDIATE: DifficultyLevel.MEDIUM,
    MasteryLevel.ADVANCED: DifficultyLevel.HARD,
    MasteryLevel.MASTERED: DifficultyLevel.HARD,
}


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubmissionResult:
    """Returned to the view layer after processing an answer."""
    is_correct: bool
    explanation: str
    mastery_level: int
    mastery_display: str
    streak: int
    next_question: Optional[Question]


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
      4. If mastery threshold reached, cascade via descendants.
      5. Select the next adaptive question (read-only, outside lock).

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

    # --- Step 3: Lock & update user knowledge state ------------------------
    # select_for_update prevents race conditions from concurrent submissions
    state, _created = UserKnowledgeState.objects.select_for_update().get_or_create(
        user=user,
        topic=topic,
        defaults={
            "mastery_level": MasteryLevel.NOT_STARTED,
            "score": 0,
            "total_attempts": 0,
            "correct_attempts": 0,
            "streak": 0,
        },
    )

    state.total_attempts += 1

    if is_correct:
        state.correct_attempts += 1
        state.streak += 1
        _maybe_promote(state, question.difficulty)
    else:
        state.streak = 0

    # Recalculate running accuracy
    state.score = round(
        (state.correct_attempts / state.total_attempts) * 100
    )
    state.save(update_fields=[
        "mastery_level", "score", "total_attempts",
        "correct_attempts", "streak", "updated_at",
    ])

    # --- Step 4: Cascade mastery to descendants if threshold met -----------
    if (
        state.mastery_level >= MasteryLevel.MASTERED
        and is_correct
    ):
        _cascade_mastery_to_descendants(user=user, topic=topic)

    # --- Step 5: Pick next question (read-only) ----------------------------
    next_question = get_next_question(user=user, topic_id=topic.pk)

    return SubmissionResult(
        is_correct=is_correct,
        explanation=question.explanation,
        mastery_level=state.mastery_level,
        mastery_display=state.get_mastery_level_display(),
        streak=state.streak,
        next_question=next_question,
    )


def get_next_question(*, user, topic_id: int) -> Optional[Question]:
    """
    Public API: Select the next adaptive question for a user on a topic.

    Algorithm:
      1. Look up the user's current mastery level for the topic.
      2. Map mastery → target difficulty.
      3. Exclude questions already answered correctly by this user.
      4. Return the first unanswered question at the target difficulty.
      5. Fallback: any unanswered active question on this topic.

    The returned Question has `topic` pre-loaded (select_related) and
    `choices` pre-loaded (prefetch_related) so the serializer can nest
    them without additional queries.

    Performance: 2-3 queries total (state lookup + question + prefetch).
    """
    topic: Topic = Topic.objects.get(pk=topic_id)

    # Get the user's current mastery for this topic
    try:
        state = UserKnowledgeState.objects.get(user=user, topic=topic)
        mastery_level: int = state.mastery_level
    except UserKnowledgeState.DoesNotExist:
        mastery_level = MasteryLevel.NOT_STARTED

    target_difficulty: int = MASTERY_TO_DIFFICULTY.get(
        mastery_level, DifficultyLevel.EASY
    )

    # Subquery: IDs of questions user already answered correctly
    answered_correctly_ids: QuerySet = (
        AssessmentAttempt.objects
        .filter(user=user, is_correct=True, question__topic=topic)
        .values_list("question_id", flat=True)
    )

    # Base queryset — select_related + prefetch_related for serializer
    base_qs: QuerySet[Question] = (
        Question.objects
        .filter(topic=topic, is_active=True)
        .exclude(pk__in=answered_correctly_ids)
        .select_related("topic")
        .prefetch_related("choices")
    )

    # Primary attempt: match target difficulty
    candidate: Optional[Question] = (
        base_qs.filter(difficulty=target_difficulty).first()
    )
    if candidate:
        return candidate

    # Fallback: any unanswered active question on this topic
    return base_qs.order_by("difficulty").first()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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


@transaction.atomic
def _cascade_mastery_to_descendants(*, user, topic: Topic) -> None:
    """
    When a user masters a topic, mark ALL descendant topics as MASTERED.

    Uses django-tree-queries' get_descendants() for the tree traversal
    (single recursive CTE query) and bulk_create with update_conflicts
    for the upsert (single INSERT ... ON CONFLICT).

    Wrapped in @transaction.atomic as a nested savepoint for safety.

    Performance: exactly 2 DB queries regardless of tree depth.
    """
    # Query 1: Get all descendant topic IDs via recursive CTE
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
        update_fields=["mastery_level", "score"],
    )

    logger.info(
        "Cascaded MASTERED to %d descendants of topic %s for user %s",
        len(descendant_ids), topic.pk, user.pk,
    )
