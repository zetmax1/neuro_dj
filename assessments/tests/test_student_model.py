"""
Stage 3: the student model through the Django layer (TM1–TM6, D33–D36).

The arithmetic itself is checked without a database in
``neuro_model/tests/test_student.py``. What is checked here is that the
prototype feeds the pure model the right inputs and stores the right outputs:
the section 4 values arrive in the ledger, θ is held per course, question
selection and the Elo update read the same θ, and the two commands rebuild
and calibrate from the ledger alone.
"""

from __future__ import annotations

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    ParamSource,
    Question,
    TopicModelParams,
    UserAbility,
    UserKnowledgeState,
)
from assessments.services import student_model
from assessments.services.orchestrator import process_submission
from assessments.services.question_selection import get_next_question
from curriculum.services import kb
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()
TOL = 1e-3


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def student():
    return User.objects.create_user(email="model.student@example.org", password=None)


@pytest.fixture
def course_tree():
    course = make_course("Model course", slug="model-course")
    section = make_section("Section", course, slug="model-section")
    first = make_topic("First", section, slug="model-first")
    second = make_topic("Second", section, slug="model-second")
    return course, section, first, second


def _question(topic, text: str, *, b: float = 0.0) -> tuple[Question, Choice, Choice]:
    question = Question.objects.create(topic=topic, text=text, irt_difficulty=b)
    right = Choice.objects.create(question=question, text="right", is_correct=True)
    wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
    return question, right, wrong


def _params(topic, *, p0=0.6, pt=0.1, g0=0.2, s0=0.05) -> TopicModelParams:
    return TopicModelParams.objects.create(topic=topic, p0=p0, pt=pt, g0=g0, s0=s0)


def _submit(user, question, choice, source=AttemptSource.ADAPTIVE):
    return process_submission(
        user=user, question_id=question.pk, choice_id=choice.pk, source=source,
    )


# ---------------------------------------------------------------------------
# Section 4 values, end to end through the ledger
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize(
    ("b", "correct", "expected"),
    [
        # b, is_correct, (P(G), P(S), p_hat, P(L) after)
        (1.5, True, (0.1272, 0.0731, 0.6070, 0.9246)),
        (1.5, False, (0.1272, 0.0731, 0.6070, 0.2005)),
        (-0.5, True, (0.2534, 0.0269, 0.6852, 0.8669)),
        (-0.5, False, (0.2534, 0.0269, 0.6852, 0.1461)),
    ],
)
def test_section_four_values_reach_the_ledger(student, course_tree, b, correct, expected):
    """θ=0.5, P(L)=0.6 (as P0 with no prerequisites), PT=0.1, G0=0.2, S0=0.05."""
    course, _, topic, _ = course_tree
    _params(topic)
    UserAbility.objects.create(user=student, course=course, theta=0.5, n_answers=0)
    question, right, wrong = _question(topic, "Q", b=b)

    _submit(student, question, right if correct else wrong)

    row = AssessmentAttempt.objects.get(user=student)
    guess, slip, p_hat, p_after = expected
    assert row.p_before == pytest.approx(0.6, abs=TOL)
    assert row.guess_used == pytest.approx(guess, abs=TOL)
    assert row.slip_used == pytest.approx(slip, abs=TOL)
    assert row.p_hat == pytest.approx(p_hat, abs=TOL)
    assert row.p_after == pytest.approx(p_after, abs=TOL)
    assert row.engine_version == student_model.ENGINE_VERSION


@pytest.mark.django_db
def test_the_bkt_sequence_of_four_correct_answers(student, course_tree):
    """P0=0.3, G=0.2, S=0.1, T=0.1 with a_q = 0: 0.6927 / 0.9192 / 0.9828 / 0.9965."""
    _, _, topic, _ = course_tree
    _params(topic, p0=0.3, pt=0.1, g0=0.2, s0=0.099999)

    questions = [_question(topic, f"Q{i}") for i in range(4)]
    with_classical_bkt = {"use_irt": False, "use_prereq_init": False}
    from django.test import override_settings

    with override_settings(THESIS_FLAGS=with_classical_bkt):
        # S0 must stay below S_MAX for γ; the sequence of section 4 uses
        # S = 0.1 exactly, which is the bound, so it is approached from below.
        for question, right, _ in questions:
            _submit(student, question, right)

    values = list(
        AssessmentAttempt.objects.filter(user=student)
        .order_by("attempt_no").values_list("p_after", flat=True)
    )
    assert values == pytest.approx([0.6927, 0.9192, 0.9828, 0.9965], abs=2e-3)


@pytest.mark.django_db
def test_the_prior_of_a_first_attempt_comes_from_the_prerequisites(student, course_tree):
    """P0=0.3, λ=0.5, one mastered prerequisite → the blended, capped P(L0)."""
    course, _, first, second = course_tree
    _params(first, p0=0.3)
    _params(second, p0=0.3)
    kb.add_prerequisite(prerequisite=first, topic=second)

    # Bring the prerequisite to a known P(L).
    q1, right1, _ = _question(first, "Q1")
    _submit(student, q1, right1)
    prerequisite_mastery = AssessmentAttempt.objects.get(user=student, topic=first).p_after

    q2, right2, _ = _question(second, "Q2")
    _submit(student, q2, right2)

    row = AssessmentAttempt.objects.get(user=student, topic=second)
    expected = min(0.5 * 0.3 + 0.5 * prerequisite_mastery, 0.95 - 0.05)
    assert row.p_before == pytest.approx(expected, abs=TOL)


@pytest.mark.django_db
def test_a_prerequisite_never_answered_contributes_its_own_p0(student, course_tree):
    _, _, first, second = course_tree
    _params(first, p0=0.8)
    _params(second, p0=0.3)
    kb.add_prerequisite(prerequisite=first, topic=second)

    question, right, _ = _question(second, "Q")
    _submit(student, question, right)

    row = AssessmentAttempt.objects.get(user=student)
    assert row.p_before == pytest.approx(0.5 * 0.3 + 0.5 * 0.8, abs=TOL)


@pytest.mark.django_db
def test_a_topic_without_parameters_uses_the_settings_defaults(student, course_tree, settings):
    _, _, topic, _ = course_tree
    question, right, _ = _question(topic, "Q")
    _submit(student, question, right)
    row = AssessmentAttempt.objects.get(user=student)
    assert row.p_before == pytest.approx(settings.THESIS_MODEL["DEFAULT_P0"], abs=TOL)


# ---------------------------------------------------------------------------
# Order of Algorithm 2.4
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_p_hat_is_recorded_from_the_theta_before_the_update(student, course_tree):
    course, _, topic, _ = course_tree
    _params(topic)
    UserAbility.objects.create(user=student, course=course, theta=0.5)
    question, right, _ = _question(topic, "Q", b=1.5)

    _submit(student, question, right)

    row = AssessmentAttempt.objects.get(user=student)
    assert row.theta_before == pytest.approx(0.5)
    assert row.theta_after > row.theta_before
    # p̂ reproduces from the recorded before-values, never from the after-values.
    assert row.p_hat == pytest.approx(
        row.p_before * (1 - row.slip_used) + (1 - row.p_before) * row.guess_used
    )
    assert row.guess_used == pytest.approx(
        student_model.constants().g_max
        * _sigma(_gamma(0.2, 0.30) + (row.theta_before - row.b_before))
    )


def _sigma(z: float) -> float:
    from neuro_model.irt import sigma
    return sigma(z)


def _gamma(base: float, bound: float) -> float:
    from neuro_model.irt import gamma
    return gamma(base, bound)


@pytest.mark.django_db
def test_elo_moves_the_learner_and_the_item(student, course_tree):
    course, _, topic, _ = course_tree
    question, right, _ = _question(topic, "Q", b=1.5)

    _submit(student, question, right)

    row = AssessmentAttempt.objects.get(user=student)
    ability = UserAbility.objects.get(user=student, course=course)
    item = Question.objects.get(pk=question.pk)
    assert ability.theta == pytest.approx(row.theta_after)
    assert ability.n_answers == 1
    assert item.irt_difficulty == pytest.approx(row.b_after)
    assert item.n_answers == 1
    assert row.theta_after > row.theta_before
    assert row.b_after < row.b_before


# ---------------------------------------------------------------------------
# Ablation flags (D34)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_without_irt_theta_and_b_stay_put(student, course_tree, settings):
    course, _, topic, _ = course_tree
    settings.THESIS_FLAGS = {"use_irt": False, "use_prereq_init": True}
    question, right, _ = _question(topic, "Q", b=1.5)

    _submit(student, question, right)

    row = AssessmentAttempt.objects.get(user=student)
    assert row.theta_before == row.theta_after == 0.0
    assert row.b_before == row.b_after == 1.5
    assert Question.objects.get(pk=question.pk).irt_difficulty == pytest.approx(1.5)
    # The counters still move: K(n) must shrink over the answers given.
    assert UserAbility.objects.get(user=student, course=course).n_answers == 1


@pytest.mark.django_db
def test_without_prereq_init_the_first_attempt_starts_at_p0(student, course_tree, settings):
    _, _, first, second = course_tree
    _params(first, p0=0.9)
    _params(second, p0=0.3)
    kb.add_prerequisite(prerequisite=first, topic=second)
    settings.THESIS_FLAGS = {"use_irt": True, "use_prereq_init": False}

    question, right, _ = _question(second, "Q")
    _submit(student, question, right)

    assert AssessmentAttempt.objects.get(user=student).p_before == pytest.approx(0.3, abs=TOL)


@pytest.mark.django_db
def test_the_engine_name_is_recorded_on_every_row(student, course_tree):
    _, _, topic, _ = course_tree
    question, right, _ = _question(topic, "Q")
    _submit(student, question, right)
    row = AssessmentAttempt.objects.get(user=student)
    assert row.engine_version == "thesis_hybrid/1"
    assert row.history_entry.algorithm_used == "thesis_hybrid"


# ---------------------------------------------------------------------------
# θ is one number per course (D33)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_theta_is_shared_by_every_topic_of_the_course(student, course_tree):
    course, _, first, second = course_tree
    q1, right1, _ = _question(first, "Q1")
    q2, right2, _ = _question(second, "Q2")

    _submit(student, q1, right1)
    _submit(student, q2, right2)

    assert UserAbility.objects.filter(user=student).count() == 1
    ability = UserAbility.objects.get(user=student, course=course)
    assert ability.n_answers == 2
    rows = list(AssessmentAttempt.objects.filter(user=student).order_by("answered_at", "id"))
    assert rows[1].theta_before == pytest.approx(rows[0].theta_after)


@pytest.mark.django_db
def test_two_courses_hold_two_abilities(student, course_tree):
    _, _, first, _ = course_tree
    other_course = make_course("Other", slug="other-course")
    other_topic = make_topic("Other topic", other_course, slug="other-topic")

    q1, right1, _ = _question(first, "Q1")
    q2, right2, _ = _question(other_topic, "Q2")
    _submit(student, q1, right1)
    _submit(student, q2, right2)

    assert UserAbility.objects.filter(user=student).count() == 2


# ---------------------------------------------------------------------------
# Question selection reads the same θ the update writes
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_selection_picks_the_question_closest_to_theta(student, course_tree):
    course, _, topic, _ = course_tree
    UserAbility.objects.create(user=student, course=course, theta=1.0)
    _question(topic, "far low", b=-2.0)
    closest, _, _ = _question(topic, "closest", b=1.2)
    _question(topic, "far high", b=3.0)

    assert get_next_question(user=student, topic_id=topic.pk).pk == closest.pk


@pytest.mark.django_db
def test_selection_breaks_ties_by_id(student, course_tree):
    course, _, topic, _ = course_tree
    UserAbility.objects.create(user=student, course=course, theta=0.0)
    first, _, _ = _question(topic, "A", b=0.5)
    _question(topic, "B", b=-0.5)

    assert get_next_question(user=student, topic_id=topic.pk).pk == first.pk


@pytest.mark.django_db
def test_selection_uses_the_course_theta_not_zero(student, course_tree):
    """The removed per-topic lookup returned 0 here and chose the wrong item."""
    course, _, topic, _ = course_tree
    UserAbility.objects.create(user=student, course=course, theta=2.5)
    _question(topic, "easy", b=0.0)
    hard, _, _ = _question(topic, "hard", b=2.4)

    assert get_next_question(user=student, topic_id=topic.pk).pk == hard.pk


# ---------------------------------------------------------------------------
# rebuild_student_states (D35)
# ---------------------------------------------------------------------------

def _answer_a_few(student, topic, *, count: int = 4) -> None:
    for index in range(count):
        question, right, wrong = _question(topic, f"Q{index}", b=0.2 * index)
        _submit(student, question, right if index % 2 == 0 else wrong)


def _state_fingerprint(student) -> tuple:
    return (
        tuple(
            UserKnowledgeState.objects.filter(user=student)
            .order_by("topic_id")
            .values_list("topic_id", "mastery_percentage", "total_attempts", "correct_attempts")
        ),
        tuple(
            UserAbility.objects.filter(user=student)
            .order_by("course_id").values_list("course_id", "theta", "n_answers")
        ),
        tuple(Question.objects.order_by("id").values_list("id", "irt_difficulty", "n_answers")),
    )


@pytest.mark.django_db
def test_rebuild_reproduces_the_live_state(student, course_tree):
    _, _, topic, _ = course_tree
    _params(topic)
    _answer_a_few(student, topic)
    live = _state_fingerprint(student)

    call_command("rebuild_student_states", stdout=StringIO())

    assert _state_fingerprint(student) == live


@pytest.mark.django_db
def test_rebuild_is_deterministic(student, course_tree):
    _, _, topic, _ = course_tree
    _answer_a_few(student, topic)

    call_command("rebuild_student_states", stdout=StringIO())
    once = _state_fingerprint(student)
    call_command("rebuild_student_states", stdout=StringIO())

    assert _state_fingerprint(student) == once


@pytest.mark.django_db
def test_rebuild_restores_state_that_was_tampered_with(student, course_tree):
    course, _, topic, _ = course_tree
    _answer_a_few(student, topic)
    expected = _state_fingerprint(student)

    UserKnowledgeState.objects.filter(user=student).update(mastery_percentage=0.01)
    UserAbility.objects.filter(user=student, course=course).update(theta=-3.0, n_answers=99)

    call_command("rebuild_student_states", stdout=StringIO())

    assert _state_fingerprint(student) == expected


@pytest.mark.django_db
def test_rebuild_dry_run_writes_nothing(student, course_tree):
    _, _, topic, _ = course_tree
    _answer_a_few(student, topic)
    UserKnowledgeState.objects.filter(user=student).update(mastery_percentage=0.01)
    tampered = _state_fingerprint(student)

    out = StringIO()
    call_command("rebuild_student_states", "--dry-run", stdout=out)

    assert "nothing was written" in out.getvalue()
    assert _state_fingerprint(student) == tampered


@pytest.mark.django_db
def test_rebuild_ignores_generated_answers_by_default(student, course_tree):
    """
    A seeded answer is a model observation when it is given, so the live path
    writes state for it; the rebuild simply does not replay it. It rebuilds
    what is in scope and leaves everything else as it stands.
    """
    course, _, topic, _ = course_tree
    question, right, _ = _question(topic, "Seeded")
    _submit(student, question, right, source=AttemptSource.SEED)
    live = UserAbility.objects.get(user=student, course=course)

    out = StringIO()
    call_command("rebuild_student_states", stdout=out)

    assert "Replaying 0 row(s)" in out.getvalue()
    untouched = UserAbility.objects.get(user=student, course=course)
    assert (untouched.theta, untouched.n_answers) == (live.theta, live.n_answers)

    out = StringIO()
    call_command("rebuild_student_states", "--include-legacy", stdout=out)
    assert "Replaying 1 row(s)" in out.getvalue()
    replayed = UserAbility.objects.get(user=student, course=course)
    assert (replayed.theta, replayed.n_answers) == (live.theta, live.n_answers)


@pytest.mark.django_db
def test_rebuild_skips_review_repeats(student, course_tree):
    _, _, topic, _ = course_tree
    question, right, wrong = _question(topic, "Q")
    _submit(student, question, wrong)
    _submit(student, question, right)  # inside the review window → review_repeat

    out = StringIO()
    call_command("rebuild_student_states", stdout=out)

    assert "Replaying 1 row(s)" in out.getvalue()
    assert UserAbility.objects.get(user=student).n_answers == 1


# ---------------------------------------------------------------------------
# calibrate_bkt (D36)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_calibrate_leaves_thin_topics_at_the_defaults(student, course_tree):
    _, _, topic, _ = course_tree
    _answer_a_few(student, topic, count=3)

    out = StringIO()
    call_command("calibrate_bkt", stdout=out)

    assert "below --min-answers" in out.getvalue()
    assert not TopicModelParams.objects.exists()


@pytest.mark.django_db
def test_calibrate_writes_fitted_parameters(student, course_tree, settings):
    _, _, topic, _ = course_tree
    _answer_a_few(student, topic, count=6)

    out = StringIO()
    call_command("calibrate_bkt", "--min-answers", "4", stdout=out)

    row = TopicModelParams.objects.get(topic=topic)
    assert row.source == ParamSource.FITTED
    assert row.fitted_at is not None
    # The bounds γ needs are respected by the search.
    assert 0.0 < row.g0 < settings.THESIS_MODEL["G_MAX"]
    assert 0.0 < row.s0 < settings.THESIS_MODEL["S_MAX"]
    assert "Wrote 1 fitted parameter set" in out.getvalue()


@pytest.mark.django_db
def test_calibrate_dry_run_writes_nothing(student, course_tree):
    _, _, topic, _ = course_tree
    _answer_a_few(student, topic, count=6)

    out = StringIO()
    call_command("calibrate_bkt", "--min-answers", "4", "--dry-run", stdout=out)

    assert "nothing was written" in out.getvalue()
    assert not TopicModelParams.objects.exists()


@pytest.mark.django_db
def test_calibrate_is_deterministic(student, course_tree):
    _, _, topic, _ = course_tree
    _answer_a_few(student, topic, count=6)

    call_command("calibrate_bkt", "--min-answers", "4", stdout=StringIO())
    first = TopicModelParams.objects.values_list("p0", "pt", "g0", "s0").get(topic=topic)
    call_command("calibrate_bkt", "--min-answers", "4", stdout=StringIO())
    second = TopicModelParams.objects.values_list("p0", "pt", "g0", "s0").get(topic=topic)

    assert first == second


@pytest.mark.django_db
def test_calibrate_ignores_generated_answers_by_default(student, course_tree):
    _, _, topic, _ = course_tree
    for index in range(6):
        question, right, _ = _question(topic, f"S{index}")
        _submit(student, question, right, source=AttemptSource.SEED)

    out = StringIO()
    call_command("calibrate_bkt", "--min-answers", "4", stdout=out)

    assert "nothing to calibrate" in out.getvalue()
    assert not TopicModelParams.objects.exists()


@pytest.mark.django_db
def test_fitted_parameters_are_used_by_the_next_answer(student, course_tree):
    _, _, topic, _ = course_tree
    TopicModelParams.objects.create(topic=topic, p0=0.42, pt=0.1, g0=0.2, s0=0.05)

    question, right, _ = _question(topic, "Q")
    _submit(student, question, right)

    assert AssessmentAttempt.objects.get(user=student).p_before == pytest.approx(0.42, abs=TOL)
