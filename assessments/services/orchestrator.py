"""
assessments/services/orchestrator.py — Execution Orchestrator.

Coordinates the full answer-submission lifecycle inside a single
@transaction.atomic block:

    1. Validate question + choice (archived topics are not answerable).
    2. Lock the learner's (user, topic) ledger key.
    3. Refuse a closed topic (TY1-TY4): the readiness service is the only
       authority on that, and the view turns the refusal into a 403.
    4. Classify the answer: a repeat of a question answered within the
       review window is logged as ``review_repeat`` and changes nothing (D25).
    5. Record readiness as it stood at answer time — r_s(w) and R_s(w).
    6. Run Algorithm 2.4 (``student_model.apply_answer``), which locks the
       ability row and the question row and moves P(L), θ and b_q.
    7. Run Algorithm 2.3 (``readiness.apply_answer``): recompute M, and when
       it changed, move the counters of the immediate successors.
    8. Append the answer to the ledger with everything the model used, and
       link the history entry to it.
    9. Select the next adaptive question.

The order inside step 6 is fixed by 3.3: P(G) and P(S) come from the θ and b
in force when the question was asked, p̂ is recorded as predicted, and Elo
moves θ and b only afterwards. Step 7 is step 7 of Algorithm 2.4.

The orchestrator never writes anything for topics or questions the learner
did not answer (D8): the descendant cascade and the easy-question skip that
fabricated answers were removed in stage 1, and the global unlock cascade
was removed in stage 4 along with ``Topic.is_unlocked``.

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
    Question,
    StudentTopicState,
    UserKnowledgeHistory,
)
from assessments.services import ledger, readiness, student_model
from assessments.services.question_selection import get_next_question

logger = logging.getLogger(__name__)

# Sources ``process_submission`` accepts. Seeds and the simulator go through
# the same engine path but are labelled so experiments can exclude them (D13).
SUBMISSION_SOURCES: frozenset[str] = frozenset({
    AttemptSource.ADAPTIVE,
    AttemptSource.SEED,
    AttemptSource.SIMULATED,
})


class TopicClosed(Exception):
    """
    The learner has unmet prerequisites for this topic (TY1-TY4).

    ``payload`` is the 403 body: ``{"missing": [{topic_id, name, p_mastery}]}``.
    """

    def __init__(self, blocked: readiness.Blocked) -> None:
        super().__init__(f"Topic {blocked.topic_id} is closed for this learner.")
        self.blocked = blocked

    def payload(self) -> dict:
        return self.blocked.payload()


# ---------------------------------------------------------------------------
# Data Transfer Object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubmissionResult:
    """
    Returned to the view layer after processing an answer.

    The names are the ones every student-facing endpoint uses: ``p_mastery``,
    ``accuracy`` and ``status`` (3.4). The mixed-scale ``mastery_percentage``
    and the discrete ``mastery_level`` are gone.
    """
    is_correct: bool
    explanation: str
    p_mastery: float
    status: str
    mastered: bool
    accuracy: float
    attempts: int
    opened_topics: tuple[int, ...]
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
    Everything runs in one transaction: the ledger row, the state update, the
    readiness propagation and the history entry commit or roll back together.

    Raises ``TopicClosed`` when the learner has unmet prerequisites.
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
    # prerequisites of P(L0), the readiness counters and the ledger's
    # kb_version all come from it, so they cannot disagree with each other.
    snapshot = get_snapshot()

    # --- Step 2: Serialise this learner's answers on this topic ------------
    # The advisory lock is taken before the state row lock (same order as the
    # test-session path), so classification, attempt_no and the state update
    # all see one consistent ledger.
    ledger.lock_learner_topics(user.pk, [topic.pk])

    # --- Step 3: a closed topic is not answerable --------------------------
    states = readiness.states_for(user=user, snapshot=snapshot)
    blocked = readiness.check_open(user=user, topic_id=topic.pk, snapshot=snapshot)
    if blocked is not None:
        raise TopicClosed(blocked)

    # --- Step 4: D25 — a repeat within the review window updates nothing ---
    source = ledger.classify_source(user=user, question=question, requested=source)
    if source == AttemptSource.REVIEW_REPEAT:
        attempt = ledger.record_attempt(user=user, choice=choice, source=source)
        state = states[topic.pk]
        return SubmissionResult(
            is_correct=is_correct,
            explanation=question.explanation,
            p_mastery=state.p_mastery,
            status=state.status,
            mastered=state.mastered_flag,
            accuracy=state.accuracy,
            attempts=state.attempts,
            opened_topics=(),
            next_question=get_next_question(user=user, topic_id=topic.pk),
            source=attempt.source,
            attempt_id=attempt.pk,
            attempt_no=attempt.attempt_no,
        )

    # --- Step 5: readiness as it stood when the question was answered ------
    was = readiness.readiness_at(topic_id=topic.pk, states=states, snapshot=snapshot)

    # --- Step 6: Algorithm 2.4 ---------------------------------------------
    applied = student_model.apply_answer(
        user=user,
        topic=topic,
        course_id=snapshot.root_of(topic.pk),
        question=question,
        is_correct=is_correct,
        snapshot=snapshot,
    )

    # --- Step 7: Algorithm 2.3 ---------------------------------------------
    readiness_result = readiness.apply_answer(
        user=user,
        topic_id=topic.pk,
        p_mastery=applied.mastery,
        is_correct=is_correct,
        snapshot=snapshot,
        answered_at=answered_at,
    )
    state = readiness_result.state

    # --- Step 8: Append to the ledger and the history ----------------------
    attempt = ledger.record_attempt(
        user=user,
        choice=choice,
        source=source,
        trace=replace(
            applied.trace,
            kb_version=snapshot.version,
            readiness_score=was.score,
            was_ready=was.was_ready,
        ),
        answered_at=answered_at,
    )
    UserKnowledgeHistory.objects.create(
        user=user,
        topic=topic,
        calculated_mastery=applied.mastery,
        algorithm_used=AlgorithmChoice.THESIS_HYBRID,
        attempt=attempt,
        created_at=attempt.answered_at,
    )

    if readiness_result.opened:
        logger.info(
            "Learner %s mastered topic %s; opened %s",
            user.pk, topic.pk, readiness_result.opened,
        )

    # --- Step 9: Pick next question (read-only) ----------------------------
    next_question = get_next_question(user=user, topic_id=topic.pk)

    return SubmissionResult(
        is_correct=is_correct,
        explanation=question.explanation,
        p_mastery=state.p_mastery,
        status=state.status,
        mastered=state.mastered_flag,
        accuracy=state.accuracy,
        attempts=state.attempts,
        opened_topics=readiness_result.opened,
        next_question=next_question,
        source=attempt.source,
        attempt_id=attempt.pk,
        attempt_no=attempt.attempt_no,
    )


def state_of(*, user, topic_id: int) -> StudentTopicState:
    """The learner's state on one topic, materialised if it does not exist."""
    return readiness.states_for(user=user)[topic_id]
