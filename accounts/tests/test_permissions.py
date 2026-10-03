"""Role rule (D15) and student/instructor endpoint separation."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from accounts.permissions import get_role, is_instructor
from curriculum.models import Topic, TopicResource

User = get_user_model()


def make_user(email, *, groups=(), **extra):
    user = User.objects.create_user(email=email, password=None, **extra)
    for name in groups:
        group, _ = Group.objects.get_or_create(name=name)
        user.groups.add(group)
    return user


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_role_rule_is_shared_by_permission_and_profile():
    student = make_user("s@example.org")
    teacher = make_user("t@example.org", groups=["Instructor"])
    staff = make_user("staff@example.org", is_staff=True)
    admin = make_user("a@example.org", groups=["Admin"])

    assert [is_instructor(u) for u in (student, teacher, staff, admin)] == [False, True, True, True]
    assert [get_role(u) for u in (student, teacher, staff, admin)] == [
        "student", "instructor", "instructor", "admin",
    ]
    profile = client_for(teacher).get("/api/accounts/profile/").json()
    assert profile["role"] == "instructor"


@pytest.mark.django_db
def test_instructor_group_without_staff_can_manage_questions_and_topics():
    teacher = make_user("t@example.org", groups=["Instructor"])
    client = client_for(teacher)

    resp = client.post("/api/curriculum/instructor/topics/", {"name": "Algebra", "slug": "algebra"}, format="json")
    assert resp.status_code == 201
    topic_id = resp.json()["id"]

    resp = client.post(
        "/api/assessments/instructor/questions/",
        {
            "topic": topic_id,
            "text": "2 + 2?",
            "difficulty": 1,
            "choices": [{"text": "4", "is_correct": True}, {"text": "5", "is_correct": False}],
        },
        format="json",
    )
    assert resp.status_code == 201
    assert client.get("/api/assessments/instructor/questions/").status_code == 200
    assert client.get("/api/assessments/instructor/templates/questions/?file_format=excel").status_code == 200


@pytest.mark.django_db
def test_student_cannot_read_instructor_endpoints():
    student = make_user("s@example.org")
    topic = Topic.objects.create(name="T", slug="t")
    client = client_for(student)

    for url in (
        "/api/curriculum/instructor/topics/",
        f"/api/curriculum/instructor/topics/{topic.id}/",
        "/api/curriculum/instructor/resources/",
        "/api/assessments/instructor/questions/",
        "/api/assessments/instructor/templates/questions/",
    ):
        assert client.get(url).status_code == 403, url


@pytest.mark.django_db
def test_student_read_only_topic_endpoints():
    student = make_user("s@example.org")
    topic = Topic.objects.create(name="T", slug="t")
    TopicResource.objects.create(topic=topic, title="Notes", duration_minutes=7)
    client = client_for(student)

    detail = client.get(f"/api/curriculum/topics/{topic.id}/")
    assert detail.status_code == 200
    assert detail.json()["total_duration_minutes"] == 7
    resources = client.get(f"/api/curriculum/topics/{topic.id}/resources/")
    assert resources.status_code == 200
    assert [r["title"] for r in resources.json()] == ["Notes"]
    assert client.post(f"/api/curriculum/topics/{topic.id}/", {}).status_code == 405
    assert client.get("/api/curriculum/topics/999999/resources/").status_code == 404


@pytest.mark.django_db
def test_anonymous_access_is_rejected():
    client = APIClient()
    assert client.get("/api/curriculum/prerequisite-graph/").status_code == 401
    assert client.get("/api/assessments/instructor/templates/questions/").status_code == 401
