"""
7.1 / D40: topic search on real data.

The removed ``KnowledgeSearch`` page searched twelve concepts hard-coded in
the frontend. The search itself is useful, so it is back as one endpoint over
the knowledge base: names from the database, status and P(L) from this
learner's state, nothing invented (D23).

What is checked here: the match, the shape of a result, that a section or a
course carries no status (D22), that archived nodes and nodes under an
archived ancestor are absent, the limit, the order and the query budget.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from assessments.models import StudentTopicState, TopicStatus
from assessments.services import readiness
from assessments.views.learning import SEARCH_LIMIT
from curriculum.services import kb
from curriculum.services.graph import clear_local_cache
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()

pytestmark = pytest.mark.django_db

SEARCH = "/api/learning/search/"


@pytest.fixture
def student():
    return User.objects.create_user(email="search.student@example.org", password=None)


@pytest.fixture
def api(student):
    client = APIClient()
    client.force_authenticate(student)
    return client


@pytest.fixture
def course():
    """
    Ma'lumotlar tuzilmalari
      ├── Chiziqli tuzilmalar ── Massivlar, Bog'langan ro'yxat
      └── Daraxtlar           ── Ikkilik daraxt
    """
    root = make_course("Ma'lumotlar tuzilmalari", slug="ts-course")
    linear = make_section("Chiziqli tuzilmalar", root, slug="ts-linear", position=0)
    trees = make_section("Daraxtlar", root, slug="ts-trees", position=1)
    nodes = {
        "course": root,
        "linear": linear,
        "trees": trees,
        "arrays": make_topic("Massivlar", linear, slug="ts-arrays", position=0),
        "lists": make_topic("Bog'langan ro'yxat", linear, slug="ts-lists", position=1),
        "binary": make_topic("Ikkilik daraxt", trees, slug="ts-binary", position=0),
    }
    clear_local_cache()
    return nodes


def names(response) -> list[str]:
    return [row["name"] for row in response.json()["results"]]


def test_the_match_is_case_insensitive_and_partial(api, course):
    assert names(api.get(SEARCH, {"q": "massiv"})) == ["Massivlar"]
    assert names(api.get(SEARCH, {"q": "MASSIVLAR"})) == ["Massivlar"]
    assert names(api.get(SEARCH, {"q": "daraxt"})) == ["Daraxtlar", "Ikkilik daraxt"]


def test_an_empty_query_returns_nothing_rather_than_everything(api, course):
    for value in ("", "   "):
        body = api.get(SEARCH, {"q": value}).json()
        assert body["results"] == []
        assert body["count"] == 0

    body = api.get(SEARCH).json()
    assert body["results"] == []


def test_a_topic_carries_this_learner_s_status_and_p_mastery(api, course, student):
    readiness.states_for(user=student)
    StudentTopicState.objects.filter(user=student, topic=course["arrays"]).update(
        p_mastery=0.72, status=TopicStatus.IN_PROGRESS, started_at="2026-01-01T00:00:00Z",
    )

    row = api.get(SEARCH, {"q": "Massivlar"}).json()["results"][0]
    assert row == {
        "topic_id": course["arrays"].pk,
        "name": "Massivlar",
        "slug": "ts-arrays",
        "kind": "topic",
        "course_id": course["course"].pk,
        "course_name": "Ma'lumotlar tuzilmalari",
        "status": TopicStatus.IN_PROGRESS,
        "p_mastery": 0.72,
    }


def test_a_section_and_a_course_have_no_status(api, course):
    rows = {row["kind"]: row for row in api.get(SEARCH, {"q": "tuzilmalar"}).json()["results"]}
    assert set(rows) == {"course", "section"}
    for row in rows.values():
        assert row["status"] is None
        assert row["p_mastery"] is None
    # A course's own course is itself; a section reports the course above it.
    assert rows["course"]["course_id"] == course["course"].pk
    assert rows["section"]["course_id"] == course["course"].pk


def test_a_closed_topic_of_a_new_learner_reports_closed(api, course):
    kb.add_prerequisite(prerequisite=course["arrays"], topic=course["binary"])
    clear_local_cache()

    rows = {row["name"]: row for row in api.get(SEARCH, {"q": "ikkilik"}).json()["results"]}
    assert rows["Ikkilik daraxt"]["status"] == TopicStatus.CLOSED
    assert rows["Ikkilik daraxt"]["p_mastery"] == 0.0


def test_archived_nodes_and_archived_subtrees_are_absent(api, course):
    kb.archive_node(course["trees"])
    clear_local_cache()

    assert names(api.get(SEARCH, {"q": "daraxt"})) == []


def test_the_results_are_in_programme_order_and_cut_at_the_limit(api, course):
    extra = [
        make_topic(f"Massivlar {index:02d}", course["linear"], slug=f"ts-x{index}", position=10 + index)
        for index in range(SEARCH_LIMIT + 5)
    ]
    clear_local_cache()

    body = api.get(SEARCH, {"q": "massiv"}).json()
    assert body["limit"] == SEARCH_LIMIT
    assert body["count"] == SEARCH_LIMIT
    # pos is the preorder position (D4): the original topic comes first, then
    # the new ones in the order they sit under the section.
    assert names(api.get(SEARCH, {"q": "massiv"}))[:3] == [
        "Massivlar", "Massivlar 00", "Massivlar 01",
    ]
    assert len(extra) > SEARCH_LIMIT


def test_the_same_query_answers_the_same_way_twice(api, course):
    first = api.get(SEARCH, {"q": "a"}).json()
    second = api.get(SEARCH, {"q": "a"}).json()
    assert first == second


def test_the_search_needs_an_account(course):
    assert APIClient().get(SEARCH, {"q": "massiv"}).status_code == 401


def test_the_cost_does_not_grow_with_the_number_of_matches(api, course, student):
    """ES7: one state sync, one row query, one course-name query."""
    readiness.states_for(user=student)
    api.get(SEARCH, {"q": "massiv"})  # warm the KB snapshot

    with CaptureQueriesContext(connection) as single:
        api.get(SEARCH, {"q": "massivlar"})
    with CaptureQueriesContext(connection) as several:
        api.get(SEARCH, {"q": "a"})

    assert len(several.captured_queries) == len(single.captured_queries)
