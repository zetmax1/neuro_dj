"""Stage 1: seed and simulator rows are labelled and never re-time other rows (D10, D13)."""

from datetime import timedelta
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from accounts.demo import DEMO_EMAILS
from assessments.models import AssessmentAttempt, AttemptSource, Choice, Question
from assessments.services.orchestrator import process_submission
from curriculum.models import Topic
from curriculum.testing import make_topic

User = get_user_model()


def _answer_once(user, slug="real-topic"):
    topic = Topic.objects.filter(slug=slug).first() or make_topic(slug, slug=slug)
    q = Question.objects.create(topic=topic, text="Q")
    choice = Choice.objects.create(question=q, text="A", is_correct=True)
    process_submission(user=user, question_id=q.pk, choice_id=choice.pk)
    return AssessmentAttempt.objects.get(user=user, question=q)


@pytest.mark.django_db
def test_seed_thesis_demo_writes_seed_rows_and_leaves_others_alone():
    real = User.objects.create_user(email="real.student@example.org", password=None)
    real_attempt = _answer_once(real)

    call_command("seed_thesis_demo", stdout=StringIO())

    seeded = AssessmentAttempt.objects.filter(user__email__in=DEMO_EMAILS)
    assert seeded.exists()
    assert set(seeded.values_list("source", flat=True)) == {AttemptSource.SEED}
    now = timezone.now()
    for attempt in seeded:
        assert now - timedelta(days=3) <= attempt.answered_at <= now - timedelta(hours=2)
        assert attempt.history_entry.created_at == attempt.answered_at
    untouched = AssessmentAttempt.objects.get(pk=real_attempt.pk)
    assert (untouched.answered_at, untouched.source) == (real_attempt.answered_at, AttemptSource.ADAPTIVE)


@pytest.mark.django_db
def test_seed_thesis_demo_keeps_foreign_answers_of_demo_accounts_unless_asked():
    call_command("seed_thesis_demo", stdout=StringIO())
    demo = User.objects.get(email="hybrid_demo@test.com")
    practice = _answer_once(demo)

    with pytest.raises(CommandError, match="--reset-demo-answers"):
        call_command("seed_thesis_demo", stdout=StringIO())
    assert AssessmentAttempt.objects.filter(pk=practice.pk).exists()

    call_command("seed_thesis_demo", "--reset-demo-answers", stdout=StringIO())
    assert not AssessmentAttempt.objects.filter(pk=practice.pk).exists()
    assert set(
        AssessmentAttempt.objects.filter(user=demo).values_list("source", flat=True)
    ) == {AttemptSource.SEED}


@pytest.mark.django_db
def test_seed_data_writes_dated_seed_rows():
    call_command("seed_data", "--yes-delete-all", stdout=StringIO())
    rows = AssessmentAttempt.objects.all()
    assert rows.exists()
    assert set(rows.values_list("source", flat=True)) == {AttemptSource.SEED}
    days = {a.answered_at.date() for a in rows}
    assert len(days) == 7


@pytest.mark.django_db
def test_simulator_labels_its_rows():
    call_command("simulate_bkt_data", "--students", "1", stdout=StringIO())
    rows = AssessmentAttempt.objects.filter(user__is_simulated=True)
    assert rows.exists()
    assert set(rows.values_list("source", flat=True)) == {AttemptSource.SIMULATED}
