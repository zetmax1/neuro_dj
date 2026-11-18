"""
7.1 / D39: the structure editor's two backend needs.

The prerequisite editor arrived in stage 7; editing an existing course did
not — renaming one topic still meant walking a five-step wizard. What the
editor needs from the backend is an ordering operation that is one change
rather than two, and the counters that say in advance which ``kind`` changes
the KB service will accept.

Everything else the editor does (name, description, pass mark, parent, kind)
already goes through ``kb.update_node`` and is covered by test_kb.py.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from assessments.models import Choice, DifficultyLevel, Question
from curriculum.models import KnowledgeBaseVersion, Topic, TopicKind
from curriculum.services import kb
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher():
    user = User.objects.create_user(email="structure.teacher@example.org", password=None)
    user.groups.add(Group.objects.get_or_create(name="Instructor")[0])
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    return user


@pytest.fixture
def api(teacher):
    client = APIClient()
    client.force_authenticate(teacher)
    return client


@pytest.fixture
def course(teacher):
    """C ── B1 (t1, t2, t3), B2; t1 holds one question."""
    root = make_course("C", slug="se-c", instructor=teacher)
    b1 = make_section("B1", root, slug="se-b1", position=0, instructor=teacher)
    b2 = make_section("B2", root, slug="se-b2", position=1, instructor=teacher)
    topics = {
        name: make_topic(name, b1, slug=f"se-{name}", position=index, instructor=teacher)
        for index, name in enumerate(("t1", "t2", "t3"))
    }
    question = Question.objects.create(
        topic=topics["t1"], text="?", difficulty=DifficultyLevel.MEDIUM,
    )
    Choice.objects.create(question=question, text="a", is_correct=True)
    return {"C": root, "B1": b1, "B2": b2, **topics}


def order_of(parent: Topic) -> list[str]:
    return list(
        Topic.objects.filter(parent=parent, is_archived=False)
        .order_by("position", "id")
        .values_list("name", flat=True)
    )


def listed(api) -> dict[str, dict]:
    """The instructor topic list, keyed by name (the endpoint is paginated)."""
    body = api.get("/api/curriculum/instructor/topics/").json()
    return {row["name"]: row for row in body["results"]}


def reorder(api, node: Topic, direction: str):
    return api.post(
        f"/api/curriculum/instructor/topics/{node.pk}/reorder/",
        {"direction": direction},
        format="json",
    )


# ---------------------------------------------------------------------------
# Ordering among siblings
# ---------------------------------------------------------------------------

def test_moving_a_topic_down_and_back_up_restores_the_order(api, course):
    assert order_of(course["B1"]) == ["t1", "t2", "t3"]

    response = reorder(api, course["t1"], "down")
    assert response.status_code == 200, response.json()
    assert [row["name"] for row in response.json()["siblings"]] == ["t2", "t1", "t3"]
    assert order_of(course["B1"]) == ["t2", "t1", "t3"]

    assert reorder(api, course["t1"], "up").status_code == 200
    assert order_of(course["B1"]) == ["t1", "t2", "t3"]


def test_one_move_is_one_version_bump(api, course):
    before = KnowledgeBaseVersion.current()
    assert reorder(api, course["t3"], "up").status_code == 200
    assert KnowledgeBaseVersion.current() == before + 1


def test_the_row_is_renumbered_so_no_two_siblings_share_a_position(api, course):
    # Seeded positions are whatever the wizard left behind, gaps included.
    with kb.kb_write():
        Topic.objects.filter(pk=course["t2"].pk).update(position=40)
        Topic.objects.filter(pk=course["t3"].pk).update(position=40)

    assert reorder(api, course["t1"], "down").status_code == 200
    positions = list(
        Topic.objects.filter(parent=course["B1"]).order_by("position", "id")
        .values_list("name", "position")
    )
    assert positions == [("t2", 0), ("t1", 1), ("t3", 2)]


def test_a_node_already_at_the_edge_is_refused_and_nothing_moves(api, course):
    before = KnowledgeBaseVersion.current()

    first = reorder(api, course["t1"], "up")
    assert first.status_code == 400
    assert first.json()["reason"] == "at_edge"

    last = reorder(api, course["t3"], "down")
    assert last.status_code == 400
    assert last.json()["reason"] == "at_edge"

    assert order_of(course["B1"]) == ["t1", "t2", "t3"]
    assert KnowledgeBaseVersion.current() == before


def test_an_unknown_direction_is_refused(api, course):
    response = reorder(api, course["t2"], "sideways")
    assert response.status_code == 400
    assert response.json()["reason"] == "direction"


def test_sections_and_courses_reorder_the_same_way(api, course, teacher):
    assert reorder(api, course["B2"], "up").status_code == 200
    assert order_of(course["C"]) == ["B2", "B1"]

    other = make_course("D", slug="se-d", instructor=teacher)
    assert reorder(api, other, "up").status_code == 200
    assert list(
        Topic.objects.filter(parent=None, is_archived=False)
        .order_by("position", "id").values_list("name", flat=True)
    ) == ["D", "C"]


def test_archived_siblings_do_not_take_a_slot(api, course):
    kb.archive_node(course["t2"])
    assert reorder(api, course["t3"], "up").status_code == 200
    assert order_of(course["B1"]) == ["t3", "t1"]


def test_reordering_is_instructor_only(course):
    client = APIClient()
    client.force_authenticate(User.objects.create_user(email="s@example.org", password=None))
    assert reorder(client, course["t1"], "down").status_code == 403
    assert order_of(course["B1"]) == ["t1", "t2", "t3"]


# ---------------------------------------------------------------------------
# The counters that gate the kind select
# ---------------------------------------------------------------------------

def test_the_counters_say_which_kind_changes_are_possible(api, course):
    rows = listed(api)

    # A section with children is not a leaf, so it cannot become a topic.
    assert rows["B1"]["child_count"] == 3
    assert rows["B1"]["question_count"] == 0
    # An empty section can.
    assert rows["B2"]["child_count"] == 0
    # t1 holds a question, so it cannot become a section (Y4); t2 can.
    assert rows["t1"]["question_count"] == 1
    assert rows["t2"]["question_count"] == 0

    refused = api.patch(
        f"/api/curriculum/instructor/topics/{course['t1'].pk}/",
        {"kind": TopicKind.SECTION}, format="json",
    )
    assert refused.status_code == 400
    assert refused.json()["reason"] == "has_questions"

    accepted = api.patch(
        f"/api/curriculum/instructor/topics/{course['t2'].pk}/",
        {"kind": TopicKind.SECTION}, format="json",
    )
    assert accepted.status_code == 200
    assert accepted.json()["kind"] == TopicKind.SECTION


def test_the_counters_do_not_distort_the_duration(api, course, teacher):
    from curriculum.models import TopicResource

    # Two resources and one question on the same node: joining both tables
    # without care would report the duration twice.
    TopicResource.objects.create(topic=course["t1"], title="a", duration_minutes=30)
    TopicResource.objects.create(topic=course["t1"], title="b", duration_minutes=12)
    question = Question.objects.create(
        topic=course["t1"], text="?2", difficulty=DifficultyLevel.EASY,
    )
    Choice.objects.create(question=question, text="a", is_correct=True)

    rows = listed(api)
    assert rows["t1"]["total_duration_minutes"] == 42
    assert rows["t1"]["question_count"] == 2
    assert rows["B1"]["total_duration_minutes"] == 0


def test_archived_children_are_not_counted(api, course):
    kb.archive_node(course["t2"])
    rows = listed(api)
    assert rows["B1"]["child_count"] == 2
