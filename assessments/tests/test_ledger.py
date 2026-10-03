"""
Stage 1: the answer ledger (D8, D10, D25, TM7; audit 4.4, 4.7, 4.9, 6).

- no code path other than the ledger creates AssessmentAttempt rows;
- one submitted answer is exactly one row, attempt_no runs 1, 2, 3, …;
- the engine's quantities are stored, the prior comes from the state row;
- review_repeat answers are logged but change nothing;
- ledger rows cannot be rewritten.
"""

from __future__ import annotations

import re
import threading
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    DifficultyLevel,
    ImmutableLedgerError,
    Question,
    UserAbility,
    UserKnowledgeHistory,
    UserKnowledgeState,
)
from assessments.services import ledger
from assessments.services.engines.bayesian import DEFAULT_P_INIT
from assessments.services.orchestrator import process_submission
from curriculum.models import KnowledgeBaseVersion, Topic
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()

LEDGER_MODULE = Path("assessments/services/ledger.py")
WRITE_PATTERNS = [
    re.compile(r"(?<!class )\bAssessmentAttempt\("),
    re.compile(r"\bAssessmentAttempt\.objects\.(create|bulk_create|get_or_create|update_or_create)\b"),
    re.compile(
        r"\.(attempts|assessment_attempts|course_attempts|selections)"
        r"\.(create|bulk_create|get_or_create|update_or_create)\b"
    ),
]


def _project_python_files():
    root = Path(settings.BASE_DIR)
    skip = {"venv", ".venv", ".git", "migrations", "tests", "node_modules", "backups"}
    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        if skip.intersection(rel.parts) or rel.name == "conftest.py":
            continue
        yield rel, path.read_text(encoding="utf-8")


def test_only_the_ledger_creates_attempts():
    offenders = [
        f"{rel}:{lineno}: {line.strip()}"
        for rel, text in _project_python_files()
        if rel != LEDGER_MODULE
        for lineno, line in enumerate(text.splitlines(), 1)
        if any(p.search(line) for p in WRITE_PATTERNS)
    ]
    assert offenders == []


def test_removed_fabricating_helpers_are_gone():
    from assessments.services import orchestrator

    assert not hasattr(orchestrator, "_maybe_skip_easy_questions")
    assert not hasattr(orchestrator, "_cascade_mastery_to_descendants")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _question(topic, text, difficulty=DifficultyLevel.MEDIUM, b=0.0):
    q = Question.objects.create(topic=topic, text=text, difficulty=difficulty, irt_difficulty=b)
    right = Choice.objects.create(question=q, text="right", is_correct=True)
    wrong = Choice.objects.create(question=q, text="wrong", is_correct=False)
    return q, right, wrong


@pytest.fixture
def student():
    return User.objects.create_user(email="ledger.student@example.org", password=None)


@pytest.fixture
def course_tree():
    course = make_course("Course", slug="course")
    section = make_section("Section", course, slug="section")
    leaf_a = make_topic("Leaf A", section, slug="leaf-a")
    leaf_b = make_topic("Leaf B", section, slug="leaf-b")
    return course, section, leaf_a, leaf_b


def _submit(user, question, choice, **kwargs):
    return process_submission(user=user, question_id=question.pk, choice_id=choice.pk, **kwargs)


# ---------------------------------------------------------------------------
# No fabricated rows (audit probes 4.7 and 4.9)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_easy_skip_probe_writes_only_real_answers(student, course_tree):
    """Audit 4.9: 3 correct M/H answers used to add 4 synthetic Easy rows."""
    _, _, leaf, _ = course_tree
    hard = [_question(leaf, f"H{i}", DifficultyLevel.HARD) for i in range(3)]
    for i in range(4):
        _question(leaf, f"E{i}", DifficultyLevel.EASY)

    for q, right, _ in hard:
        _submit(student, q, right)

    rows = AssessmentAttempt.objects.filter(user=student)
    assert rows.count() == 3
    assert set(rows.values_list("question_id", flat=True)) == {q.pk for q, _, _ in hard}


@pytest.mark.django_db
def test_mastering_a_topic_writes_nothing_for_other_nodes(student, course_tree):
    """
    Audit 4.7: mastering a node used to write P=1.0 with 0 answers to every
    descendant. Since stage 2 only topics hold questions (Y4), so the check is
    that no other node gets a state or an answer.
    """
    course, section, leaf_a, leaf_b = course_tree
    for i in range(4):
        q, right, _ = _question(leaf_a, f"S{i}")
        _submit(student, q, right)

    assert UserKnowledgeState.objects.get(user=student, topic=leaf_a).mastery_percentage >= 0.70
    assert not UserKnowledgeState.objects.filter(user=student).exclude(topic=leaf_a).exists()
    assert AssessmentAttempt.objects.filter(user=student).count() == 4


# ---------------------------------------------------------------------------
# Identity columns
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_attempt_no_counts_per_user_and_topic(student, course_tree):
    course, _, leaf_a, leaf_b = course_tree
    qa = [_question(leaf_a, f"A{i}") for i in range(3)]
    qb = _question(leaf_b, "B0")
    other = User.objects.create_user(email="other@example.org", password=None)

    _submit(student, qa[0][0], qa[0][1])
    _submit(student, qb[0], qb[2])
    _submit(other, qa[0][0], qa[0][2])
    _submit(student, qa[1][0], qa[1][2])
    result = _submit(student, qa[2][0], qa[2][1])

    assert result.attempt_no == 3
    assert result.source == AttemptSource.ADAPTIVE
    numbers = {
        (a.user_id, a.topic_id): sorted(
            AssessmentAttempt.objects.filter(user=a.user, topic=a.topic).values_list("attempt_no", flat=True)
        )
        for a in AssessmentAttempt.objects.all()
    }
    assert numbers == {
        (student.pk, leaf_a.pk): [1, 2, 3],
        (student.pk, leaf_b.pk): [1],
        (other.pk, leaf_a.pk): [1],
    }
    assert set(AssessmentAttempt.objects.values_list("course_id", flat=True)) == {course.pk}


@pytest.mark.django_db
def test_topic_is_a_snapshot_at_answer_time(student, course_tree):
    _, _, leaf_a, leaf_b = course_tree
    q, right, _ = _question(leaf_a, "moves later")
    _submit(student, q, right)

    q.topic = leaf_b
    q.save()

    attempt = AssessmentAttempt.objects.get(user=student)
    assert attempt.topic_id == leaf_a.pk


@pytest.mark.django_db
def test_hybrid_trace_is_stored_and_prior_comes_from_state(student, course_tree):
    _, _, leaf, _ = course_tree
    (q1, right1, _), (q2, _, wrong2) = _question(leaf, "Q1", b=0.5), _question(leaf, "Q2", b=-0.5)

    _submit(student, q1, right1)
    _submit(student, q2, wrong2)

    first, second = AssessmentAttempt.objects.filter(user=student).order_by("attempt_no")
    state = UserKnowledgeState.objects.get(user=student, topic=leaf)
    for row in (first, second):
        assert row.source == AttemptSource.ADAPTIVE
        assert row.engine_version == "hybrid_bkt_irt/0"
        assert row.p_hat == pytest.approx(
            row.p_before * (1 - row.slip_used) + (1 - row.p_before) * row.guess_used
        )
        assert row.b_before == row.b_after == row.question.irt_difficulty
        assert row.history_entry.calculated_mastery == pytest.approx(row.p_after)
        assert row.history_entry.created_at == row.answered_at
        # The KB version is recorded since stage 2; readiness comes in stage 4.
        assert row.kb_version == KnowledgeBaseVersion.current()
        assert row.readiness_score is None and row.was_ready is None

    assert first.p_before == pytest.approx(DEFAULT_P_INIT)
    assert second.p_before == pytest.approx(first.p_after)
    assert second.theta_before == pytest.approx(first.theta_after)
    assert state.mastery_percentage == pytest.approx(second.p_after)
    assert UserAbility.objects.get(user=student, topic=leaf).theta == pytest.approx(second.theta_after)


@pytest.mark.django_db
@pytest.mark.parametrize("stored", [0.0, 100.0, 80.0])
def test_state_without_engine_estimate_falls_back_to_p0(student, course_tree, stored):
    """Legacy rows: 0-100 test grades, or counters bumped by a test session only."""
    _, _, leaf, _ = course_tree
    UserKnowledgeState.objects.create(user=student, topic=leaf, mastery_percentage=stored, total_attempts=5)
    q, right, _ = _question(leaf, "Q")
    _submit(student, q, right)
    assert AssessmentAttempt.objects.get(user=student).p_before == pytest.approx(DEFAULT_P_INIT)


@pytest.mark.django_db
def test_submit_answer_api_reports_ledger_source(student, course_tree):
    from rest_framework.test import APIClient

    _, _, leaf, _ = course_tree
    q, right, _ = _question(leaf, "Q")
    client = APIClient()
    client.force_authenticate(student)
    body = client.post(
        "/api/assessments/submit_answer/", {"question_id": q.pk, "choice_id": right.pk}, format="json",
    ).json()
    assert body["source"] == AttemptSource.ADAPTIVE
    assert body["attempt_no"] == 1


# ---------------------------------------------------------------------------
# D25: repeats within the review window
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_repeat_within_window_is_logged_but_changes_nothing(student, course_tree):
    _, _, leaf, _ = course_tree
    q, right, wrong = _question(leaf, "Q")
    _submit(student, q, wrong)
    before = UserKnowledgeState.objects.get(user=student, topic=leaf)
    theta_before = UserAbility.objects.get(user=student, topic=leaf).theta

    result = _submit(student, q, right)

    assert result.source == AttemptSource.REVIEW_REPEAT
    assert result.attempt_no == 2
    assert result.mastery_percentage == pytest.approx(before.mastery_percentage)
    after = UserKnowledgeState.objects.get(user=student, topic=leaf)
    assert (after.mastery_percentage, after.total_attempts, after.correct_attempts) == (
        before.mastery_percentage, before.total_attempts, before.correct_attempts,
    )
    assert UserAbility.objects.get(user=student, topic=leaf).theta == theta_before
    repeat = AssessmentAttempt.objects.get(user=student, attempt_no=2)
    assert repeat.is_correct is True
    assert repeat.p_before is None and repeat.p_after is None and repeat.engine_version == ""
    assert not UserKnowledgeHistory.objects.filter(attempt=repeat).exists()


@pytest.mark.django_db
def test_repeat_after_window_is_a_normal_answer(student, course_tree, settings):
    settings.THESIS_MODEL = {**settings.THESIS_MODEL, "REVIEW_REPEAT_HOURS": 0.0}
    _, _, leaf, _ = course_tree
    q, right, wrong = _question(leaf, "Q")
    _submit(student, q, wrong)
    assert _submit(student, q, right).source == AttemptSource.ADAPTIVE


@pytest.mark.django_db
def test_seed_and_simulated_answers_are_never_downgraded(student, course_tree):
    _, _, leaf, _ = course_tree
    q, right, _ = _question(leaf, "Q")
    past = timezone.now() - timedelta(days=2)
    _submit(student, q, right, source=AttemptSource.SEED, answered_at=past)
    result = _submit(student, q, right, source=AttemptSource.SEED, answered_at=past + timedelta(minutes=1))
    assert result.source == AttemptSource.SEED
    assert AssessmentAttempt.objects.get(user=student, attempt_no=1).answered_at == past


@pytest.mark.django_db
def test_next_question_prefers_questions_outside_the_window(student, course_tree):
    from assessments.services import get_next_question

    _, _, leaf, _ = course_tree
    near, _, near_wrong = _question(leaf, "near", b=0.0)
    far, _, _ = _question(leaf, "far", b=3.0)
    _submit(student, near, near_wrong)
    # "near" is still the closest to theta but was just answered (D25).
    assert get_next_question(user=student, topic_id=leaf.pk) == far


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_ledger_rows_cannot_be_rewritten(student, course_tree):
    _, _, leaf, _ = course_tree
    q, right, _ = _question(leaf, "Q")
    _submit(student, q, right)
    attempt = AssessmentAttempt.objects.get(user=student)

    attempt.is_correct = False
    with pytest.raises(ImmutableLedgerError):
        attempt.save()
    with pytest.raises(ImmutableLedgerError):
        AssessmentAttempt.objects.filter(pk=attempt.pk).update(answered_at=timezone.now())
    with pytest.raises(ImmutableLedgerError):
        AssessmentAttempt.objects.bulk_create([attempt])


@pytest.mark.django_db
def test_record_attempt_rejects_invalid_requests(student, course_tree):
    _, _, leaf, _ = course_tree
    _, right, _ = _question(leaf, "Q")

    with transaction.atomic():
        for kwargs, message in [
            ({"source": AttemptSource.LEGACY}, "cannot write"),
            ({"source": "made_up"}, "cannot write"),
            ({"source": AttemptSource.ADAPTIVE, "answered_at": timezone.now()}, "back-dated"),
            ({"source": AttemptSource.TEST_SESSION}, "session"),
            ({"source": AttemptSource.REVIEW_REPEAT, "trace": ledger.ModelTrace(p_after=0.5)}, "observations"),
        ]:
            with pytest.raises(ValueError, match=message):
                ledger.record_attempt(user=student, choice=right, **kwargs)
    with pytest.raises(ValueError):
        process_submission(user=student, question_id=right.question_id, choice_id=right.pk,
                           source=AttemptSource.TEST_SESSION)
    assert not AssessmentAttempt.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_record_attempt_requires_a_transaction(student, course_tree):
    _, _, leaf, _ = course_tree
    _, right, _ = _question(leaf, "Q")
    with pytest.raises(RuntimeError, match="transaction"):
        ledger.record_attempt(user=student, choice=right, source=AttemptSource.ADAPTIVE)
    assert not AssessmentAttempt.objects.exists()


@pytest.mark.django_db
def test_database_rejects_out_of_range_values(student, course_tree):
    from django.db import IntegrityError

    _, _, leaf, _ = course_tree
    _, right, _ = _question(leaf, "Q")
    with pytest.raises(IntegrityError), transaction.atomic():
        ledger.record_attempt(
            user=student, choice=right, source=AttemptSource.ADAPTIVE,
            trace=ledger.ModelTrace(p_after=1.5),
        )


# ---------------------------------------------------------------------------
# Concurrency (V-D1)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_parallel_answers_get_gapless_numbers_and_chain():
    user = User.objects.create_user(email="parallel@example.org", password=None)
    topic = make_topic("Parallel", slug="parallel")
    pairs = []
    for i in range(10):
        q, right, wrong = _question(topic, f"P{i}", b=i / 5)
        pairs.append((q.pk, (right if i % 3 else wrong).pk))

    barrier = threading.Barrier(len(pairs))
    errors: list[BaseException] = []

    def worker(question_id, choice_id):
        try:
            barrier.wait()
            process_submission(user=user, question_id=question_id, choice_id=choice_id)
        except BaseException as exc:  # reported below, never swallowed
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=pair) for pair in pairs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    rows = list(AssessmentAttempt.objects.filter(user=user).order_by("attempt_no"))
    assert [r.attempt_no for r in rows] == list(range(1, 11))
    assert rows[0].p_before == pytest.approx(DEFAULT_P_INIT)
    for prev, row in zip(rows, rows[1:]):
        assert row.p_before == pytest.approx(prev.p_after)
        assert row.theta_before == pytest.approx(prev.theta_after)
    state = UserKnowledgeState.objects.get(user=user, topic=topic)
    assert state.total_attempts == 10
    assert state.mastery_percentage == pytest.approx(rows[-1].p_after)


@pytest.mark.django_db(transaction=True)
def test_parallel_ledger_writes_without_a_state_lock():
    """
    Paths that do not lock a state row first (test sessions, seeds) rely on
    the ledger's own (user, topic) lock for attempt_no.
    """
    user = User.objects.create_user(email="parallel-ledger@example.org", password=None)
    topic = make_topic("Parallel ledger", slug="parallel-ledger")
    choices = [_question(topic, f"L{i}")[1] for i in range(10)]

    barrier = threading.Barrier(len(choices))
    errors: list[BaseException] = []

    def worker(choice):
        try:
            barrier.wait()
            with transaction.atomic():
                ledger.record_attempt(user=user, choice=choice, source=AttemptSource.SEED)
        except BaseException as exc:  # reported below, never swallowed
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(c,)) for c in choices]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert sorted(AssessmentAttempt.objects.filter(user=user).values_list("attempt_no", flat=True)) == list(range(1, 11))
