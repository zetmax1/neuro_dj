"""
assessments/services/ledger.py — the only writer of the answer ledger (D10).

Every ``AssessmentAttempt`` row is created by ``record_attempt``. It assigns
``attempt_no`` under a per-(learner, topic) transaction lock, snapshots the
topic and course, and stores the model quantities the engine used. Nothing
else may create, back-date or rewrite ledger rows; a test scans the code base
to keep it that way.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Max
from django.utils import timezone

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    Question,
    TestSessionResult,
)

# Namespace (first key) of the two-key advisory locks taken per (learner,
# topic). The single-key lock space stays free for the knowledge-base lock.
LEDGER_LOCK_NAMESPACE: int = 1

# Only synthetic rows may carry a caller-supplied timestamp.
_BACKDATABLE_SOURCES = frozenset({AttemptSource.SEED, AttemptSource.SIMULATED})
_SESSION_SOURCES = frozenset({AttemptSource.TEST_SESSION, AttemptSource.REVIEW_REPEAT})
# Learner-facing sources that D25 may downgrade to review_repeat.
_REVIEWABLE_SOURCES = frozenset({AttemptSource.ADAPTIVE, AttemptSource.TEST_SESSION})


@dataclass(frozen=True)
class ModelTrace:
    """Quantities the student model used for one answer (all optional)."""
    p_before: float | None = None
    p_hat: float | None = None
    p_after: float | None = None
    guess_used: float | None = None
    slip_used: float | None = None
    theta_before: float | None = None
    theta_after: float | None = None
    b_before: float | None = None
    b_after: float | None = None
    readiness_score: float | None = None
    was_ready: bool | None = None
    engine_version: str = ""
    kb_version: int | None = None


def _require_transaction() -> None:
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Ledger writes must run inside transaction.atomic().")


def lock_learner_topics(user_id: int, topic_ids: Iterable[int]) -> None:
    """
    Serialise ledger writes per (learner, topic) until the transaction ends.

    Locks are taken in ascending topic order so that callers locking several
    topics cannot deadlock. Callers that also lock state rows take these
    advisory locks first. Re-locking a key already held is a no-op.
    """
    _require_transaction()
    if connection.vendor != "postgresql":
        return  # SQLite serialises all writers on the database file
    with connection.cursor() as cursor:
        for topic_id in sorted(set(topic_ids)):
            cursor.execute(
                "SELECT pg_advisory_xact_lock(%s, hashtext(%s))",
                [LEDGER_LOCK_NAMESPACE, f"{user_id}:{topic_id}"],
            )


def review_window() -> timedelta:
    return timedelta(hours=settings.THESIS_MODEL["REVIEW_REPEAT_HOURS"])


def answered_recently(*, user, question: Question, at: datetime | None = None) -> bool:
    """Whether the learner already answered this exact question within the review window."""
    cutoff = (at or timezone.now()) - review_window()
    return AssessmentAttempt.objects.filter(
        user=user, question=question, answered_at__gte=cutoff,
    ).exists()


def classify_source(*, user, question: Question, requested: str) -> str:
    """
    D25: an adaptive or test-session answer to a question the learner answered
    within the review window is a ``review_repeat``. It is logged but never
    updates P(L) and never enters the experiments. Call under the topic lock.
    """
    if requested in _REVIEWABLE_SOURCES and answered_recently(user=user, question=question):
        return AttemptSource.REVIEW_REPEAT
    return requested


def course_of(topic):
    """Course of a topic: the root of its tree (D2)."""
    return topic.get_root()


def record_attempt(
    *,
    user,
    choice: Choice,
    source: str,
    trace: ModelTrace | None = None,
    session: TestSessionResult | None = None,
    answered_at: datetime | None = None,
) -> AssessmentAttempt:
    """
    Append one answer to the ledger and return the new row.

    ``is_correct`` is taken from the choice, ``topic``/``course`` from the
    question at this moment, and ``attempt_no`` is the next number for
    (user, topic). Must run inside the caller's transaction so the row commits
    or rolls back together with the state update it belongs to.
    """
    _require_transaction()
    if source not in AttemptSource.values or source == AttemptSource.LEGACY:
        raise ValueError(f"record_attempt cannot write source={source!r}.")
    if answered_at is not None and source not in _BACKDATABLE_SOURCES:
        raise ValueError("Only seed and simulated answers may be back-dated.")
    if source == AttemptSource.TEST_SESSION and session is None:
        raise ValueError("Test-session answers must reference their session.")
    if session is not None and source not in _SESSION_SOURCES:
        raise ValueError(f"source={source!r} answers do not belong to a test session.")
    if trace is not None and source == AttemptSource.REVIEW_REPEAT:
        raise ValueError("review_repeat answers are not model observations.")

    question: Question = choice.question
    topic = question.topic
    lock_learner_topics(user.pk, [topic.pk])
    last_no = (
        AssessmentAttempt.objects
        .filter(user=user, topic=topic)
        .aggregate(last=Max("attempt_no"))["last"]
    ) or 0

    return AssessmentAttempt.objects.create(
        user=user,
        question=question,
        selected_choice=choice,
        is_correct=choice.is_correct,
        topic=topic,
        course=course_of(topic),
        attempt_no=last_no + 1,
        source=source,
        session=session,
        answered_at=answered_at or timezone.now(),
        **asdict(trace or ModelTrace()),
    )
