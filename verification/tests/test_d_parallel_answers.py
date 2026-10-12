"""
V-D1 — ten answers to one topic at the same moment.

The specification asks for three things from such a race:

* ``attempt_no`` comes out 1..n with no repeats and no gaps;
* the final P(L) equals a sequential replay of the answers in ``attempt_no``
  order — the lock must serialise the updates, not interleave them;
* nothing is swallowed: every request either committed a row or failed loudly.

The replay comparison is done against ``verification.oracle.model``, so the
ledger is checked against an independent transcription of algorithm 2.4 rather
than against the prototype's own engine.

Real commits and real connections are needed (``transactional_db``), so this
module must not run under xdist.
"""

from __future__ import annotations

import threading

import pytest
from django.conf import settings

from verification.oracle import model as oracle

THESIS = settings.THESIS_MODEL
PARALLEL = 10
PASSWORD = "Verify-D-passw0rd!"


@pytest.fixture
def world(transactional_db):
    """A one-topic course, a learner, and ten distinct questions on that topic."""
    from assessments.models import Choice, Question
    from django.contrib.auth import get_user_model
    from curriculum.services import kb

    course = kb.create_node(name="Parallel course", slug="v-d-course", kind="course")
    section = kb.create_node(
        name="Parallel section", slug="v-d-section", parent=course.pk, kind="section"
    )
    topic = kb.create_node(
        name="Parallel topic", slug="v-d-topic", parent=section.pk, kind="topic"
    )

    user = get_user_model().objects.create_user(
        email="v-d.learner@verify-d.example", password=PASSWORD,
        first_name="Talaba", last_name="Parallel",
    )

    questions = []
    for index in range(PARALLEL):
        question = Question.objects.create(topic_id=topic.pk, text=f"V-D question {index}")
        right = Choice.objects.create(question=question, text="right", is_correct=True)
        wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
        questions.append((question, right, wrong))
    return user, topic.pk, questions


def _post(user, question_id: int, choice_id: int):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=user)
    return client.post(
        "/api/assessments/submit_answer/",
        {"question_id": question_id, "choice_id": choice_id},
        format="json",
    )


def _fire_together(user, payloads):
    """Send every payload from its own thread, released by one barrier."""
    from django.db import connection

    barrier = threading.Barrier(len(payloads))
    outcomes: list = [None] * len(payloads)

    def run(index, question_id, choice_id):
        try:
            barrier.wait(timeout=30)
            response = _post(user, question_id, choice_id)
            outcomes[index] = (response.status_code, response.json())
        except Exception as exc:  # noqa: BLE001 — the outcome is the subject
            outcomes[index] = exc
        finally:
            connection.close()

    threads = [
        threading.Thread(target=run, args=(index, question_id, choice_id))
        for index, (question_id, choice_id) in enumerate(payloads)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not any(t.is_alive() for t in threads), "a submission deadlocked"
    return outcomes


def test_v_d1_ten_parallel_answers_keep_attempt_no_unique_and_gapless(world):
    from assessments.models import AssessmentAttempt

    user, topic_id, questions = world
    payloads = [
        (question.pk, (right if index % 2 == 0 else wrong).pk)
        for index, (question, right, wrong) in enumerate(questions)
    ]

    outcomes = _fire_together(user, payloads)

    errors = [o for o in outcomes if isinstance(o, Exception)]
    assert not errors, f"a request raised instead of answering: {errors!r}"
    codes = [code for code, _ in outcomes]
    assert codes.count(200) == PARALLEL, (
        f"every answer must be accepted or refused with a reason, got {codes}"
    )

    rows = list(
        AssessmentAttempt.objects.filter(user=user, topic_id=topic_id).order_by("attempt_no")
    )
    numbers = [row.attempt_no for row in rows]
    assert len(rows) == PARALLEL, f"{len(rows)} rows for {PARALLEL} answers"
    assert numbers == list(range(1, PARALLEL + 1)), numbers
    assert len({row.question_id for row in rows}) == PARALLEL, (
        "each of the ten questions was answered exactly once"
    )
    # the response bodies agree with the ledger about how many attempts there were
    reported = sorted(body["attempt_no"] for _, body in outcomes)
    assert reported == numbers


def test_v_d1_the_final_p_l_equals_a_sequential_replay(world):
    """
    The chain must be serialised: replaying the committed rows in
    ``attempt_no`` order through the oracle has to reproduce both every stored
    ``p_before``/``p_after`` and the state row the learner now has.
    """
    from assessments.models import AssessmentAttempt, StudentTopicState

    user, topic_id, questions = world
    payloads = [
        (question.pk, (right if index % 3 else wrong).pk)
        for index, (question, right, wrong) in enumerate(questions)
    ]

    _fire_together(user, payloads)

    rows = list(
        AssessmentAttempt.objects.filter(user=user, topic_id=topic_id).order_by("attempt_no")
    )
    assert len(rows) == PARALLEL

    params = dict(
        p0=THESIS["DEFAULT_P0"], pt=THESIS["DEFAULT_PT"],
        g0=THESIS["DEFAULT_G0"], s0=THESIS["DEFAULT_S0"],
    )
    constants = dict(
        g_max=THESIS["G_MAX"], s_max=THESIS["S_MAX"], a_q=THESIS["A_Q"],
        elo_alpha=THESIS["ELO_ALPHA"], elo_beta=THESIS["ELO_BETA"],
        lam=THESIS["LAMBDA"], cap=THESIS["TAU"] - THESIS["C_OFFSET"],
        theta_clamp=THESIS["THETA_CLAMP"],
    )

    p_l = None
    for index, row in enumerate(rows):
        # θ and b are taken from the row itself: which answer saw which θ
        # depends on the order the lock granted, and that order is exactly what
        # ``attempt_no`` records. P(L), however, must come from the replay.
        expected = oracle.observe(
            **params, **constants,
            is_correct=row.is_correct, p_l=p_l,
            theta=row.theta_before, b_q=row.b_before,
            n_student=0, n_question=0, prerequisites=(),
        )
        assert row.p_before == pytest.approx(expected.p_before, abs=1e-9), index
        assert row.p_hat == pytest.approx(expected.p_hat, abs=1e-9), index
        assert row.p_after == pytest.approx(expected.p_after, abs=1e-9), index
        p_l = row.p_after

    state = StudentTopicState.objects.get(user=user, topic_id=topic_id)
    assert state.p_mastery == pytest.approx(p_l, abs=1e-9), (
        "the state row must hold the last link of the chain, not an interleaved value"
    )
    assert state.attempts == PARALLEL
    assert state.correct == sum(1 for row in rows if row.is_correct)
    # and the M flag that ended the chain is the one the two thresholds give
    flag = False
    for row in rows:
        flag = oracle.mastered_flag(
            p_mastery=row.p_after, tau=THESIS["TAU"], delta=THESIS["DELTA"], previous=flag,
        )
    assert state.mastered_flag is flag


def test_v_d1_a_parallel_repeat_of_one_question_is_recorded_once_as_an_answer(world):
    """
    Ten threads, the same question: by D25 only the first is an ``adaptive``
    answer and the rest are ``review_repeat``, which must not move P(L). The
    race must not turn that rule into two P(L) updates.
    """
    from assessments.models import AssessmentAttempt, AttemptSource, StudentTopicState

    user, topic_id, questions = world
    question, right, _ = questions[0]
    payloads = [(question.pk, right.pk)] * PARALLEL

    outcomes = _fire_together(user, payloads)
    errors = [o for o in outcomes if isinstance(o, Exception)]
    assert not errors, f"a request raised instead of answering: {errors!r}"

    rows = list(AssessmentAttempt.objects.filter(user=user, topic_id=topic_id))
    assert len(rows) == PARALLEL
    sources = [row.source for row in rows]
    assert sources.count(AttemptSource.ADAPTIVE) == 1, sources
    assert sources.count(AttemptSource.REVIEW_REPEAT) == PARALLEL - 1, sources

    moved = [row for row in rows if row.p_after is not None]
    assert len(moved) == 1, "only the first answer may carry a new P(L)"
    state = StudentTopicState.objects.get(user=user, topic_id=topic_id)
    assert state.p_mastery == pytest.approx(moved[0].p_after, abs=1e-9)

    numbers = sorted(row.attempt_no for row in rows)
    assert numbers == list(range(1, PARALLEL + 1)), numbers
