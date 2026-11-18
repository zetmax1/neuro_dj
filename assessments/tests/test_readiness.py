"""
Stage 4: readiness and statuses through the Django layer (TY1–TY6, P0-3, P0-6).

The arithmetic is checked without a database in
``neuro_model/tests/test_readiness.py``. What is checked here is the service
and the endpoints: the initial state of a new learner, the readiness example
of section 4, that inheritance runs through G_L only, TY5, TY6, and the 403
that a closed topic answers with.

The reference course of section 4 is rebuilt through the KB service:

    C ── B1 (t1, t2, t3) ── B2 (t4, t5) ── B3 (t6, t7, t8)
    E_P: t1→t3, t1→t5, t2→t4, t3→t6, t5→t6, t6→t7, t6→t8, t4→B3

so E_L gives Pre(t6) = {t3, t4, t5} and Pre(t7) = Pre(t8) = {t4, t6}.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    Question,
    StudentTopicState,
    TopicModelParams,
    TopicStatus,
)
from assessments.services import readiness
from assessments.services.orchestrator import TopicClosed, process_submission
from curriculum.services import kb
from curriculum.services.graph import clear_local_cache, get_snapshot
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()
TOL = 1e-3


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def student():
    return User.objects.create_user(email="readiness.student@example.org", password=None)


@pytest.fixture
def reference_course():
    """The course of section 4, built through the only KB writer."""
    course = make_course("Ma'lumotlar tuzilmalari", slug="ref-course")
    sections = {
        name: make_section(name, course, slug=f"ref-{name.lower()}", position=index)
        for index, name in enumerate(("B1", "B2", "B3"))
    }
    layout = {"B1": ("t1", "t2", "t3"), "B2": ("t4", "t5"), "B3": ("t6", "t7", "t8")}
    topics = {
        slug: make_topic(slug, sections[section], slug=f"ref-{slug}", position=index)
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


def _question(topic, text: str, *, b: float = 0.0):
    question = Question.objects.create(topic=topic, text=text, irt_difficulty=b)
    right = Choice.objects.create(question=question, text="right", is_correct=True)
    wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
    return question, right, wrong


def _submit(user, question, choice):
    return process_submission(
        user=user, question_id=question.pk, choice_id=choice.pk,
        source=AttemptSource.ADAPTIVE,
    )


def _set_state(user, topic, *, p_mastery: float, mastered: bool, status: str, started: bool):
    readiness.states_for(user=user)
    StudentTopicState.objects.filter(user=user, topic=topic).update(
        p_mastery=p_mastery,
        mastered_flag=mastered,
        status=status,
        started_at=timezone.now() if started else None,
        attempts=1 if started else 0,
        correct=1 if started and mastered else 0,
        accuracy=1.0 if started and mastered else 0.0,
    )


def _state(user, topic) -> StudentTopicState:
    return StudentTopicState.objects.get(user=user, topic=topic)


# ---------------------------------------------------------------------------
# The initial state of a new learner
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_a_new_learner_starts_with_the_size_of_pre(student, reference_course):
    nodes = reference_course
    states = readiness.states_for(user=student)

    expected = {
        "t1": 0, "t2": 0, "t3": 1, "t4": 1, "t5": 1, "t6": 3, "t7": 2, "t8": 2,
    }
    for slug, missing in expected.items():
        state = states[nodes[slug].pk]
        assert state.missing_count == missing, slug
        assert state.p_mastery == 0.0
        assert state.mastered_flag is False
        assert state.started_at is None
        assert state.status == (TopicStatus.OPEN if missing == 0 else TopicStatus.CLOSED), slug


@pytest.mark.django_db
def test_the_states_are_materialised_once_and_stay_stable(student, reference_course):
    first = readiness.states_for(user=student)
    count = StudentTopicState.objects.filter(user=student).count()
    second = readiness.states_for(user=student)

    assert StudentTopicState.objects.filter(user=student).count() == count
    assert first.keys() == second.keys()


@pytest.mark.django_db
def test_only_topics_carry_a_state(student, reference_course):
    """
    D22: a status belongs to a topic. Sections and courses hold no questions
    (Y4) and therefore no P(L); the UI shows ``k / n`` for them instead, so no
    state row is created and the graph reports the defaults.
    """
    states = readiness.states_for(user=student)
    assert reference_course["B3"].pk not in states
    assert reference_course["C"].pk not in states
    assert reference_course["t1"].pk in states


# ---------------------------------------------------------------------------
# The readiness example of section 4
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_the_readiness_example_of_section_four(student, reference_course):
    """
    τ=0.95, δ=0.10. Starting state: t1=0.97, t2=0.96, t3=0.98, t5=0.96 (M=1)
    and t4=0.62 (in_progress). Two correct answers take t4's P(L) to 0.8921
    and then 0.9764: the first changes no counter, the second opens t6 and
    takes t7 and t8 from 2 to 1.

    P(L) is handed to Algorithm 2.3 directly here; that those two numbers are
    what BKT produces is asserted in the student-model tests.
    """
    nodes = reference_course
    for slug, p in (("t1", 0.97), ("t2", 0.96), ("t3", 0.98), ("t5", 0.96)):
        _set_state(
            student, nodes[slug], p_mastery=p, mastered=True,
            status=TopicStatus.MASTERED, started=True,
        )
    _set_state(
        student, nodes["t4"], p_mastery=0.62, mastered=False,
        status=TopicStatus.IN_PROGRESS, started=True,
    )
    readiness.resync(user=student, snapshot=get_snapshot())

    assert _state(student, nodes["t6"]).missing_count == 1
    assert _state(student, nodes["t7"]).missing_count == 2
    assert _state(student, nodes["t8"]).missing_count == 2

    # --- first correct answer: 0.62 → 0.8921, inside the band -------------
    from django.db import transaction

    with transaction.atomic():
        first = readiness.apply_answer(
            user=student, topic_id=nodes["t4"].pk, p_mastery=0.8921, is_correct=True,
        )
    assert first.flag_changed is False
    assert first.state.mastered_flag is False
    assert first.state.status == TopicStatus.IN_PROGRESS
    assert _state(student, nodes["t6"]).missing_count == 1, "no counter may move"
    assert _state(student, nodes["t7"]).missing_count == 2
    assert _state(student, nodes["t8"]).missing_count == 2

    # --- second correct answer: 0.9764 ≥ τ --------------------------------
    with transaction.atomic():
        second = readiness.apply_answer(
            user=student, topic_id=nodes["t4"].pk, p_mastery=0.9764, is_correct=True,
        )
    assert second.flag_changed is True
    assert second.state.mastered_flag is True
    assert second.state.status == TopicStatus.MASTERED
    assert second.opened == (nodes["t6"].pk,)

    assert _state(student, nodes["t6"]).missing_count == 0
    assert _state(student, nodes["t6"]).status == TopicStatus.OPEN
    assert _state(student, nodes["t7"]).missing_count == 1
    assert _state(student, nodes["t8"]).missing_count == 1
    assert _state(student, nodes["t7"]).status == TopicStatus.CLOSED


@pytest.mark.django_db
def test_losing_mastery_closes_an_unstarted_successor_again(student, reference_course):
    nodes = reference_course
    for slug in ("t3", "t4", "t5"):
        _set_state(
            student, nodes[slug], p_mastery=0.98, mastered=True,
            status=TopicStatus.MASTERED, started=True,
        )
    readiness.resync(user=student, snapshot=get_snapshot())
    assert _state(student, nodes["t6"]).status == TopicStatus.OPEN

    from django.db import transaction

    with transaction.atomic():
        result = readiness.apply_answer(
            user=student, topic_id=nodes["t4"].pk, p_mastery=0.10, is_correct=False,
        )

    assert result.state.status == TopicStatus.REVIEW, "mastered → review when M falls"
    assert result.closed == (nodes["t6"].pk,)
    assert _state(student, nodes["t6"]).status == TopicStatus.CLOSED
    assert _state(student, nodes["t6"]).missing_count == 1


# ---------------------------------------------------------------------------
# Inheritance runs through G_L only
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_a_mastered_parent_does_not_open_its_child(student):
    """
    The probe of audit 4.3: the removed implementations opened a topic when
    its tree parent was mastered. Readiness has no parent fallback.
    """
    course = make_course("Probe", slug="probe-course")
    section = make_section("S", course, slug="probe-s")
    gate = make_topic("gate", section, slug="probe-gate")
    locked = make_topic("locked", section, slug="probe-locked")
    kb.add_prerequisite(prerequisite=gate, topic=locked)
    clear_local_cache()

    # Master the parent section itself — it is an ancestor, not a predecessor.
    _set_state(
        student, section, p_mastery=0.99, mastered=True,
        status=TopicStatus.MASTERED, started=True,
    )
    readiness.resync(user=student, snapshot=get_snapshot())

    blocked = readiness.check_open(user=student, topic_id=locked.pk)
    assert blocked is not None
    assert [item["topic_id"] for item in blocked.missing] == [gate.pk]


@pytest.mark.django_db
def test_a_relation_on_a_section_is_inherited_by_its_topics(student, reference_course):
    """t4 → B3 in E_P reaches t6, t7 and t8 through G_L."""
    nodes = reference_course
    states = readiness.states_for(user=student)
    pre = get_snapshot().pre
    for slug in ("t6", "t7", "t8"):
        assert nodes["t4"].pk in pre[nodes[slug].pk], slug
    assert states[nodes["t7"].pk].missing_count == 2


# ---------------------------------------------------------------------------
# TY5 — a started topic never closes again
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_ty5_a_new_prerequisite_does_not_close_a_started_topic(student, reference_course):
    nodes = reference_course
    question, right, _ = _question(nodes["t1"], "Q")
    _submit(student, question, right)
    assert _state(student, nodes["t1"]).status == TopicStatus.IN_PROGRESS

    # The instructor adds a prerequisite afterwards.
    kb.add_prerequisite(prerequisite=nodes["t2"], topic=nodes["t1"])
    clear_local_cache()
    readiness.states_for(user=student)

    state = _state(student, nodes["t1"])
    assert state.missing_count == 1, "the counter does reflect the new relation"
    assert state.status == TopicStatus.IN_PROGRESS, "but a started topic is not closed"
    assert readiness.check_open(user=student, topic_id=nodes["t1"].pk) is None


@pytest.mark.django_db
def test_ty5_an_unstarted_topic_does_close_when_a_prerequisite_arrives(student, reference_course):
    nodes = reference_course
    readiness.states_for(user=student)
    assert _state(student, nodes["t1"]).status == TopicStatus.OPEN

    kb.add_prerequisite(prerequisite=nodes["t2"], topic=nodes["t1"])
    clear_local_cache()
    readiness.states_for(user=student)

    assert _state(student, nodes["t1"]).status == TopicStatus.CLOSED


@pytest.mark.django_db
def test_ty5_is_also_a_database_constraint(student, reference_course):
    """A closed row may not carry started_at, and a started one must."""
    from django.db import IntegrityError, transaction

    readiness.states_for(user=student)
    topic = reference_course["t1"]

    with pytest.raises(IntegrityError), transaction.atomic():
        StudentTopicState.objects.filter(user=student, topic=topic).update(
            status=TopicStatus.CLOSED, started_at=timezone.now(),
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        StudentTopicState.objects.filter(user=student, topic=topic).update(
            status=TopicStatus.IN_PROGRESS, started_at=None,
        )


# ---------------------------------------------------------------------------
# TY6 — a state computed under an older KB version is recomputed
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_ty6_a_stale_counter_is_recomputed(student, reference_course):
    nodes = reference_course
    readiness.states_for(user=student)

    # Corrupt the counter and mark the row as belonging to an older KB.
    StudentTopicState.objects.filter(user=student, topic=nodes["t6"]).update(
        missing_count=99, kb_version=0,
    )

    states = readiness.states_for(user=student)

    assert states[nodes["t6"].pk].missing_count == 3
    assert states[nodes["t6"].pk].kb_version == get_snapshot().version


@pytest.mark.django_db
def test_ty6_every_row_records_the_kb_version(student, reference_course):
    version = get_snapshot().version
    states = readiness.states_for(user=student)
    assert {state.kb_version for state in states.values()} == {version}


@pytest.mark.django_db
def test_ty6_a_removed_prerequisite_opens_a_topic(student, reference_course):
    nodes = reference_course
    readiness.states_for(user=student)
    assert _state(student, nodes["t3"]).status == TopicStatus.CLOSED

    relation = (
        kb.TopicPrerequisite.objects
        .get(prerequisite=nodes["t1"], topic=nodes["t3"])
    )
    kb.remove_prerequisite(relation.pk)
    clear_local_cache()
    readiness.states_for(user=student)

    assert _state(student, nodes["t3"]).missing_count == 0
    assert _state(student, nodes["t3"]).status == TopicStatus.OPEN


# ---------------------------------------------------------------------------
# Status transitions driven by real answers
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_open_to_in_progress_to_mastered(student, reference_course):
    topic = reference_course["t1"]
    TopicModelParams.objects.create(topic=topic, p0=0.3, pt=0.1, g0=0.2, s0=0.05)
    readiness.states_for(user=student)
    assert _state(student, topic).status == TopicStatus.OPEN

    question, right, _ = _question(topic, "Q0")
    result = _submit(student, question, right)
    assert result.status == TopicStatus.IN_PROGRESS
    assert _state(student, topic).started_at is not None

    for index in range(1, 6):
        question, right, _ = _question(topic, f"Q{index}")
        result = _submit(student, question, right)

    assert result.status == TopicStatus.MASTERED
    assert result.mastered is True
    assert _state(student, topic).mastered_flag is True


@pytest.mark.django_db
def test_accuracy_and_attempts_follow_the_answers(student, reference_course):
    topic = reference_course["t1"]
    for text, correct in (("a", True), ("b", False), ("c", True), ("d", True)):
        question, right, wrong = _question(topic, text)
        result = _submit(student, question, right if correct else wrong)

    assert result.attempts == 4
    assert result.accuracy == pytest.approx(0.75)
    state = _state(student, topic)
    assert (state.attempts, state.correct) == (4, 3)


@pytest.mark.django_db
def test_answering_an_open_topic_opens_what_depends_on_it(student, reference_course):
    """The end-to-end version of Algorithm 2.3: real answers open t3."""
    nodes = reference_course
    TopicModelParams.objects.create(topic=nodes["t1"], p0=0.3, pt=0.1, g0=0.2, s0=0.05)
    readiness.states_for(user=student)
    assert _state(student, nodes["t3"]).status == TopicStatus.CLOSED

    opened: tuple[int, ...] = ()
    for index in range(6):
        question, right, _ = _question(nodes["t1"], f"Q{index}")
        result = _submit(student, question, right)
        opened = opened or result.opened_topics

    assert nodes["t3"].pk in opened
    assert _state(student, nodes["t3"]).status == TopicStatus.OPEN


# ---------------------------------------------------------------------------
# A closed topic answers 403 with the unmet prerequisites
# ---------------------------------------------------------------------------

@pytest.fixture
def api(student):
    client = APIClient()
    client.force_authenticate(student)
    return client


@pytest.mark.django_db
def test_submit_answer_refuses_a_closed_topic(student, reference_course, api):
    nodes = reference_course
    question, right, _ = _question(nodes["t3"], "Q")

    response = api.post(
        "/api/assessments/submit_answer/",
        {"question_id": question.pk, "choice_id": right.pk},
        format="json",
    )

    assert response.status_code == 403
    body = response.json()
    assert [item["topic_id"] for item in body["missing"]] == [nodes["t1"].pk]
    assert body["missing"][0]["name"] == "t1"
    assert body["missing"][0]["p_mastery"] == 0.0
    assert not AssessmentAttempt.objects.filter(user=student).exists()


@pytest.mark.django_db
def test_next_question_refuses_a_closed_topic(student, reference_course, api):
    nodes = reference_course
    _question(nodes["t6"], "Q")

    response = api.get(f"/api/assessments/next_question/?topic_id={nodes['t6'].pk}")

    assert response.status_code == 403
    assert {item["topic_id"] for item in response.json()["missing"]} == {
        nodes["t3"].pk, nodes["t4"].pk, nodes["t5"].pk,
    }


@pytest.mark.django_db
def test_test_session_refuses_a_closed_topic(student, reference_course, api):
    nodes = reference_course
    _question(nodes["t3"], "Q")

    response = api.get(f"/api/assessments/test_session/?topic_id={nodes['t3'].pk}")

    assert response.status_code == 403
    assert response.json()["missing"][0]["topic_id"] == nodes["t1"].pk


@pytest.mark.django_db
def test_an_open_topic_is_served_normally(student, reference_course, api):
    nodes = reference_course
    _question(nodes["t1"], "Q")

    response = api.get(f"/api/assessments/next_question/?topic_id={nodes['t1'].pk}")
    assert response.status_code == 200

    response = api.get(f"/api/assessments/test_session/?topic_id={nodes['t1'].pk}")
    assert response.status_code == 200


@pytest.mark.django_db
def test_the_missing_list_is_in_programme_order(student, reference_course, api):
    nodes = reference_course
    _question(nodes["t6"], "Q")

    response = api.get(f"/api/assessments/next_question/?topic_id={nodes['t6'].pk}")

    pos = get_snapshot().pos
    returned = [item["topic_id"] for item in response.json()["missing"]]
    assert returned == sorted(returned, key=lambda pk: (pos[pk], pk))


@pytest.mark.django_db
def test_a_started_topic_stays_answerable_after_a_new_prerequisite(student, reference_course, api):
    """TY5 through the endpoint: no 403 for a topic the learner has begun."""
    nodes = reference_course
    question, right, _ = _question(nodes["t1"], "Q")
    _submit(student, question, right)

    kb.add_prerequisite(prerequisite=nodes["t2"], topic=nodes["t1"])
    clear_local_cache()

    second, right2, _ = _question(nodes["t1"], "Q2")
    response = api.post(
        "/api/assessments/submit_answer/",
        {"question_id": second.pk, "choice_id": right2.pk},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_the_service_refusal_and_the_endpoint_agree(student, reference_course):
    """``process_submission`` raises; the view is what turns it into a 403."""
    nodes = reference_course
    question, right, _ = _question(nodes["t3"], "Q")

    with pytest.raises(TopicClosed) as refused:
        _submit(student, question, right)

    assert refused.value.payload()["missing"][0]["topic_id"] == nodes["t1"].pk


# ---------------------------------------------------------------------------
# One vocabulary across the endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_every_student_endpoint_reports_the_same_state(student, reference_course, api):
    """
    Audit 3.4: the tree used to report ``score`` as ``mastery_percentage``
    while the dashboard reported the probability. Now every endpoint carries
    ``p_mastery``, ``accuracy`` and ``status`` for the same topic.
    """
    topic = reference_course["t1"]
    TopicModelParams.objects.create(topic=topic, p0=0.3, pt=0.1, g0=0.2, s0=0.05)
    question, right, wrong = _question(topic, "Q")
    _submit(student, question, right)
    second, right2, _ = _question(topic, "Q2")
    _submit(student, second, right2)

    expected = _state(student, topic)

    def find(nodes, pk):
        for node in nodes:
            if node.get("id") == pk or node.get("topic_id") == pk:
                return node
            found = find(node.get("children", []), pk)
            if found:
                return found
        return None

    tree = api.get("/api/learning_path/tree/").json()
    in_tree = find(tree, topic.pk)
    assert in_tree is not None
    assert in_tree["p_mastery"] == pytest.approx(expected.p_mastery)
    assert in_tree["accuracy"] == pytest.approx(expected.accuracy)
    assert in_tree["status"] == expected.status

    graph = api.get("/api/curriculum/prerequisite-graph/").json()
    in_graph = next(n for n in graph["nodes"] if n["id"] == str(topic.pk))
    assert in_graph["data"]["p_mastery"] == pytest.approx(expected.p_mastery)
    assert in_graph["data"]["accuracy"] == pytest.approx(expected.accuracy)
    assert in_graph["data"]["status"] == expected.status

    tests = api.get("/api/assessments/tests/").json()
    in_tests = next(t for t in tests if t["id"] == topic.pk)
    assert in_tests["p_mastery"] == pytest.approx(expected.p_mastery)
    assert in_tests["accuracy"] == pytest.approx(expected.accuracy)
    assert in_tests["status"] == expected.status

    states = api.get("/api/knowledge_states/").json()
    rows = states["results"] if isinstance(states, dict) else states
    in_states = next(r for r in rows if r["topic"] == topic.pk)
    assert in_states["p_mastery"] == pytest.approx(expected.p_mastery)
    assert in_states["accuracy"] == pytest.approx(expected.accuracy)
    assert in_states["status"] == expected.status


@pytest.mark.django_db
def test_the_dashboard_counts_statuses_not_thresholds(student, reference_course, api):
    nodes = reference_course
    _set_state(
        student, nodes["t1"], p_mastery=0.80, mastered=True,
        status=TopicStatus.MASTERED, started=True,
    )
    readiness.resync(user=student, snapshot=get_snapshot())

    body = api.get("/api/analytics/overview/").json()

    # M is set even though P(L) is below τ — hysteresis, not a threshold.
    assert body["topics_mastered"] == 1
    assert body["topics_unlocked"] >= 1
