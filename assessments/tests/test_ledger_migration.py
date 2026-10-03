"""
Stage 1 data migration (0006–0008): pre-ledger answers become ``legacy`` rows
with topic, course and attempt_no filled in; nothing is deleted or re-timed.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

BEFORE = [
    ("assessments", "0005_add_irt_fields_and_userability"),
    ("curriculum", "0009_topic_is_archived"),
    ("accounts", "0004_user_is_simulated"),
]


def _migrate(targets=None):
    """Migrate to ``targets`` (default: the latest migrations) and return their app registry."""
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    targets = targets or executor.loader.graph.leaf_nodes()
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


@pytest.mark.django_db(transaction=True)
def test_legacy_rows_are_numbered_and_labelled():
    old = _migrate(BEFORE)
    User = old.get_model("accounts", "CustomUser")
    Topic = old.get_model("curriculum", "Topic")
    Question = old.get_model("assessments", "Question")
    Choice = old.get_model("assessments", "Choice")
    Attempt = old.get_model("assessments", "AssessmentAttempt")

    def topic(slug, parent=None, lft=1, rght=2, level=0):
        return Topic.objects.create(
            name=slug, slug=slug, parent=parent, tree_id=1, lft=lft, rght=rght, level=level,
        )

    course = topic("course", lft=1, rght=6)
    section = topic("section", course, lft=2, rght=5, level=1)
    leaf = topic("leaf", section, lft=3, rght=4, level=2)
    alice = User.objects.create(email="alice@example.org", password="!")
    bob = User.objects.create(email="bob@example.org", password="!")
    q_leaf = Question.objects.create(topic=leaf, text="leaf q")
    q_course = Question.objects.create(topic=course, text="course q")
    c_leaf = Choice.objects.create(question=q_leaf, text="a", is_correct=True)
    c_course = Choice.objects.create(question=q_course, text="b", is_correct=False)

    now = timezone.now()
    # Inserted out of chronological order on purpose.
    plan = [
        (alice, q_leaf, c_leaf, now - timedelta(hours=1)),
        (alice, q_leaf, c_leaf, now - timedelta(hours=3)),
        (bob, q_leaf, c_leaf, now - timedelta(hours=2)),
        (alice, q_course, c_course, now - timedelta(hours=5)),
        (alice, q_leaf, c_leaf, now - timedelta(hours=2)),
    ]
    ids = []
    for user, question, choice, when in plan:
        row = Attempt.objects.create(user=user, question=question, selected_choice=choice, is_correct=choice.is_correct)
        Attempt.objects.filter(pk=row.pk).update(answered_at=when)  # historical model: no ledger guard
        ids.append(row.pk)

    _migrate()
    from assessments.models import AssessmentAttempt

    rows = {a.pk: a for a in AssessmentAttempt.objects.filter(pk__in=ids)}
    assert len(rows) == len(plan)
    assert {a.source for a in rows.values()} == {"legacy"}
    for pk, (user, question, _, when) in zip(ids, plan):
        row = rows[pk]
        assert row.answered_at == when
        assert row.topic_id == question.topic_id
        assert row.course_id == course.pk
        assert row.p_before is None and row.engine_version == ""

    # alice on the leaf: ordered by answered_at, not by insertion.
    assert [rows[ids[i]].attempt_no for i in (1, 4, 0)] == [1, 2, 3]
    assert rows[ids[2]].attempt_no == 1  # bob
    assert rows[ids[3]].attempt_no == 1  # alice on the course node
