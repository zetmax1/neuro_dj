"""
assessments/services/orchestrator.py — Execution Orchestrator.

Coordinates the full answer-submission lifecycle inside a single
@transaction.atomic block:

    1. Validate question + choice (archived topics are not answerable).
    2. Lock the learner's (user, topic) ledger key, then the state row.
    3. Classify the answer: a repeat of a question answered within the
       review window is logged as ``review_repeat`` and changes nothing (D25).
    4. Run Algorithm 2.4 (``student_model.apply_answer``), which locks the
       ability row and the question row and moves P(L), θ and b_q.
    5. Persist mastery_percentage + discrete mastery_level on the state row.
    6. Append the answer to the ledger (``ledger.record_attempt``) together
       with the quantities the engine used, and link the history entry to it.
    7. If the legacy threshold is reached, set the global unlock flag of the
       child topics (removed with the readiness service in stage 4).
    8. Select the next adaptive question.

The order inside step 4 is fixed by 3.3 and is the engine's own concern: P(G)
and P(S) come from the θ and b in force when the question was asked, p̂ is
recorded as predicted, and Elo moves θ and b only afterwards.

The orchestrator never writes anything for topics or questions the learner
did not answer (D8): the descendant cascade and the easy-question skip that
fabricated answers were removed in stage 1.

Engine:
    ``thesis_hybrid`` is the only engine (D34). The classical variants are
    reproduced by its ablation flags (``settings.THESIS_FLAGS``), so there is
    nothing to resolve at runtime.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

from django.db import transaction

from curriculum.models import Topic
from curriculum.services.graph import get_snapshot

from assessments.models import (
    AlgorithmChoice,
    AttemptSource,
    Choice,
    MasteryLevel,
    Question,
    UserKnowledgeHistory,
    UserKnowledgeState,
)
from assessments.services import ledger, student_model
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

    # One snapshot for the whole submission: the course of the ability row, the
    # prerequisites of P(L0) and the ledger's kb_version all come from it, so
    # they cannot disagree with each other.
    snapshot = get_snapshot()

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

    # --- Step 5: Algorithm 2.4 ---------------------------------------------
    # The engine reads P(L), θ and b_q as they stand now and writes the new θ
    # and b_q itself; the counters below move only afterwards.
    applied = student_model.apply_answer(
        user=user,
        topic=topic,
        course_id=snapshot.root_of(topic.pk),
        question=question,
        is_correct=is_correct,
        snapshot=snapshot,
    )
    mastery_float: float = applied.mastery

    # --- Step 6: Persist mastery state -------------------------------------
    state.total_attempts += 1
    if is_correct:
        state.correct_attempts += 1
        state.streak += 1
    else:
        state.streak = 0

    state.mastery_level = student_model.mastery_level_for(mastery_float)
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
        trace=replace(applied.trace, kb_version=snapshot.version),
        answered_at=answered_at,
    )
    UserKnowledgeHistory.objects.create(
        user=user,
        topic=topic,
        calculated_mastery=mastery_float,
        algorithm_used=AlgorithmChoice.THESIS_HYBRID,
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
