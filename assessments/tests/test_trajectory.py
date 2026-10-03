"""
Stage 6: the trajectory and the learner-facing API (TR1–TR4, P1-8, ES7).

The arithmetic of Algorithm 2.5 is checked without a database in
``neuro_model/tests/test_trajectory.py``. Here the service and the endpoints
are checked, including the two values section 4 fixes:

- Need(t7) = {t4, t6} and the path t4 → t6 → t7;
- review priority: t1 (impact 4) before t3 (impact 3).

The reference course of section 4 is rebuilt through the KB service.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    MistakeReview,
    Question,
    StudentTopicState,
    TopicModelParams,
    TopicStatus,
)
from assessments.services import readiness, trajectory
from assessments.services.orchestrator import process_submission
from curriculum.services import kb
from curriculum.services.graph import clear_local_cache, get_snapshot
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def student():
    return User.objects.create_user(email="trajectory.student@example.org", password=None)


@pytest.fixture
def api(student):
    client = APIClient()
    client.force_authenticate(student)
    return client


@pytest.fixture
def reference_course():
    """
    C ── B1 (t1, t2, t3) ── B2 (t4, t5) ── B3 (t6, t7, t8)
    E_P: t1→t3, t1→t5, t2→t4, t3→t6, t5→t6, t6→t7, t6→t8, t4→B3
    """
    course = make_course("Ma'lumotlar tuzilmalari", slug="tr-course")
    sections = {
        name: make_section(name, course, slug=f"tr-{name.lower()}", position=index)
        for index, name in enumerate(("B1", "B2", "B3"))
    }
    layout = {"B1": ("t1", "t2", "t3"), "B2": ("t4", "t5"), "B3": ("t6", "t7", "t8")}
    topics = {
        slug: make_topic(slug, sections[section], slug=f"tr-{slug}", position=index)
        for section, slugs in layout.items()
        for index, slug in enumerate(slugs)
    }
    nodes = {**topics, **sections, "C": course}
    for source, target in (
        ("t1", "t3"), ("t1", "t5"), ("t2", "t4"), ("t3", "t6"),
        ("t5", "t6"), ("t6", "t7"), ("t6", "t8"), ("t4", "B3"),
    ):
        kb.add_prerequisite(prerequisite=nodes[source], topic=nodes[target])
    clear_local_cache()
    return nodes


def _set(student, topic, *, p, mastered, status, started=True):
    readiness.states_for(user=student)
    StudentTopicState.objects.filter(user=student, topic=topic).update(
        p_mastery=p,
        mastered_flag=mastered,
        status=status,
        started_at=timezone.now() if started else None,
        attempts=1 if started else 0,
        correct=1 if started and mastered else 0,
        accuracy=1.0 if started and mastered else 0.0,
    )


def readiness_state(student, nodes):
    """t1, t2, t3, t5 mastered; t4 in_progress at 0.62 — before the two answers."""
    for slug in ("t1", "t2", "t3", "t5"):
        _set(student, nodes[slug], p=0.97, mastered=True, status=TopicStatus.MASTERED)
    _set(student, nodes["t4"], p=0.62, mastered=False, status=TopicStatus.IN_PROGRESS)
    readiness.resync(user=student, snapshot=get_snapshot())


def review_state(student, nodes):
    """t1=0.80 and t3=0.70 in review, t5 mastered, t6-t8 unmastered."""
    _set(student, nodes["t1"], p=0.80, mastered=False, status=TopicStatus.REVIEW)
    _set(student, nodes["t3"], p=0.70, mastered=False, status=TopicStatus.REVIEW)
    for slug in ("t2", "t4", "t5"):
        _set(student, nodes[slug], p=0.99, mastered=True, status=TopicStatus.MASTERED)
    readiness.resync(user=student, snapshot=get_snapshot())


# ---------------------------------------------------------------------------
# Need(t7) and the path — the value of section 4
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_need_of_t7_and_its_path(student, reference_course, api):
    nodes = reference_course
    readiness_state(student, nodes)

    body = api.get(f"/api/learning/path-to/{nodes['t7'].pk}/").json()

    assert [item["topic_id"] for item in body["need"]] == [nodes["t4"].pk, nodes["t6"].pk]
    assert [item["topic_id"] for item in body["path"]] == [
        nodes["t4"].pk, nodes["t6"].pk, nodes["t7"].pk,
    ]
    assert [item["name"] for item in body["path"]] == ["t4", "t6", "t7"]
    assert body["goal_id"] == nodes["t7"].pk
    assert body["reachable"] is True


@pytest.mark.django_db
def test_the_path_carries_the_status_and_p_of_each_step(student, reference_course, api):
    nodes = reference_course
    readiness_state(student, nodes)

    body = api.get(f"/api/learning/path-to/{nodes['t7'].pk}/").json()
    by_id = {item["topic_id"]: item for item in body["path"]}

    assert by_id[nodes["t4"].pk]["status"] == TopicStatus.IN_PROGRESS
    assert by_id[nodes["t4"].pk]["p_mastery"] == pytest.approx(0.62)
    assert by_id[nodes["t6"].pk]["status"] == TopicStatus.CLOSED


@pytest.mark.django_db
def test_the_path_to_an_open_topic_is_just_that_topic(student, reference_course, api):
    nodes = reference_course
    readiness_state(student, nodes)

    body = api.get(f"/api/learning/path-to/{nodes['t4'].pk}/").json()

    assert body["need"] == []
    assert [item["topic_id"] for item in body["path"]] == [nodes["t4"].pk]


@pytest.mark.django_db
def test_the_path_to_an_unknown_topic_is_404(student, reference_course, api):
    assert api.get("/api/learning/path-to/999999/").status_code == 404


@pytest.mark.django_db
def test_a_section_is_not_a_path_target(student, reference_course, api):
    """Only topics carry state (D22), so Need is defined on topics."""
    assert api.get(f"/api/learning/path-to/{reference_course['B3'].pk}/").status_code == 404


# ---------------------------------------------------------------------------
# Review priority — the value of section 4
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_review_priority_of_section_four(student, reference_course, api):
    nodes = reference_course
    review_state(student, nodes)

    body = api.get("/api/learning/trajectory/").json()
    group_a = body["groups"]["A"]

    assert [item["name"] for item in group_a] == ["t1", "t3"]
    assert group_a[0]["reason"] == {"code": "review_impact", "params": {"impact": 4, "p": 0.80}}
    assert group_a[1]["reason"]["params"] == {"impact": 3, "p": 0.70}
    assert body["next"]["name"] == "t1", "the review with the widest impact comes first"


@pytest.mark.django_db
def test_the_groups_are_a_b_c_d_and_mastered_is_absent(student, reference_course, api):
    nodes = reference_course
    readiness_state(student, nodes)

    body = api.get("/api/learning/trajectory/").json()

    assert [item["name"] for item in body["groups"]["B"]] == ["t4"]
    assert [item["name"] for item in body["groups"]["C"]] == []
    assert [item["name"] for item in body["groups"]["D"]] == ["t6", "t7", "t8"]
    listed = {item["name"] for item in body["items"]}
    assert listed.isdisjoint({"t1", "t2", "t3", "t5"}), "mastered topics are not next steps"


@pytest.mark.django_db
def test_closed_items_name_what_is_in_the_way(student, reference_course, api):
    nodes = reference_course
    readiness_state(student, nodes)

    body = api.get("/api/learning/trajectory/").json()
    blocked = {item["name"]: item for item in body["groups"]["D"]}

    assert [item["name"] for item in blocked["t6"]["missing"]] == ["t4"]
    assert blocked["t6"]["reason"] == {"code": "blocked", "params": {"missing": 1}}
    assert {item["name"] for item in blocked["t7"]["missing"]} == {"t4", "t6"}


@pytest.mark.django_db
def test_the_order_is_topological_not_by_position(student, reference_course, api):
    """
    t4 is in section B2 and t3 in B1, but t4 → t6 means t4 comes before t6
    whatever their positions. The closed group follows G_L, not position.
    """
    nodes = reference_course
    readiness.states_for(user=student)

    body = api.get("/api/learning/trajectory/").json()

    # Nothing answered yet: t1 and t2 have no prerequisites so they are open,
    # the rest are closed. Both groups keep the order of G_L.
    assert [item["name"] for item in body["groups"]["C"]] == ["t1", "t2"]
    closed = [item["name"] for item in body["groups"]["D"]]
    assert closed.index("t4") < closed.index("t6") < closed.index("t7")
    assert closed.index("t3") < closed.index("t6")
    # Position would have put t3 (B1, position 2) before t4 (B2, position 0);
    # the topological order puts t4 first because t4 → t6 and t3 → t6 both
    # feed t6 and Algorithm 2.2 breaks the tie on (pos, id) of the whole tree.
    assert closed == ["t3", "t4", "t5", "t6", "t7", "t8"]


@pytest.mark.django_db
def test_every_item_has_a_code_and_numbers_not_a_sentence(student, reference_course, api):
    nodes = reference_course
    review_state(student, nodes)

    for item in api.get("/api/learning/trajectory/").json()["items"]:
        reason = item["reason"]
        assert reason["code"] in {"review_impact", "in_progress", "ready", "blocked"}
        assert " " not in reason["code"]
        assert all(isinstance(value, (int, float)) for value in reason["params"].values())


@pytest.mark.django_db
def test_the_trajectory_can_be_scoped_to_one_course(student, reference_course, api):
    nodes = reference_course
    other = make_course("Other", slug="tr-other")
    outside = make_topic("outside", other, slug="tr-outside")
    clear_local_cache()
    readiness.states_for(user=student)

    whole = api.get("/api/learning/trajectory/").json()
    scoped = api.get(f"/api/learning/trajectory/?course={nodes['C'].pk}").json()

    assert "outside" in {item["name"] for item in whole["items"]}
    assert "outside" not in {item["name"] for item in scoped["items"]}
    assert scoped["course_id"] == nodes["C"].pk
    assert len(scoped["items"]) == 8


@pytest.mark.django_db
def test_an_unknown_course_is_404(student, reference_course, api):
    assert api.get("/api/learning/trajectory/?course=999999").status_code == 404
    assert api.get("/api/learning/trajectory/?course=abc").status_code == 404


@pytest.mark.django_db
def test_the_trajectory_cost_does_not_grow_with_the_course(student, api):
    """ES7: the budget must not scale with the number of topics."""
    def build(name: str, topics: int):
        course = make_course(name, slug=f"budget-{name}")
        section = make_section("S", course, slug=f"budget-{name}-s")
        previous = None
        for index in range(topics):
            topic = make_topic(f"{name}{index}", section, slug=f"budget-{name}-t{index}")
            if previous is not None:
                kb.add_prerequisite(prerequisite=previous, topic=topic)
            previous = topic
        clear_local_cache()
        return course

    small = build("small", 3)
    with CaptureQueriesContext(connection) as few:
        assert api.get(f"/api/learning/trajectory/?course={small.pk}").status_code == 200

    large = build("large", 15)
    with CaptureQueriesContext(connection) as many:
        assert api.get(f"/api/learning/trajectory/?course={large.pk}").status_code == 200

    per_topic = (len(many) - len(few)) / 12
    assert per_topic < 0.5, (
        f"{per_topic:.2f} queries per extra topic: the trajectory is N+1"
    )


# ---------------------------------------------------------------------------
# The dashboard uses the service
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_the_dashboard_reports_the_trajectory_not_four_heuristics(student, reference_course, api):
    nodes = reference_course
    review_state(student, nodes)

    body = api.get("/api/analytics/overview/").json()

    assert "recommendations" not in body
    assert set(body["trajectory"]["groups"]) == {"A", "B", "C", "D"}
    assert body["trajectory"]["next"]["name"] == "t1"


@pytest.mark.django_db
def test_the_dashboard_and_the_endpoint_agree(student, reference_course, api):
    nodes = reference_course
    review_state(student, nodes)

    dashboard = api.get("/api/analytics/overview/").json()["trajectory"]
    endpoint = api.get("/api/learning/trajectory/").json()

    assert dashboard["groups"] == endpoint["groups"]
    assert dashboard["next"] == endpoint["next"]


# ---------------------------------------------------------------------------
# Mistakes (D25, addendum 2.10)
# ---------------------------------------------------------------------------

def _question(topic, text, *, explanation=""):
    question = Question.objects.create(topic=topic, text=text, explanation=explanation)
    right = Choice.objects.create(question=question, text="right", is_correct=True)
    wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
    return question, right, wrong


def _submit(user, question, choice):
    return process_submission(
        user=user, question_id=question.pk, choice_id=choice.pk,
        source=AttemptSource.ADAPTIVE,
    )


@pytest.mark.django_db
def test_mistakes_are_grouped_by_topic_with_both_choices(student, reference_course, api):
    nodes = reference_course
    question, right, wrong = _question(nodes["t1"], "Nima?", explanation="Chunki shunday.")
    _submit(student, question, wrong)

    body = api.get("/api/learning/mistakes/").json()

    assert body["total"] == 1
    assert body["reviewed"] == 0
    assert len(body["topics"]) == 1
    group = body["topics"][0]
    assert group["name"] == "t1"
    mistake = group["mistakes"][0]
    assert mistake["question"] == "Nima?"
    assert mistake["selected_choice"]["text"] == "wrong"
    assert mistake["correct_choice"]["text"] == "right"
    assert mistake["explanation"] == "Chunki shunday."
    assert mistake["corrected_later"] is False
    assert mistake["reviewed"] is False


@pytest.mark.django_db
def test_a_mistake_answered_correctly_later_is_marked(student, reference_course, api, settings):
    nodes = reference_course
    question, right, wrong = _question(nodes["t1"], "Q")
    _submit(student, question, wrong)
    # Outside the review window, so the second answer is a real observation.
    settings.THESIS_MODEL = {**settings.THESIS_MODEL, "REVIEW_REPEAT_HOURS": 0.0}
    _submit(student, question, right)

    body = api.get("/api/learning/mistakes/").json()

    assert body["total"] == 1
    assert body["topics"][0]["mistakes"][0]["corrected_later"] is True


@pytest.mark.django_db
def test_correct_answers_are_not_mistakes(student, reference_course, api):
    nodes = reference_course
    question, right, _ = _question(nodes["t1"], "Q")
    _submit(student, question, right)

    body = api.get("/api/learning/mistakes/").json()
    assert body["total"] == 0
    assert body["topics"] == []


@pytest.mark.django_db
def test_a_mistake_can_be_marked_reviewed_and_the_marking_is_idempotent(
    student, reference_course, api,
):
    nodes = reference_course
    question, _right, wrong = _question(nodes["t1"], "Q")
    result = _submit(student, question, wrong)

    first = api.post(f"/api/learning/mistakes/{result.attempt_id}/reviewed/")
    second = api.post(f"/api/learning/mistakes/{result.attempt_id}/reviewed/")

    assert first.status_code == 201
    assert second.status_code == 200
    assert MistakeReview.objects.filter(user=student).count() == 1

    body = api.get("/api/learning/mistakes/").json()
    assert body["reviewed"] == 1
    assert body["topics"][0]["mistakes"][0]["reviewed"] is True


@pytest.mark.django_db
def test_marking_does_not_touch_the_ledger(student, reference_course, api):
    nodes = reference_course
    question, _right, wrong = _question(nodes["t1"], "Q")
    result = _submit(student, question, wrong)
    before = AssessmentAttempt.objects.get(pk=result.attempt_id)

    api.post(f"/api/learning/mistakes/{result.attempt_id}/reviewed/")

    after = AssessmentAttempt.objects.get(pk=result.attempt_id)
    assert (after.is_correct, after.p_after, after.answered_at) == (
        before.is_correct, before.p_after, before.answered_at,
    )


@pytest.mark.django_db
def test_another_learners_mistake_cannot_be_marked(student, reference_course, api):
    nodes = reference_course
    other = User.objects.create_user(email="other.learner@example.org", password=None)
    question, _right, wrong = _question(nodes["t1"], "Q")
    result = _submit(other, question, wrong)

    assert api.post(f"/api/learning/mistakes/{result.attempt_id}/reviewed/").status_code == 404
    assert not MistakeReview.objects.filter(user=student).exists()


@pytest.mark.django_db
def test_a_correct_answer_cannot_be_marked_as_a_mistake(student, reference_course, api):
    nodes = reference_course
    question, right, _ = _question(nodes["t1"], "Q")
    result = _submit(student, question, right)

    assert api.post(f"/api/learning/mistakes/{result.attempt_id}/reviewed/").status_code == 404


# ---------------------------------------------------------------------------
# Topic history (addendum A4-12, 2.5)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_the_history_reports_what_the_model_used(student, reference_course, api):
    nodes = reference_course
    TopicModelParams.objects.create(topic=nodes["t1"], p0=0.3, pt=0.1, g0=0.2, s0=0.05)
    first, right, wrong = _question(nodes["t1"], "Q1")
    second, right2, _ = _question(nodes["t1"], "Q2")
    _submit(student, first, wrong)
    _submit(student, second, right2)

    body = api.get(f"/api/learning/topics/{nodes['t1'].pk}/history/").json()

    assert body["topic_id"] == nodes["t1"].pk
    assert body["attempts_count"] == 2
    assert len(body["attempts"]) == 2
    a1, a2 = body["attempts"]
    assert a1["attempt_no"] == 1 and a2["attempt_no"] == 2
    assert a1["p_before"] == pytest.approx(0.3, abs=1e-3)
    for row in (a1, a2):
        for field in ("p_hat", "guess", "slip", "p_before", "p_after",
                      "theta_before", "theta_after", "b_before", "b_after"):
            assert row[field] is not None, field
        assert row["engine_version"] == "thesis_hybrid/1"
    # The chain: what one answer left is what the next one started from.
    assert a2["p_before"] == pytest.approx(a1["p_after"])
    assert a2["theta_before"] == pytest.approx(a1["theta_after"])


@pytest.mark.django_db
def test_the_history_reports_theta_per_course_and_the_missing_prerequisites(
    student, reference_course, api,
):
    nodes = reference_course
    body = api.get(f"/api/learning/topics/{nodes['t6'].pk}/history/").json()

    assert body["status"] == TopicStatus.CLOSED
    assert {item["name"] for item in body["missing"]} == {"t3", "t4", "t5"}
    assert body["theta"] == 0.0
    assert body["attempts"] == []


@pytest.mark.django_db
def test_the_history_of_an_unknown_topic_is_404(student, reference_course, api):
    assert api.get("/api/learning/topics/999999/history/").status_code == 404


# ---------------------------------------------------------------------------
# me/summary (D27) and config/model (D29)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_the_summary_is_real_data_only(student, reference_course, api):
    nodes = reference_course
    question, right, wrong = _question(nodes["t1"], "Q")
    _submit(student, question, right)
    _set(student, nodes["t3"], p=0.70, mastered=False, status=TopicStatus.REVIEW)

    body = api.get("/api/me/summary/").json()

    assert body["email"] == student.email
    assert body["attempts"] == 1
    assert body["correct"] == 1
    assert body["accuracy"] == pytest.approx(1.0)
    assert body["topics_in_review"] == 1
    assert body["role"]
    # D27: nothing the system invented.
    assert "xp" not in body
    assert "achievements" not in body
    assert "study_hours" not in body


@pytest.mark.django_db
def test_the_summary_counts_mastered_per_course(student, reference_course, api):
    nodes = reference_course
    readiness_state(student, nodes)

    body = api.get("/api/me/summary/").json()
    course = next(c for c in body["courses"] if c["course_id"] == nodes["C"].pk)

    assert course["total"] == 8
    assert course["mastered"] == 4
    assert course["name"] == "Ma'lumotlar tuzilmalari"
    assert "theta" in course


@pytest.mark.django_db
def test_the_weekly_activity_comes_from_answer_times(student, reference_course, api):
    nodes = reference_course
    for index in range(3):
        question, right, _ = _question(nodes["t1"], f"Q{index}")
        _submit(student, question, right)

    body = api.get("/api/me/summary/").json()

    assert body["activity_days"] == 7
    assert sum(day["answers"] for day in body["weekly_activity"]) == 3


@pytest.mark.django_db
def test_the_model_config_is_the_single_source(student, api, settings):
    body = api.get("/api/config/model/").json()

    assert body["tau"] == settings.THESIS_MODEL["TAU"]
    assert body["delta"] == settings.THESIS_MODEL["DELTA"]
    assert body["g_max"] == settings.THESIS_MODEL["G_MAX"]
    assert body["s_max"] == settings.THESIS_MODEL["S_MAX"]
    assert body["engine"] == "thesis_hybrid/1"
    assert body["flags"] == {"use_irt": True, "use_prereq_init": True}
    assert body["defaults"]["p0"] == settings.THESIS_MODEL["DEFAULT_P0"]
    assert body["statuses"] == ["closed", "open", "in_progress", "mastered", "review"]
    assert body["trajectory_groups"] == ["A", "B", "C", "D"]


@pytest.mark.django_db
def test_every_learning_endpoint_needs_authentication(reference_course):
    anonymous = APIClient()
    for url in (
        "/api/learning/trajectory/",
        "/api/learning/mistakes/",
        "/api/me/summary/",
        "/api/config/model/",
        f"/api/learning/path-to/{reference_course['t1'].pk}/",
        f"/api/learning/topics/{reference_course['t1'].pk}/history/",
    ):
        assert anonymous.get(url).status_code == 401, url


# ---------------------------------------------------------------------------
# The service agrees with the endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_the_service_and_the_endpoint_return_the_same_thing(student, reference_course, api):
    nodes = reference_course
    review_state(student, nodes)

    from_service = [item.payload() for item in trajectory.for_learner(user=student)]
    from_endpoint = api.get("/api/learning/trajectory/").json()["items"]

    assert from_service == from_endpoint


@pytest.mark.django_db
def test_next_step_is_the_head_of_the_trajectory(student, reference_course):
    nodes = reference_course
    review_state(student, nodes)

    items = trajectory.for_learner(user=student)
    assert trajectory.next_step(user=student).topic_id == items[0].topic_id


@pytest.mark.django_db
def test_a_learner_who_has_mastered_everything_has_no_next_step(student, reference_course):
    nodes = reference_course
    for slug in ("t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"):
        _set(student, nodes[slug], p=0.99, mastered=True, status=TopicStatus.MASTERED)
    readiness.resync(user=student, snapshot=get_snapshot())

    assert trajectory.for_learner(user=student) == []
    assert trajectory.next_step(user=student) is None
