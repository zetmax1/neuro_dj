"""
assessments/services/question_selection.py — Adaptive question selection.

Extracted from the original monolithic services.py. Read-only module.
"""

from __future__ import annotations

from typing import Optional

from django.conf import settings
from django.db.models import F, QuerySet
from django.db.models.functions import Abs

from curriculum.models import Topic

from assessments.models import (
    AlgorithmChoice,
    AssessmentAttempt,
    DifficultyLevel,
    MasteryLevel,
    Question,
    UserAbility,
    UserKnowledgeState,
)

MASTERY_TO_DIFFICULTY: dict[int, int] = {
    MasteryLevel.NOT_STARTED: DifficultyLevel.EASY,
    MasteryLevel.BEGINNER: DifficultyLevel.EASY,
    MasteryLevel.INTERMEDIATE: DifficultyLevel.MEDIUM,
    MasteryLevel.ADVANCED: DifficultyLevel.HARD,
    MasteryLevel.MASTERED: DifficultyLevel.HARD,
}


def get_next_question(*, user, topic_id: int) -> Optional[Question]:
    """
    Select the next adaptive question for a user on a topic.

    If the active engine is 'irt' or 'hybrid_bkt_irt', selects the question whose
    `irt_difficulty` is closest to the user's current `theta` (maximizing IRT information).
    Otherwise, falls back to discrete 3-bucket difficulty matching.
    """
    topic: Topic = Topic.objects.get(pk=topic_id)
    topic_ids: list[int] = list(topic.get_descendants(include_self=True).values_list("id", flat=True))

    answered_correctly_ids: QuerySet = (
        AssessmentAttempt.objects
        .filter(user=user, is_correct=True, question__topic_id__in=topic_ids)
        .values_list("question_id", flat=True)
    )

    base_qs: QuerySet[Question] = (
        Question.objects
        .filter(topic_id__in=topic_ids, is_active=True)
        .exclude(pk__in=answered_correctly_ids)
        .select_related("topic")
        .prefetch_related("choices")
    )


    active_engine: str = getattr(settings, "STUDENT_MODEL_ENGINE", AlgorithmChoice.BKT)

    # IRT / Hybrid continuous selection: pick question closest to user's theta
    if active_engine in (AlgorithmChoice.IRT, AlgorithmChoice.HYBRID_BKT_IRT):
        ability_obj = UserAbility.objects.filter(user=user, topic=topic).first()
        theta: float = ability_obj.theta if ability_obj else 0.0

        candidate = (
            base_qs.annotate(diff_dist=Abs(F("irt_difficulty") - theta))
            .order_by("diff_dist")
            .first()
        )
        if candidate:
            return candidate
        return base_qs.first()

    # Discrete 3-bucket selection for streak and plain bkt
    try:
        state = UserKnowledgeState.objects.get(user=user, topic=topic)
        mastery_level: int = state.mastery_level
    except UserKnowledgeState.DoesNotExist:
        mastery_level = MasteryLevel.NOT_STARTED

    target_difficulty: int = MASTERY_TO_DIFFICULTY.get(
        mastery_level, DifficultyLevel.EASY
    )

    return base_qs.order_by("difficulty").first()


def get_stratified_test_questions(*, topic_id: int) -> list[Question]:
    """
    Selects a stratified random sample of test questions for a topic.
    Target difficulty distribution for N questions (e.g. 10):
      - Easy (40%): 4 questions
      - Medium (30%): 3 questions
      - Hard (30%): 3 questions
    If any difficulty tier has fewer questions available, backfills from remaining pool.
    """
    import random

    topic = Topic.objects.get(pk=topic_id)
    topic_ids = list(topic.get_descendants(include_self=True).values_list("id", flat=True))

    target_total = topic.test_question_count or 10

    # Calculate target counts per difficulty tier
    target_easy = int(round(target_total * 0.40))
    target_med = int(round(target_total * 0.30))
    target_hard = max(0, target_total - target_easy - target_med)

    qs_easy = list(Question.objects.filter(topic_id__in=topic_ids, difficulty=DifficultyLevel.EASY, is_active=True).prefetch_related("choices"))
    qs_med = list(Question.objects.filter(topic_id__in=topic_ids, difficulty=DifficultyLevel.MEDIUM, is_active=True).prefetch_related("choices"))
    qs_hard = list(Question.objects.filter(topic_id__in=topic_ids, difficulty=DifficultyLevel.HARD, is_active=True).prefetch_related("choices"))

    random.shuffle(qs_easy)
    random.shuffle(qs_med)
    random.shuffle(qs_hard)

    selected_easy = qs_easy[:target_easy]
    selected_med = qs_med[:target_med]
    selected_hard = qs_hard[:target_hard]

    selected_ids = {q.id for q in (selected_easy + selected_med + selected_hard)}

    # Pool of remaining questions across all tiers
    remaining = [
        q for q in (qs_easy + qs_med + qs_hard)
        if q.id not in selected_ids
    ]
    random.shuffle(remaining)

    # Backfill if any tier was short of questions
    combined = selected_easy + selected_med + selected_hard
    needed = target_total - len(combined)
    if needed > 0 and remaining:
        combined.extend(remaining[:needed])

    # Sort final question paper by difficulty order (Easy -> Medium -> Hard)
    combined.sort(key=lambda q: (q.difficulty, q.id))

    return combined

