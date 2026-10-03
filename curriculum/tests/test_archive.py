"""
Stage 1, D11: answers keep their question, choice and topic.

- deleting an answered topic archives its subtree instead (API);
- deleting an answered question deactivates it (API);
- editing a question edits its choices in place, so answers keep their choice;
- the ORM refuses deletions that would drop answers.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import ProtectedError
from rest_framework.test import APIClient

from assessments.models import AssessmentAttempt, Choice, Question
from assessments.services.orchestrator import process_submission
from curriculum.kb_guard import KBWriteError, kb_write
from curriculum.models import KnowledgeBaseVersion, Topic
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()


@pytest.fixture
def teacher():
    user = User.objects.create_user(email="teacher@example.org", password=None, is_staff=True)
    user.groups.add(Group.objects.get_or_create(name="Instructor")[0])
    return user


@pytest.fixture
def student():
    return User.objects.create_user(email="student@example.org", password=None)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def tree():
    course = make_course("Course", slug="course")
    section = make_section("Section", course, slug="section")
    answered = make_topic("Answered", section, slug="answered")
    untouched = make_topic("Untouched", section, slug="untouched")
    return course, section, answered, untouched


def _question(topic, text="Q"):
    q = Question.objects.create(topic=topic, text=text)
    right = Choice.objects.create(question=q, text="right", is_correct=True)
    wrong = Choice.objects.create(question=q, text="wrong", is_correct=False)
    return q, right, wrong


def _answer(user, choice):
    process_submission(user=user, question_id=choice.question_id, choice_id=choice.pk)


@pytest.mark.django_db
def test_deleting_an_unanswered_topic_deletes_it(teacher, tree):
    _, _, _, untouched = tree
    _question(untouched)
    response = client_for(teacher).delete(f"/api/curriculum/instructor/topics/{untouched.pk}/")
    assert response.status_code == 204
    assert not Topic.objects.filter(pk=untouched.pk).exists()


@pytest.mark.django_db
def test_deleting_an_answered_subtree_archives_it(teacher, student, tree):
    course, section, answered, untouched = tree
    _, right, _ = _question(answered)
    _answer(student, right)
    attempts_before = list(AssessmentAttempt.objects.values_list("pk", "topic_id", "question_id"))
    version_before = KnowledgeBaseVersion.current()

    response = client_for(teacher).delete(f"/api/curriculum/instructor/topics/{section.pk}/")

    assert response.status_code == 200
    assert response.json() == {"id": section.pk, "archived": True, "archived_topics": 3}
    assert set(Topic.objects.filter(is_archived=True).values_list("pk", flat=True)) == {
        section.pk, answered.pk, untouched.pk,
    }
    assert not Topic.objects.get(pk=course.pk).is_archived
    assert list(AssessmentAttempt.objects.values_list("pk", "topic_id", "question_id")) == attempts_before
    # The refused delete rolled back; the archive is one KB change.
    assert KnowledgeBaseVersion.current() == version_before + 1


@pytest.mark.django_db
def test_archived_topics_disappear_from_learner_and_instructor_views(teacher, student, tree):
    course, section, answered, _ = tree
    q, right, _ = _question(answered)
    _answer(student, right)
    client_for(teacher).delete(f"/api/curriculum/instructor/topics/{section.pk}/")

    teacher_client, student_client = client_for(teacher), client_for(student)
    listed = {t["id"] for t in teacher_client.get("/api/curriculum/instructor/topics/").json()["results"]}
    assert course.pk in listed and section.pk not in listed
    with_archived = teacher_client.get("/api/curriculum/instructor/topics/?include_archived=true").json()["results"]
    assert {t["id"]: t["is_archived"] for t in with_archived}[section.pk] is True

    def ids(nodes):
        for node in nodes:
            yield node["id"]
            yield from ids(node.get("children", []))

    tree_ids = set(ids(student_client.get("/api/learning_path/tree/").json()))
    assert course.pk in tree_ids and answered.pk not in tree_ids
    graph_ids = {n["id"] for n in student_client.get("/api/curriculum/prerequisite-graph/").json()["nodes"]}
    assert str(course.pk) in graph_ids and str(answered.pk) not in graph_ids
    assert student_client.get(f"/api/curriculum/topics/{answered.pk}/").status_code == 404
    assert student_client.get(f"/api/assessments/next_question/?topic_id={answered.pk}").status_code == 404
    assert student_client.get(f"/api/assessments/test_session/?topic_id={answered.pk}").status_code == 404
    tests_ids = {t["id"] for t in student_client.get("/api/assessments/tests/").json()}
    assert course.pk in tests_ids and answered.pk not in tests_ids
    submit = student_client.post(
        "/api/assessments/submit_answer/", {"question_id": q.pk, "choice_id": right.pk}, format="json",
    )
    assert submit.status_code == 400
    assert teacher_client.post(
        "/api/curriculum/instructor/topics/",
        {"name": "Child", "slug": "child", "parent": section.pk},
        format="json",
    ).status_code == 400


@pytest.mark.django_db
def test_orm_refuses_to_drop_answers(student, tree):
    course, _, answered, _ = tree
    q, right, _ = _question(answered)
    _answer(student, right)
    for obj in (Topic.objects.get(pk=answered.pk), Topic.objects.get(pk=course.pk)):
        with pytest.raises(KBWriteError):
            obj.delete()  # outside the KB service
        with kb_write(), pytest.raises(ProtectedError):
            obj.delete()  # inside it, PROTECT still refuses (D11)
    for obj in (q, right):
        with pytest.raises(ProtectedError):
            obj.delete()
    assert AssessmentAttempt.objects.count() == 1


@pytest.mark.django_db
def test_deleting_an_answered_question_deactivates_it(teacher, student, tree):
    _, _, answered, _ = tree
    q, right, _ = _question(answered, "answered")
    spare, _, _ = _question(answered, "spare")
    _answer(student, right)
    client = client_for(teacher)

    assert client.delete(f"/api/assessments/instructor/questions/{spare.pk}/").status_code == 204
    response = client.delete(f"/api/assessments/instructor/questions/{q.pk}/")
    assert response.status_code == 200
    assert response.json() == {"id": q.pk, "archived": True}
    q.refresh_from_db()
    assert q.is_active is False
    assert AssessmentAttempt.objects.filter(question=q).count() == 1

    listed = client.get(f"/api/assessments/instructor/questions/?topic={answered.pk}").json()
    listed = listed["results"] if isinstance(listed, dict) else listed
    assert listed == []
    with_inactive = client.get(
        f"/api/assessments/instructor/questions/?topic={answered.pk}&include_inactive=true"
    ).json()
    with_inactive = with_inactive["results"] if isinstance(with_inactive, dict) else with_inactive
    assert [item["id"] for item in with_inactive] == [q.pk]


@pytest.mark.django_db
def test_editing_a_question_keeps_answered_choices(teacher, student, tree):
    _, _, answered, _ = tree
    q, right, wrong = _question(answered)
    _answer(student, wrong)
    client = client_for(teacher)
    url = f"/api/assessments/instructor/questions/{q.pk}/"
    base = {"topic": answered.pk, "text": "Edited text", "explanation": "", "difficulty": 2}

    edited = client.put(url, {**base, "choices": [
        {"id": right.pk, "text": "right, reworded", "is_correct": True},
        {"id": wrong.pk, "text": "wrong, reworded", "is_correct": False},
        {"text": "new option", "is_correct": False},
    ]}, format="json")
    assert edited.status_code == 200, edited.json()
    assert sorted(q.choices.values_list("text", flat=True)) == ["new option", "right, reworded", "wrong, reworded"]
    attempt = AssessmentAttempt.objects.get(question=q)
    assert attempt.selected_choice_id == wrong.pk

    new_option = q.choices.get(text="new option")
    dropped_unanswered = client.put(url, {**base, "choices": [
        {"id": right.pk, "text": "right", "is_correct": True},
        {"id": wrong.pk, "text": "wrong", "is_correct": False},
    ]}, format="json")
    assert dropped_unanswered.status_code == 200
    assert not Choice.objects.filter(pk=new_option.pk).exists()

    dropped_answered = client.put(url, {**base, "choices": [
        {"id": right.pk, "text": "right", "is_correct": True},
        {"text": "replacement", "is_correct": False},
    ]}, format="json")
    assert dropped_answered.status_code == 400
    assert Choice.objects.filter(pk=wrong.pk).exists()
    assert not q.choices.filter(text="replacement").exists()

    foreign = _question(answered, "other")[1]
    stolen = client.put(url, {**base, "choices": [
        {"id": foreign.pk, "text": "x", "is_correct": True},
        {"id": wrong.pk, "text": "wrong", "is_correct": False},
    ]}, format="json")
    assert stolen.status_code == 400
