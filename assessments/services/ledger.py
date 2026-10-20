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
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Max
from django.utils import timezone

from curriculum.services.graph import KBSnapshot, get_snapshot

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
class HistoryEntry:
    """The ``UserKnowledgeHistory`` row written with a counted answer."""
    calculated_mastery: float
    algorithm_used: str


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


def classify_source(*, user, question: Question, requested: str, recent: bool | None = None) -> str:
    """
    D25: an adaptive or test-session answer to a question the learner answered
    within the review window is a ``review_repeat``. It is logged but never
    updates P(L) and never enters the experiments. Call under the topic lock.

    ``recent`` is ``answered_recently`` already read under that lock
    (``student_model.answer_context``, D66a); None reads it here.
    """
    if requested not in _REVIEWABLE_SOURCES:
        return requested
    if recent is None:
        recent = answered_recently(user=user, question=question)
    return AttemptSource.REVIEW_REPEAT if recent else requested


def record_attempt(
    *,
    user,
    choice: Choice,
    source: str,
    trace: ModelTrace | None = None,
    session: TestSessionResult | None = None,
    answered_at: datetime | None = None,
    snapshot: KBSnapshot | None = None,
    lock_held: bool = False,
    last_attempt_no: int | None = None,
    history: HistoryEntry | None = None,
) -> AssessmentAttempt:
    """
    Append one answer to the ledger and return the new row.

    ``is_correct`` is taken from the choice, ``topic``/``course`` from the
    question at this moment (course = the root of the topic's tree, D2, and
    ``kb_version`` from the KB snapshot), and ``attempt_no`` is the next number for
    (user, topic). Must run inside the caller's transaction so the row commits
    or rolls back together with the state update it belongs to.

    A caller that already holds this (learner, topic) lock in the current
    transaction and has the snapshot the answer was processed under passes
    ``lock_held=True`` and ``snapshot``: the lock is not taken a second time (it
    is held until the transaction ends anyway) and the course comes from the
    same snapshot as everything else the answer recorded. Such a caller may
    also pass ``last_attempt_no``, read under that lock before any write of
    this answer (D66a); the next number is then that plus one.

    ``history`` writes the answer's ``UserKnowledgeHistory`` row in the same
    statement as the ledger row (D66a), with ``created_at`` = ``answered_at``.
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
    if last_attempt_no is not None and not lock_held:
        raise ValueError("last_attempt_no is only valid under a lock the caller holds.")

    question: Question = choice.question
    topic = question.topic
    if not lock_held:
        lock_learner_topics(user.pk, [topic.pk])
    snapshot = snapshot or get_snapshot()
    if topic.pk not in snapshot:
        raise ValueError(f"Topic {topic.pk} is archived or unknown; it cannot be answered.")
    trace = trace or ModelTrace()
    if trace.kb_version is None:
        # The KB version the answer was given under (TY6, experiments).
        trace = replace(trace, kb_version=snapshot.version)
    if last_attempt_no is None:
        last_attempt_no = (
            AssessmentAttempt.objects
            .filter(user=user, topic=topic)
            .aggregate(last=Max("attempt_no"))["last"]
        ) or 0
    last_no = last_attempt_no

    fields = dict(
        user=user,
        question=question,
        selected_choice=choice,
        is_correct=choice.is_correct,
        topic=topic,
        course_id=snapshot.root_of(topic.pk),
        attempt_no=last_no + 1,
        source=source,
        session=session,
        answered_at=answered_at or timezone.now(),
        **asdict(trace),
    )
    if history is None:
        return AssessmentAttempt.objects.create(**fields)
    return _insert_with_history(AssessmentAttempt(**fields), history)


# Raw SQL, because the ORM cannot insert into two tables in one statement
# (D66a): the history row needs the ledger row's id, which a data-modifying
# CTE hands over inside the statement. The column lists are literals (no
# string building); ``ATTEMPT_COLUMNS`` and ``HISTORY_COLUMNS`` are checked
# against the models by a test. ``AssessmentAttempt.save()`` only refuses
# updates, and the table's CHECK and FK constraints apply to this INSERT as
# to any other. This module stays the only writer of the ledger.
ATTEMPT_COLUMNS: tuple[str, ...] = (
    "user_id", "question_id", "selected_choice_id", "is_correct", "answered_at",
    "topic_id", "course_id", "attempt_no", "source", "session_id",
    "p_before", "p_hat", "p_after", "guess_used", "slip_used",
    "theta_before", "theta_after", "b_before", "b_after",
    "readiness_score", "was_ready", "engine_version", "kb_version",
)
HISTORY_COLUMNS: tuple[str, ...] = (
    "user_id", "topic_id", "calculated_mastery", "algorithm_used", "attempt_id", "created_at",
)
INSERT_WITH_HISTORY_SQL = """
WITH attempt AS (
    INSERT INTO assessments_assessmentattempt (
        user_id, question_id, selected_choice_id, is_correct, answered_at,
        topic_id, course_id, attempt_no, source, session_id,
        p_before, p_hat, p_after, guess_used, slip_used,
        theta_before, theta_after, b_before, b_after,
        readiness_score, was_ready, engine_version, kb_version
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s
    )
    RETURNING id, user_id, topic_id, answered_at
)
INSERT INTO assessments_userknowledgehistory (
    user_id, topic_id, calculated_mastery, algorithm_used, attempt_id, created_at
)
SELECT user_id, topic_id, %s, %s, id, answered_at FROM attempt
RETURNING attempt_id
"""


def _insert_with_history(attempt: AssessmentAttempt, history: HistoryEntry) -> AssessmentAttempt:
    """INSERT ``attempt`` and its history row in one statement; return it saved."""
    by_column = {field.column: field for field in AssessmentAttempt._meta.concrete_fields}
    values = [
        by_column[column].get_db_prep_save(by_column[column].pre_save(attempt, True), connection)
        for column in ATTEMPT_COLUMNS
    ]
    with connection.cursor() as cursor:
        cursor.execute(
            INSERT_WITH_HISTORY_SQL,
            [*values, history.calculated_mastery, history.algorithm_used],
        )
        attempt.pk = cursor.fetchone()[0]
    attempt._state.adding = False
    attempt._state.db = connection.alias
    return attempt
