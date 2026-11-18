"""
assessments/services/question_selection.py — Adaptive question selection.

Extracted from the original monolithic services.py. Read-only module.
"""

from __future__ import annotations

from typing import Optional

from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import Exists, F, OuterRef, QuerySet
from django.db.models.functions import Abs, JSONObject
from django.utils import timezone

from curriculum.models import Topic
from curriculum.services.graph import KBSnapshot, get_snapshot

from assessments.models import (
    AssessmentAttempt,
    Choice,
    DifficultyLevel,
    Question,
    UserAbility,
)
from assessments.services.ledger import review_window


def ability_of(*, user, course_id: int) -> float:
    """
    θ_s for this learner in this course, 0 when they have never answered.

    Selection and the Elo update read the same row (D33), so the question the
    learner is given is the one the model will score them against.
    """
    theta = (
        UserAbility.objects
        .filter(user=user, course_id=course_id)
        .values_list("theta", flat=True)
        .first()
    )
    return 0.0 if theta is None else theta


def get_next_question(
    *,
    user,
    topic_id: int,
    topic: Topic | None = None,
    snapshot: KBSnapshot | None = None,
    theta: float | None = None,
) -> Optional[Question]:
    """
    The next question for this learner on this topic: the one whose difficulty
    is closest to their ability, ``|b_q − θ_s|``, ties broken by id.

    θ_s is the learner's ability in the **course** that holds the topic, which
    is the same θ the Elo step updates — the inconsistency of the removed
    per-topic lookup is gone.

    Questions the learner answered within the review window come last: a
    repeat is logged as review_repeat and does not update P(L) (D25), so it is
    served only when nothing else is left. Questions already answered
    correctly are not served again. Archived topics are not answerable.

    The answer path already holds the active ``topic``, the ``snapshot`` and the
    learner's ``theta`` it has just written, and passes them in; the values are
    the ones this function would read.
    """
    if topic is None:
        topic = Topic.objects.get(pk=topic_id, is_archived=False)
    snapshot = snapshot or get_snapshot()
    # Questions belong to topics only (Y4): the candidates are Leaves(n).
    topic_ids: list[int] = sorted(snapshot.leaves_of(topic.pk))

    answered_correctly_ids: QuerySet = (
        AssessmentAttempt.objects
        .filter(user=user, is_correct=True, question__topic_id__in=topic_ids)
        .values_list("question_id", flat=True)
    )

    answered_recently = AssessmentAttempt.objects.filter(
        user=user,
        question=OuterRef("pk"),
        answered_at__gte=timezone.now() - review_window(),
    )

    if theta is None:
        theta = ability_of(user=user, course_id=snapshot.root_of(topic.pk))

    question = (
        Question.objects
        .filter(topic_id__in=topic_ids, is_active=True)
        .exclude(pk__in=answered_correctly_ids)
        .annotate(answered_recently=Exists(answered_recently))
        .annotate(information=Abs(F("irt_difficulty") - theta))
        .annotate(choice_rows=ArraySubquery(
            Choice.objects.filter(question=OuterRef("pk")).order_by("id")
            .values(row=JSONObject(**{name: name for name in CHOICE_COLUMNS}))
        ))
        .select_related("topic")
        .order_by("answered_recently", "information", "id")
        .first()
    )
    if question is not None:
        _prefetch_choices(question)
    return question


# The choices come with the question as a JSON array (D66a) instead of a
# second, prefetching query; they are the rows prefetch_related("choices")
# loaded, in its order (Choice.Meta.ordering = id), and are put where it
# put them, so ``question.choices.all()`` reads no database.
CHOICE_COLUMNS: tuple[str, ...] = tuple(f.attname for f in Choice._meta.concrete_fields)


def _prefetch_choices(question: Question) -> None:
    choices = [
        Choice.from_db(question._state.db, CHOICE_COLUMNS, [row[name] for name in CHOICE_COLUMNS])
        for row in question.choice_rows
    ]
    cached = Choice.objects.filter(question=question)
    cached._result_cache = choices
    cached._prefetch_done = True
    question._prefetched_objects_cache = {"choices": cached}


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

    topic = Topic.objects.get(pk=topic_id, is_archived=False)
    topic_ids = sorted(get_snapshot().leaves_of(topic.pk))

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

