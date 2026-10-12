"""
Group C — full scenarios over HTTP (stages 4-6).

V-C2   the learner's initial states and the missing prerequisites of a closed
       topic;
V-C3   every recorded number of a fixed answer sequence equals an independent
       replay, and p̂ comes from the state *before* the update;
V-C4   t6 opens exactly after the last of its three prerequisites; before that
       both t6 endpoints answer 403 and name what is missing;
V-C5   TY5: a new prerequisite does not close a started topic, but does close
       an untouched open one;
V-C6   TY6: after a KB change the counters are recomputed on the next request;
V-C7   the trajectory's groups, reason codes, review priority and Need(t7);
V-C8   the test session goes through the engine with ``source=test_session``,
       its grade is stored apart from P(L), and passing opens nothing;
V-C9   no synthetic rows: one ledger row per submitted answer, ``attempt_no``
       without gaps;
V-C10  one scale: p_mastery ∈ [0, 1] and the same number from every endpoint;
V-C11  permissions: anonymous 401, a learner on instructor routes 403, an
       instructor without ``is_staff`` on their own routes 200;
V-C12  the same question again inside the window is ``review_repeat`` and does
       not move P(L).

Everything goes through the API. Expected numbers come from
``verification.oracle.model``, never from the prototype's own helpers. Each
topic gets several distinct questions, because answering the *same* question
twice is a ``review_repeat`` by D25 and deliberately does not move P(L).
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from django.conf import settings

from verification.oracle import model as oracle

THESIS = settings.THESIS_MODEL
PASSWORD = "Verify-C-passw0rd!"
TOPIC_SLUGS = ("t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _client(user=None):
    from rest_framework.test import APIClient

    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _user(email, **extra):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email=email, password=PASSWORD, first_name="Talaba", last_name="Tekshiruv", **extra
    )


def _question(topic_id: int, label: str, *, b_q: float = 0.0):
    from assessments.models import Choice, Question

    question = Question.objects.create(
        topic_id=topic_id, text=f"V-C question {label}", irt_difficulty=b_q,
    )
    right = Choice.objects.create(question=question, text="right", is_correct=True)
    wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
    return question, right, wrong


def _submit(user, question, choice):
    return _client(user).post(
        "/api/assessments/submit_answer/",
        {"question_id": question.pk, "choice_id": choice.pk},
        format="json",
    )


def _answer(user, question, choice):
    response = _submit(user, question, choice)
    assert response.status_code == 200, (response.status_code, response.content[:300])
    from assessments.models import AssessmentAttempt

    return AssessmentAttempt.objects.filter(user=user).order_by("-id").first(), response.json()


def _states(user) -> dict[int, dict]:
    response = _client(user).get("/api/knowledge_states/")
    assert response.status_code == 200, response.content
    payload = response.json()
    rows = payload["results"] if isinstance(payload, dict) and "results" in payload else payload
    return {row["topic"]: row for row in rows}


def _trajectory(user) -> dict:
    response = _client(user).get("/api/learning/trajectory/")
    assert response.status_code == 200, response.content
    return response.json()


def _constants() -> dict:
    return dict(
        g_max=THESIS["G_MAX"], s_max=THESIS["S_MAX"], a_q=THESIS["A_Q"],
        elo_alpha=THESIS["ELO_ALPHA"], elo_beta=THESIS["ELO_BETA"],
        lam=THESIS["LAMBDA"], cap=THESIS["TAU"] - THESIS["C_OFFSET"],
        theta_clamp=THESIS["THETA_CLAMP"],
    )


def _default_params() -> dict:
    return dict(
        p0=THESIS["DEFAULT_P0"], pt=THESIS["DEFAULT_PT"],
        g0=THESIS["DEFAULT_G0"], s0=THESIS["DEFAULT_S0"],
    )


@dataclass
class Learner:
    """One learner and six distinct questions per topic of the course."""

    user: object
    questions: dict[str, list[tuple]]

    def one(self, slug: str, index: int = 0) -> tuple:
        return self.questions[slug][index]


@pytest.fixture
def learner(reference_course) -> Learner:
    user = _user("v-c.learner@verify-c.example")
    questions = {
        slug: [
            _question(reference_course.id_of[slug], f"{slug}-{i}") for i in range(6)
        ]
        for slug in TOPIC_SLUGS
    }
    return Learner(user=user, questions=questions)


def _master(learner: Learner, slug: str) -> dict:
    """Answer distinct questions of ``slug`` correctly until M = 1."""
    payload = {}
    for question, right, _ in learner.questions[slug]:
        _, payload = _answer(learner.user, question, right)
        if payload["status"] == "mastered":
            return payload
    raise AssertionError(f"{slug} did not reach mastered: {payload}")


def _missing_ids(payload) -> set[int]:
    """The ``missing`` list of a 403 body or a trajectory item, as topic ids."""
    rows = payload.get("missing") or payload.get("missing_prerequisites") or []
    return {row["topic_id"] if isinstance(row, dict) else row for row in rows}


# ---------------------------------------------------------------------------
# V-C2 — the initial states
# ---------------------------------------------------------------------------


def test_v_c2_only_t1_and_t2_start_open_with_the_right_missing_counts(
    reference_course, learner
):
    """
    Pre(t1) = Pre(t2) = ∅, so those two are open; every other topic is closed
    with ``missing_count`` = |Pre(w)| and its missing prerequisites named.
    """
    course = reference_course
    states = _states(learner.user)
    assert {course.slug_of[t] for t in states} == set(TOPIC_SLUGS), (
        "the learner has one state row per topic, sections excluded"
    )

    open_slugs = {
        course.slug_of[topic] for topic, row in states.items() if row["status"] == "open"
    }
    assert open_slugs == {"t1", "t2"}

    expected_counts = {"t3": 1, "t4": 1, "t5": 1, "t6": 3, "t7": 2, "t8": 2}
    for slug, count in expected_counts.items():
        row = states[course.id_of[slug]]
        assert row["status"] == "closed", slug
        assert row["missing_count"] == count, slug
        assert row["p_mastery"] == 0.0 and row["attempts"] == 0, slug

    # the names behind the counters, from the trajectory's closed group
    closed = {
        course.slug_of[item["topic_id"]]: {
            course.slug_of[m["topic_id"]] for m in item["missing"]
        }
        for item in _trajectory(learner.user)["groups"]["D"]
    }
    assert closed == {
        "t3": {"t1"}, "t4": {"t2"}, "t5": {"t1"},
        "t6": {"t3", "t4", "t5"}, "t7": {"t4", "t6"}, "t8": {"t4", "t6"},
    }


# ---------------------------------------------------------------------------
# V-C3 — the recorded numbers equal an independent replay
# ---------------------------------------------------------------------------


def test_v_c3_the_ledger_replays_exactly_and_p_hat_precedes_the_update(
    reference_course, learner
):
    """
    Six answers on t1 (open, Pre = ∅, so P(L0) = P0), one per question:
    correct, wrong, correct, correct, wrong, correct. Every stored column is
    compared with the oracle's replay; p̂ is then re-derived from ``p_before``
    and shown to differ from the same formula over ``p_after``, which is what
    "p̂ is computed before the update" means.
    """
    pattern = [True, False, True, True, False, True]
    params, constants = _default_params(), _constants()
    p_l, theta = None, 0.0
    b_by_question: dict[int, float] = {}
    n_student = 0

    for index, is_correct in enumerate(pattern):
        question, right, wrong = learner.one("t1", index)
        b_q = b_by_question.get(question.pk, 0.0)
        row, _ = _answer(learner.user, question, right if is_correct else wrong)

        expected = oracle.observe(
            **params, **constants,
            is_correct=is_correct, p_l=p_l, theta=theta, b_q=b_q,
            n_student=n_student, n_question=0, prerequisites=(),
        )
        for name, mine, theirs in (
            ("p_before", row.p_before, expected.p_before),
            ("p_hat", row.p_hat, expected.p_hat),
            ("p_after", row.p_after, expected.p_after),
            ("guess_used", row.guess_used, expected.guess),
            ("slip_used", row.slip_used, expected.slip),
            ("theta_before", row.theta_before, theta),
            ("b_before", row.b_before, b_q),
            ("theta_after", row.theta_after, expected.theta_after),
            ("b_after", row.b_after, expected.b_after),
        ):
            assert mine == pytest.approx(theirs, abs=1e-9), (index, name, mine, theirs)

        assert row.p_hat == pytest.approx(
            oracle.predict(p_l=row.p_before, guess=row.guess_used, slip=row.slip_used),
            abs=1e-9,
        ), index
        assert row.p_hat != pytest.approx(
            oracle.predict(p_l=row.p_after, guess=row.guess_used, slip=row.slip_used),
            abs=1e-6,
        ), index

        p_l, theta = expected.p_after, expected.theta_after
        b_by_question[question.pk] = expected.b_after
        n_student += 1

    assert _states(learner.user)[learner.one("t1")[0].topic_id][
        "p_mastery"
    ] == pytest.approx(p_l, abs=1e-9)


def test_v_c3_the_first_answer_of_a_topic_with_prerequisites_starts_from_p_l0(
    reference_course, learner
):
    """
    Pre(t3) = {t1}. The first answer on t3 must start from
    P(L0) = min{(1−λ)P0 + λ·m̄, τ − C_OFFSET} with m̄ taken from the learner's
    P(L) on t1 — not from P0 alone.
    """
    course = reference_course
    payload = _master(learner, "t1")
    assert course.id_of["t3"] in payload["opened_topics"]
    p_t1 = _states(learner.user)[course.id_of["t1"]]["p_mastery"]

    question, right, _ = learner.one("t3")
    row, _ = _answer(learner.user, question, right)

    params, constants = _default_params(), _constants()
    expected = oracle.initial_mastery(
        p0=params["p0"],
        prerequisites=(oracle.Pre(weight=1.0, p_l=p_t1, p0=params["p0"]),),
        lam=constants["lam"], cap=constants["cap"],
    )
    assert row.p_before == pytest.approx(expected, abs=1e-9)
    assert row.p_before != pytest.approx(params["p0"], abs=1e-6), (
        "P(L0) must see the prerequisite, otherwise λ is not applied"
    )
    assert row.p_before <= constants["cap"] + 1e-12


# ---------------------------------------------------------------------------
# V-C4 — t6 opens exactly when section 4 says
# ---------------------------------------------------------------------------


def test_v_c4_a_closed_topic_answers_403_and_names_its_missing_prerequisites(
    reference_course, learner
):
    course = reference_course
    question, right, _ = learner.one("t6")

    blocked = _submit(learner.user, question, right)
    assert blocked.status_code == 403, blocked.content[:300]
    assert {course.slug_of[i] for i in _missing_ids(blocked.json())} == {"t3", "t4", "t5"}

    nexts = _client(learner.user).get(
        "/api/assessments/next_question/", {"topic_id": course.id_of["t6"]}
    )
    assert nexts.status_code == 403, nexts.content[:300]
    assert {course.slug_of[i] for i in _missing_ids(nexts.json())} == {"t3", "t4", "t5"}

    from assessments.models import AssessmentAttempt

    assert not AssessmentAttempt.objects.filter(user=learner.user).exists(), (
        "a refused answer must not reach the ledger"
    )


def test_v_c4_t6_opens_only_after_the_last_of_its_three_prerequisites(
    reference_course, learner
):
    course = reference_course
    opened = {}
    for slug in ("t1", "t2", "t3", "t5", "t4"):
        opened[slug] = set(_master(learner, slug)["opened_topics"])
        if slug != "t4":
            assert _states(learner.user)[course.id_of["t6"]]["status"] == "closed", slug

    assert course.id_of["t6"] in opened["t4"], opened
    states = _states(learner.user)
    assert states[course.id_of["t6"]]["status"] == "open"
    for slug in ("t7", "t8"):
        assert states[course.id_of[slug]]["status"] == "closed"
        assert states[course.id_of[slug]]["missing_count"] == 1, (
            "t4 is mastered, so only t6 is still missing"
        )

    question, right, _ = learner.one("t6")
    assert _submit(learner.user, question, right).status_code == 200


# ---------------------------------------------------------------------------
# V-C5 / V-C6 — TY5 and TY6
# ---------------------------------------------------------------------------


def test_v_c5_a_new_prerequisite_never_closes_a_started_topic(reference_course, learner):
    """
    TY5: t2 has been answered (``in_progress``) and t1 has not (``open``).
    Adding t5 → t2 and t5 → t1 must leave t2 started and close t1.
    """
    from curriculum.services import kb

    course = reference_course
    question, right, _ = learner.one("t2")
    _answer(learner.user, question, right)
    assert _states(learner.user)[course.id_of["t2"]]["status"] == "in_progress"

    # t5 → t2 is legal. For t1 a fresh topic is needed: after t5 → t2 every
    # existing topic is already a descendant of t1, so any of them as a new
    # prerequisite of t1 would close a cycle (Y3, V-B2's case).
    kb.add_prerequisite(prerequisite=course.id_of["t5"], topic=course.id_of["t2"])
    fresh = kb.create_node(
        name="Yangi prerekvizit", slug="v-c-tz", parent=course.id_of["B1"], kind="topic",
    ).pk
    kb.add_prerequisite(prerequisite=fresh, topic=course.id_of["t1"])

    states = _states(learner.user)
    assert states[course.id_of["t2"]]["status"] == "in_progress", (
        "a started topic must never fall back to closed (TY5)"
    )
    assert states[course.id_of["t2"]]["missing_count"] == 1, (
        "the new prerequisite is still counted, it just does not close the topic"
    )
    assert states[course.id_of["t1"]]["status"] == "closed"
    assert states[course.id_of["t1"]]["missing_count"] == 1

    # The new prerequisite comes back as a recommendation of its own: t2 stays
    # in the started group, the newly closed t1 moves to the blocked group with
    # its new prerequisite named, and t5 is listed as work to do (here in the
    # blocked group, because t5's own prerequisite t1 is not mastered either).
    groups = _trajectory(learner.user)["groups"]
    placed = {
        course.slug_of[item["topic_id"]]: name
        for name, items in groups.items() for item in items
        if item["topic_id"] in course.slug_of
    }
    assert placed["t2"] == "B", placed
    assert placed["t1"] == "D", placed
    assert "t5" in placed, placed
    t1_item = next(i for i in groups["D"] if i["topic_id"] == course.id_of["t1"])
    assert {m["name"] for m in t1_item["missing"]} == {"Yangi prerekvizit"}


def test_v_c6_the_counters_are_recomputed_after_a_kb_change(reference_course, learner):
    """
    TY6: the state rows carry ``kb_version``; after the KB moves, the next
    request recomputes the counters, and the recomputed number equals an
    independent count over the new graph.
    """
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    from verification.oracle import graph as og

    course = reference_course
    version_before = _trajectory(learner.user)["kb_version"]
    assert _states(learner.user)[course.id_of["t6"]]["missing_count"] == 3

    edge = TopicPrerequisite.objects.get(
        prerequisite_id=course.id_of["t5"], topic_id=course.id_of["t6"]
    )
    kb.remove_prerequisite(edge.pk)

    # The counter is over E_L, the leaf graph, so the oracle rebuilds E_L from
    # the new tree and E_P: t4 → B3 still lands on t6 as an inherited edge.
    expected_edges = og.inherited_edges(course.oracle_tree(), course.oracle_prereqs())
    independent = {
        x for (x, y) in expected_edges if y == course.id_of["t6"]
    }
    assert {course.slug_of[x] for x in independent} == {"t3", "t4"}

    after = _states(learner.user)[course.id_of["t6"]]
    assert after["missing_count"] == len(independent) == 2
    assert after["status"] == "closed"
    assert _trajectory(learner.user)["kb_version"] > version_before


# ---------------------------------------------------------------------------
# V-C7 — the trajectory
# ---------------------------------------------------------------------------


def test_v_c7_the_groups_come_in_order_with_structured_reasons(reference_course, learner):
    course = reference_course
    _master(learner, "t1")
    question, right, _ = learner.one("t2")
    _answer(learner.user, question, right)

    trajectory = _trajectory(learner.user)
    assert list(trajectory["groups"]) == ["A", "B", "C", "D"], trajectory["groups"].keys()

    by_group = {
        name: [course.slug_of[item["topic_id"]] for item in items]
        for name, items in trajectory["groups"].items()
    }
    assert by_group["B"] == ["t2"], by_group
    assert "t3" in by_group["C"] and "t5" in by_group["C"], by_group
    assert by_group["D"] == sorted(
        by_group["D"], key=lambda s: ("t6", "t7", "t8").index(s) if s in ("t6", "t7", "t8") else -1
    ), by_group

    for name, items in trajectory["groups"].items():
        for item in items:
            assert item["group"] == name, item
            assert isinstance(item["reason"], dict) and item["reason"].get("code"), item
            assert isinstance(item["reason"].get("params"), dict), item
            assert 0.0 <= item["p_mastery"] <= 1.0, item
            if name == "D":
                assert item["missing"], item
                assert item["reason"]["params"]["missing"] == len(item["missing"]), item


def test_v_c7_review_priority_is_t1_then_t3_and_need_of_t7_is_t4_and_t6(
    reference_course, learner
):
    """
    Section 4's trajectory case: t1 and t3 in review (0.80 and 0.70), t5
    mastered, t6-t8 not. Expected order t1 (impact 4) then t3 (impact 3), and
    Need(t7) = {t4, t6} with the path t4 → t6 → t7.
    """
    from assessments.models import StudentTopicState

    course = reference_course
    for slug in ("t1", "t2", "t3", "t5"):
        _master(learner, slug)
    # t4 is started but not mastered — section 4's state, where t6 is still
    # closed and Need(t7) therefore contains t4 as well as t6.
    question, right, _ = learner.one("t4")
    _answer(learner.user, question, right)
    assert _states(learner.user)[course.id_of["t4"]]["status"] == "in_progress"

    # Need(t7) belongs to the state before the review: t1, t2, t3, t5 mastered
    # and t4 started, so only t4 and t6 are still missing on the way to t7.
    response = _client(learner.user).get(f"/api/learning/path-to/{course.id_of['t7']}/")
    assert response.status_code == 200, response.content
    payload = response.json()
    assert payload["goal_id"] == course.id_of["t7"]
    assert {course.slug_of[row["topic_id"]] for row in payload["need"]} == {"t4", "t6"}
    assert [course.slug_of[row["topic_id"]] for row in payload["path"]] == [
        "t4", "t6", "t7",
    ], payload["path"]

    # Put t1 and t3 into review with the mastery section 4 names. The status
    # machine itself is checked in V-C4 and V-A3; here the trajectory's order
    # is what is under test.
    for slug, value in (("t1", 0.80), ("t3", 0.70)):
        state = StudentTopicState.objects.get(
            user=learner.user, topic_id=course.id_of[slug]
        )
        state.p_mastery = value
        state.mastered_flag = False
        state.status = "review"
        state.save(update_fields=["p_mastery", "mastered_flag", "status"])

    review = _trajectory(learner.user)["groups"]["A"]
    assert [course.slug_of[i["topic_id"]] for i in review][:2] == ["t1", "t3"], review
    impacts = {
        course.slug_of[i["topic_id"]]: i["reason"]["params"].get("impact") for i in review
    }
    assert impacts["t1"] == 4 and impacts["t3"] == 3, impacts
    assert review[0]["reason"]["code"] == "review_impact", review[0]

    # Once t3 falls back to review (M = 0) it joins Need(t7) again, because
    # t3 → t6 → t7 and the search stops only at a mastered or open topic.
    after_review = _client(learner.user).get(
        f"/api/learning/path-to/{course.id_of['t7']}/"
    ).json()
    assert {course.slug_of[row["topic_id"]] for row in after_review["need"]} == {
        "t3", "t4", "t6",
    }
    assert [course.slug_of[row["topic_id"]] for row in after_review["path"]][-1] == "t7"


# ---------------------------------------------------------------------------
# V-C8 — the test session
# ---------------------------------------------------------------------------


def test_v_c8_a_test_session_goes_through_the_engine_and_keeps_its_grade_apart(
    reference_course, learner
):
    from assessments.models import (
        AssessmentAttempt, AttemptSource, TestSessionResult,
    )

    course = reference_course
    topic = course.id_of["t1"]

    session = _client(learner.user).get(
        "/api/assessments/test_session/", {"topic_id": topic}
    )
    assert session.status_code == 200, session.content[:300]
    questions = session.json()["questions"]
    assert questions, session.json()
    for question in questions:
        assert "is_correct" not in str(question["choices"]), "the key must stay hidden"

    from assessments.models import Choice

    answers = [
        {
            "question_id": question["id"],
            "choice_id": Choice.objects.filter(
                question_id=question["id"], is_correct=True
            ).values_list("pk", flat=True).first(),
        }
        for question in questions
    ]
    submitted = _client(learner.user).post(
        "/api/assessments/submit_test_session/",
        {"topic_id": topic, "answers": answers},
        format="json",
    )
    assert submitted.status_code == 200, submitted.content[:300]
    result = submitted.json()

    rows = AssessmentAttempt.objects.filter(user=learner.user, topic_id=topic)
    assert rows.count() == len(answers)
    assert set(rows.values_list("source", flat=True)) == {AttemptSource.TEST_SESSION}
    for row in rows:
        assert row.engine_version.startswith("thesis_hybrid"), row.engine_version
        assert row.p_hat is not None and row.p_after is not None, (
            "a test answer is a model observation too"
        )

    # the grade is its own number in its own table, and not p_mastery
    stored = TestSessionResult.objects.filter(user=learner.user, topic_id=topic)
    assert stored.count() == 1
    assert result["grade_percentage"] == pytest.approx(100.0, abs=1e-9)
    assert result["is_passed"] is True
    state = _states(learner.user)[topic]
    assert result["grade_percentage"] != pytest.approx(state["p_mastery"] * 100.0, abs=1e-6)
    assert 0.0 <= state["p_mastery"] <= 1.0

    # passing a test opens nothing by itself: the only opened topics are the
    # ones Algorithm 2.3 opened from the answers, and they are reported
    for topic_id in result["opened_topics"]:
        assert _states(learner.user)[topic_id]["missing_count"] == 0


def test_v_c8_a_test_session_of_a_closed_topic_is_refused(reference_course, learner):
    course = reference_course
    response = _client(learner.user).get(
        "/api/assessments/test_session/", {"topic_id": course.id_of["t6"]}
    )
    assert response.status_code == 403, response.content[:200]
    assert {course.slug_of[i] for i in _missing_ids(response.json())} == {"t3", "t4", "t5"}


# ---------------------------------------------------------------------------
# V-C9 — no synthetic rows
# ---------------------------------------------------------------------------


def test_v_c9_one_ledger_row_per_submitted_answer_without_gaps(reference_course, learner):
    from assessments.models import AssessmentAttempt

    course = reference_course
    submitted = 0
    for slug in ("t1", "t2"):
        for index, (question, right, wrong) in enumerate(learner.questions[slug][:4]):
            _answer(learner.user, question, right if index % 2 == 0 else wrong)
            submitted += 1

    rows = AssessmentAttempt.objects.filter(user=learner.user)
    assert rows.count() == submitted, (rows.count(), submitted)
    for slug in ("t1", "t2"):
        numbers = list(
            rows.filter(topic_id=course.id_of[slug]).order_by("attempt_no")
            .values_list("attempt_no", flat=True)
        )
        assert numbers == list(range(1, len(numbers) + 1)), (slug, numbers)
    assert rows.filter(source="adaptive").count() == submitted, (
        "nothing was recorded under another source"
    )


# ---------------------------------------------------------------------------
# V-C10 — one scale
# ---------------------------------------------------------------------------


def _mastery_from_tree(payload, topic_id: int):
    found = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("id") == topic_id and "p_mastery" in node:
                found.append(node["p_mastery"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    assert len(found) == 1, (topic_id, found)
    return found[0]


def test_v_c10_every_endpoint_reports_the_same_p_mastery(reference_course, learner):
    course = reference_course
    # Two answers, not mastery: a mastered topic has left the trajectory's four
    # groups, and the trajectory is one of the endpoints being compared.
    for index in (0, 1):
        question, right, _ = learner.one("t1", index)
        _answer(learner.user, question, right)
    topic = course.id_of["t1"]

    states = _states(learner.user)
    assert states[topic]["status"] == "in_progress"
    expected = states[topic]["p_mastery"]
    assert 0.0 <= expected <= 1.0

    seen = {"knowledge_states": expected}

    tree = _client(learner.user).get("/api/learning_path/tree/")
    assert tree.status_code == 200, tree.content
    seen["tree"] = _mastery_from_tree(tree.json(), topic)

    graph = _client(learner.user).get("/api/curriculum/prerequisite-graph/")
    assert graph.status_code == 200, graph.content
    nodes = {int(node["id"]): node["data"] for node in graph.json()["nodes"]}
    seen["graph"] = nodes[topic]["p_mastery"]

    tests = _client(learner.user).get("/api/assessments/tests/")
    assert tests.status_code == 200, tests.content
    seen["tests"] = next(
        row["p_mastery"] for row in tests.json() if row["id"] == topic
    )

    overview = _client(learner.user).get("/api/analytics/overview/")
    assert overview.status_code == 200, overview.content
    strongest = overview.json()["strongest_topic"]
    assert strongest["topic_id"] == topic, strongest
    seen["dashboard"] = strongest["p_mastery"]

    flat = [
        item for group in _trajectory(learner.user)["groups"].values() for item in group
    ]
    seen["trajectory"] = next(i["p_mastery"] for i in flat if i["topic_id"] == topic)

    for name, value in seen.items():
        assert 0.0 <= value <= 1.0, (name, value)
        assert value == pytest.approx(expected, abs=5e-4), (name, seen)
    assert len(seen) == 6, seen


def test_v_c10_a_state_row_keeps_p_mastery_inside_the_unit_interval(
    reference_course, learner
):
    """Every answer of a long mixed run leaves every endpoint inside [0, 1]."""
    for slug in ("t1", "t2"):
        for index, (question, right, wrong) in enumerate(learner.questions[slug]):
            _, payload = _answer(learner.user, question, right if index % 3 else wrong)
            assert 0.0 <= payload["p_mastery"] <= 1.0, payload
            assert 0.0 <= payload["accuracy"] <= 1.0, payload
    for row in _states(learner.user).values():
        assert 0.0 <= row["p_mastery"] <= 1.0, row


# ---------------------------------------------------------------------------
# V-C11 — permissions
# ---------------------------------------------------------------------------

STUDENT_ROUTES = (
    "/api/knowledge_states/",
    "/api/learning/trajectory/",
    "/api/learning_path/tree/",
    "/api/assessments/tests/",
)
INSTRUCTOR_ROUTES = (
    "/api/curriculum/instructor/topics/",
    "/api/curriculum/instructor/prerequisites/",
    "/api/assessments/instructor/questions/",
    "/api/curriculum/instructor/kb/warnings/",
)


@pytest.mark.parametrize("route", STUDENT_ROUTES + INSTRUCTOR_ROUTES)
def test_v_c11_an_anonymous_request_is_401(reference_course, route):
    response = _client().get(route)
    assert response.status_code == 401, (route, response.status_code)


@pytest.mark.parametrize("route", INSTRUCTOR_ROUTES)
def test_v_c11_a_learner_on_an_instructor_route_is_403(reference_course, learner, route):
    response = _client(learner.user).get(route)
    assert response.status_code == 403, (route, response.status_code)


@pytest.mark.parametrize("route", INSTRUCTOR_ROUTES)
def test_v_c11_an_instructor_without_is_staff_may_use_their_own_routes(
    reference_course, route
):
    from django.contrib.auth.models import Group

    teacher = _user("v-c.teacher@verify-c.example")
    teacher.groups.add(Group.objects.get_or_create(name="Instructor")[0])
    assert teacher.is_staff is False

    response = _client(teacher).get(route)
    assert response.status_code == 200, (route, response.status_code, response.content[:200])


def test_v_c11_a_learner_cannot_write_through_an_instructor_route(
    reference_course, learner
):
    course = reference_course
    response = _client(learner.user).post(
        "/api/curriculum/instructor/prerequisites/",
        {"prerequisite": course.id_of["t8"], "topic": course.id_of["t3"]},
        format="json",
    )
    assert response.status_code == 403, response.content[:200]

    from curriculum.models import TopicPrerequisite

    assert not TopicPrerequisite.objects.filter(
        prerequisite_id=course.id_of["t8"], topic_id=course.id_of["t3"]
    ).exists()


# ---------------------------------------------------------------------------
# V-C12 — the repeated answer
# ---------------------------------------------------------------------------


def test_v_c12_the_same_question_again_is_review_repeat_and_does_not_move_p_l(
    reference_course, learner
):
    from assessments.models import AttemptSource

    question, right, wrong = learner.one("t1")
    first, _ = _answer(learner.user, question, right)
    assert first.source == AttemptSource.ADAPTIVE

    before = _states(learner.user)[question.topic_id]["p_mastery"]
    repeat, payload = _answer(learner.user, question, wrong)

    assert repeat.source == AttemptSource.REVIEW_REPEAT, repeat.source
    assert payload["source"] == AttemptSource.REVIEW_REPEAT
    assert repeat.p_after is None, "a review_repeat row carries no new P(L)"
    after = _states(learner.user)[question.topic_id]["p_mastery"]
    assert after == pytest.approx(before, abs=1e-12), (before, after)

    # a different question of the same topic does move it
    other, other_right, _ = learner.one("t1", 1)
    moved, _ = _answer(learner.user, other, other_right)
    assert moved.source == AttemptSource.ADAPTIVE
    assert _states(learner.user)[question.topic_id]["p_mastery"] > before
