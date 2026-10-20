"""
Reference values of NEUROLEARN_REMEDIATION.md, section 4 (student-model part),
checked on the pure functions without a database.

Covered: the BKT sequence, the guess/slip adaptation table (hard item, easy
item, a=0), the Elo step, P(L0) from prerequisites, the 2.5 assertion, the
ablation flags and the order of Algorithm 2.4.
"""

from __future__ import annotations

import math

import pytest

from neuro_model import bkt, elo, irt
from neuro_model import student as s
from neuro_model.init import Prerequisite, initial_mastery

TOL = 1e-3

# The constants of section 4 / config.settings.THESIS_MODEL.
CONSTANTS = s.Constants(
    g_max=0.30, s_max=0.10, a_q=1.0,
    elo_alpha=0.8, elo_beta=0.05,
    lam=0.5, tau=0.95, c_offset=0.05, theta_clamp=4.0,
)


# ---------------------------------------------------------------------------
# BKT sequence: P0=0.3, G=0.2, S=0.1, T=0.1, four correct answers
# ---------------------------------------------------------------------------

def test_bkt_sequence_of_four_correct_answers():
    p_l = 0.3
    seen = []
    for _ in range(4):
        p_l = bkt.step(p_l=p_l, guess=0.2, slip=0.1, pt=0.1, is_correct=True).p_after
        seen.append(p_l)
    assert seen == pytest.approx([0.6927, 0.9192, 0.9828, 0.9965], abs=TOL)


def test_p_hat_of_the_first_observation():
    """p̂ = 0.3·0.9 + 0.7·0.2 = 0.41, kept as predicted."""
    assert bkt.predict(p_l=0.3, guess=0.2, slip=0.1) == pytest.approx(0.41, abs=TOL)


# ---------------------------------------------------------------------------
# Guess and slip adaptation: θ=0.5, P(L)=0.6, PT=0.1, G0=0.2, S0=0.05
# ---------------------------------------------------------------------------

PARAMS = s.TopicParams(p0=0.3, pt=0.1, g0=0.2, s0=0.05)


def observe_at(b_q: float, *, is_correct: bool, use_irt: bool = True) -> s.StepResult:
    return s.observe(
        params=PARAMS,
        constants=CONSTANTS,
        flags=s.Flags(use_irt=use_irt, use_prereq_init=False),
        observation=s.Observation(
            is_correct=is_correct, p_l=0.6, theta=0.5, b_q=b_q,
        ),
    )


@pytest.mark.parametrize(
    ("label", "b_q", "use_irt", "expected"),
    [
        # label, b, use_irt, (P(G), P(S), p_hat, P(L) correct, P(L) wrong)
        ("hard item b=1.5", 1.5, True, (0.1272, 0.0731, 0.6070, 0.9246, 0.2005)),
        ("easy item b=-0.5", -0.5, True, (0.2534, 0.0269, 0.6852, 0.8669, 0.1461)),
        ("a=0, classical BKT", 1.5, False, (0.20, 0.05, 0.65, 0.8892, 0.1771)),
    ],
)
def test_guess_slip_table(label, b_q, use_irt, expected):
    guess, slip, p_hat, after_correct, after_wrong = expected
    right = observe_at(b_q, is_correct=True, use_irt=use_irt)
    wrong = observe_at(b_q, is_correct=False, use_irt=use_irt)

    assert right.guess == pytest.approx(guess, abs=TOL)
    assert right.slip == pytest.approx(slip, abs=TOL)
    assert right.p_hat == pytest.approx(p_hat, abs=TOL)
    assert right.p_after == pytest.approx(after_correct, abs=TOL)
    assert wrong.p_after == pytest.approx(after_wrong, abs=TOL)
    # The prediction does not depend on the answer.
    assert wrong.p_hat == pytest.approx(right.p_hat, abs=1e-12)


def test_a_zero_reproduces_the_base_values_exactly():
    """With a_q = 0 the logistic terms collapse: P(G) = G0 and P(S) = S0."""
    for b_q in (-3.0, 0.0, 1.5, 7.0):
        assert irt.guess(g0=0.2, g_max=0.3, a_q=0.0, theta=0.5, b_q=b_q) == pytest.approx(0.2)
        assert irt.slip(s0=0.05, s_max=0.1, a_q=0.0, theta=0.5, b_q=b_q) == pytest.approx(0.05)


def test_guess_and_slip_stay_inside_their_bounds():
    """Strictly inside over the working range of θ (clamped to ±4) and b."""
    for theta in (-4.0, -1.0, 0.0, 1.0, 4.0):
        for b_q in (-4.0, 0.0, 4.0):
            guess = irt.guess(g0=0.2, g_max=0.3, a_q=1.0, theta=theta, b_q=b_q)
            slip = irt.slip(s0=0.05, s_max=0.1, a_q=1.0, theta=theta, b_q=b_q)
            assert 0.0 < guess < 0.30
            assert 0.0 < slip < 0.10


def test_guess_and_slip_never_exceed_their_bounds():
    """
    Far outside the working range the logistic saturates in floating point and
    the value reaches the bound exactly; it never passes it, which is what
    assertion 2.5 needs (G_MAX + S_MAX < 1).
    """
    for theta, b_q in ((-500.0, 500.0), (500.0, -500.0)):
        guess = irt.guess(g0=0.2, g_max=0.3, a_q=1.0, theta=theta, b_q=b_q)
        slip = irt.slip(s0=0.05, s_max=0.1, a_q=1.0, theta=theta, b_q=b_q)
        assert 0.0 <= guess <= 0.30
        assert 0.0 <= slip <= 0.10
        assert guess + slip < 1.0


def test_gamma_is_undefined_at_the_bounds():
    for base in (0.0, 0.3, 0.5):
        with pytest.raises(ValueError):
            irt.gamma(base, 0.3)


# ---------------------------------------------------------------------------
# Elo: θ=0.5, b=1.5, K=0.4, correct answer
# ---------------------------------------------------------------------------

def test_elo_step():
    step = elo.update(
        theta=0.5, b=1.5, is_correct=True,
        k_student=0.4, k_question=0.4, theta_clamp=4.0,
    )
    assert step.p == pytest.approx(0.2689, abs=TOL)
    assert step.theta == pytest.approx(0.7924, abs=TOL)
    assert step.b == pytest.approx(1.2076, abs=TOL)


def test_k_factor_shrinks_with_evidence():
    first = elo.k_factor(0, alpha=0.8, beta=0.05)
    assert first == pytest.approx(0.8)
    assert elo.k_factor(20, alpha=0.8, beta=0.05) == pytest.approx(0.4)
    assert elo.k_factor(100, alpha=0.8, beta=0.05) < first


def test_theta_is_clamped():
    """θ=3.9 on a hard item (b=5) would reach 4.5; the clamp holds it at 4.0."""
    step = elo.update(
        theta=3.9, b=5.0, is_correct=True,
        k_student=0.8, k_question=0.8, theta_clamp=4.0,
    )
    assert step.theta == pytest.approx(4.0)

    low = elo.update(
        theta=-3.9, b=-5.0, is_correct=False,
        k_student=0.8, k_question=0.8, theta_clamp=4.0,
    )
    assert low.theta == pytest.approx(-4.0)


def test_elo_moves_the_learner_and_the_item_in_opposite_directions():
    right = elo.update(theta=0.0, b=0.0, is_correct=True, k_student=0.8, k_question=0.8, theta_clamp=4.0)
    wrong = elo.update(theta=0.0, b=0.0, is_correct=False, k_student=0.8, k_question=0.8, theta_clamp=4.0)
    assert right.theta > 0.0 > right.b
    assert wrong.theta < 0.0 < wrong.b


# ---------------------------------------------------------------------------
# P(L0) from prerequisites: P0=0.3, λ=0.5, equal weights
# ---------------------------------------------------------------------------

def prereqs(values, *, weight: float = 1.0, p0: float = 0.3):
    return tuple(Prerequisite(weight=weight, p_l=v, p0=p0) for v in values)


@pytest.mark.parametrize(
    ("values", "expected"),
    [((0.98, 0.96, 0.976), 0.636), ((0.4, 0.5, 0.3), 0.35)],
)
def test_initial_mastery_reference_values(values, expected):
    assert initial_mastery(
        p0=0.3, prerequisites=prereqs(values), lam=0.5, cap=0.90,
    ) == pytest.approx(expected, abs=TOL)


def test_no_prerequisites_keeps_the_base_value():
    assert initial_mastery(p0=0.3, prerequisites=(), lam=0.5, cap=0.90) == pytest.approx(0.3)


def test_lambda_zero_reduces_to_the_base_value():
    assert initial_mastery(
        p0=0.3, prerequisites=prereqs((0.99, 0.99)), lam=0.0, cap=0.90,
    ) == pytest.approx(0.3)


def test_the_prior_is_capped_below_tau():
    """Even fully mastered prerequisites cannot put a fresh topic at τ."""
    value = initial_mastery(
        p0=0.9, prerequisites=prereqs((1.0, 1.0, 1.0)), lam=1.0, cap=0.90,
    )
    assert value == pytest.approx(0.90)
    assert value < CONSTANTS.tau


def test_a_prerequisite_the_learner_never_answered_uses_its_own_p0():
    mixed = (
        Prerequisite(weight=1.0, p_l=None, p0=0.2),
        Prerequisite(weight=1.0, p_l=0.8, p0=0.2),
    )
    assert initial_mastery(p0=0.3, prerequisites=mixed, lam=1.0, cap=0.90) == pytest.approx(0.5)


def test_weights_are_respected():
    weighted = (
        Prerequisite(weight=1.0, p_l=1.0, p0=0.3),
        Prerequisite(weight=0.25, p_l=0.0, p0=0.3),
    )
    assert initial_mastery(
        p0=0.0, prerequisites=weighted, lam=1.0, cap=0.90,
    ) == pytest.approx(0.8, abs=TOL)


# ---------------------------------------------------------------------------
# Assertion 2.5 (property): P(G) + P(S) < 1 => P(L|1) > P(L) > P(L|0)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("p_l", [0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99])
@pytest.mark.parametrize(("guess", "slip"), [(0.2, 0.05), (0.3, 0.1), (0.01, 0.01), (0.49, 0.5)])
def test_assertion_2_5_on_the_posterior(p_l, guess, slip):
    assert guess + slip < 1.0
    right = bkt.posterior(p_l=p_l, guess=guess, slip=slip, is_correct=True)
    wrong = bkt.posterior(p_l=p_l, guess=guess, slip=slip, is_correct=False)
    assert right > p_l, "a correct answer must raise the posterior"
    assert wrong < p_l, "a wrong answer must lower the posterior"


def test_assertion_2_5_holds_for_every_bounded_item():
    """G_MAX + S_MAX = 0.4 < 1, so the bounded parameters always satisfy 2.5."""
    for b_q in (-4.0, -1.0, 0.0, 1.0, 4.0):
        for theta in (-4.0, 0.0, 4.0):
            guess = irt.guess(g0=0.2, g_max=0.3, a_q=1.0, theta=theta, b_q=b_q)
            slip = irt.slip(s0=0.05, s_max=0.1, a_q=1.0, theta=theta, b_q=b_q)
            assert guess + slip < 1.0
            assert bkt.posterior(p_l=0.6, guess=guess, slip=slip, is_correct=True) > 0.6
            assert bkt.posterior(p_l=0.6, guess=guess, slip=slip, is_correct=False) < 0.6


def test_the_posterior_is_clamped_once_p_l_has_rounded_to_one():
    """
    D65a: the case Hypothesis found. With P(L) = 1.0 exactly, a wrong answer's
    posterior P·S / (1 − fl(1 − S)) overshoots 1 (here by one ulp).
    """
    raw = 1.0 * 0.1 / (1.0 - bkt.predict(p_l=1.0, guess=0.2, slip=0.1))
    assert raw > 1.0, "the unclamped formula overshoots for this slip"
    assert bkt.posterior(p_l=1.0, guess=0.2, slip=0.1, is_correct=False) == 1.0
    assert bkt.step(p_l=1.0, guess=0.2, slip=0.1, pt=0.5, is_correct=False).p_after == 1.0


def test_pt_can_raise_p_l_after_a_wrong_answer():
    """
    Documented classical-BKT behaviour, not a defect: the transition applies
    after the Bayes step, so a near-zero posterior still gains PT.
    """
    step = bkt.step(p_l=0.02, guess=0.2, slip=0.05, pt=0.5, is_correct=False)
    assert step.posterior < 0.02
    assert step.p_after > 0.02


# ---------------------------------------------------------------------------
# Order of Algorithm 2.4 and the ablation flags
# ---------------------------------------------------------------------------

def test_p_hat_uses_theta_before_not_theta_after():
    """
    TM6 step 3: the prediction is computed from the θ and b that were in force
    when the question was asked, so recomputing it with theta_after must differ.
    """
    result = s.observe(
        params=PARAMS, constants=CONSTANTS, flags=s.Flags(use_prereq_init=False),
        observation=s.Observation(is_correct=True, p_l=0.6, theta=0.5, b_q=1.5),
    )
    assert result.theta_before == 0.5
    assert result.theta_after > result.theta_before

    with_before = bkt.predict(
        p_l=0.6,
        guess=irt.guess(g0=0.2, g_max=0.3, a_q=1.0, theta=result.theta_before, b_q=result.b_before),
        slip=irt.slip(s0=0.05, s_max=0.1, a_q=1.0, theta=result.theta_before, b_q=result.b_before),
    )
    with_after = bkt.predict(
        p_l=0.6,
        guess=irt.guess(g0=0.2, g_max=0.3, a_q=1.0, theta=result.theta_after, b_q=result.b_after),
        slip=irt.slip(s0=0.05, s_max=0.1, a_q=1.0, theta=result.theta_after, b_q=result.b_after),
    )
    assert result.p_hat == pytest.approx(with_before, abs=1e-12)
    assert result.p_hat != pytest.approx(with_after, abs=1e-6)


def test_the_first_attempt_uses_the_prior_from_prerequisites():
    result = s.observe(
        params=PARAMS, constants=CONSTANTS, flags=s.Flags(),
        observation=s.Observation(
            is_correct=True, p_l=None, theta=0.0, b_q=0.0,
            prerequisites=prereqs((0.98, 0.96, 0.976)),
        ),
    )
    assert result.p_before == pytest.approx(0.636, abs=TOL)


def test_without_prereq_init_the_first_attempt_starts_at_p0():
    result = s.observe(
        params=PARAMS, constants=CONSTANTS, flags=s.Flags(use_prereq_init=False),
        observation=s.Observation(
            is_correct=True, p_l=None, theta=0.0, b_q=0.0,
            prerequisites=prereqs((0.98, 0.96, 0.976)),
        ),
    )
    assert result.p_before == pytest.approx(PARAMS.p0, abs=TOL)


def test_without_irt_theta_and_b_do_not_move():
    result = s.observe(
        params=PARAMS, constants=CONSTANTS, flags=s.Flags(use_irt=False, use_prereq_init=False),
        observation=s.Observation(is_correct=True, p_l=0.6, theta=0.5, b_q=1.5, n_student=3),
    )
    assert (result.theta_after, result.b_after) == (0.5, 1.5)


def test_the_classical_variant_equals_a_plain_bkt_step():
    """Both flags off must be classical BKT, not an approximation of it."""
    flags = s.Flags(use_irt=False, use_prereq_init=False)
    p_l = PARAMS.p0
    for is_correct in (True, False, True, True):
        result = s.observe(
            params=PARAMS, constants=CONSTANTS, flags=flags,
            observation=s.Observation(is_correct=is_correct, p_l=p_l, theta=0.0, b_q=0.0),
        )
        plain = bkt.step(
            p_l=p_l, guess=PARAMS.g0, slip=PARAMS.s0,
            pt=PARAMS.pt, is_correct=is_correct,
        )
        assert result.p_after == pytest.approx(plain.p_after, abs=1e-12)
        p_l = result.p_after


def test_with_irt_the_estimate_differs_from_classical_bkt():
    common = dict(params=PARAMS, constants=CONSTANTS)
    observation = s.Observation(is_correct=True, p_l=0.6, theta=0.5, b_q=1.5)
    hybrid = s.observe(**common, flags=s.Flags(use_prereq_init=False), observation=observation)
    classical = s.observe(
        **common, flags=s.Flags(use_irt=False, use_prereq_init=False), observation=observation,
    )
    assert hybrid.p_after != pytest.approx(classical.p_after, abs=1e-6)


def test_sigma_does_not_overflow():
    assert irt.sigma(-1000.0) == pytest.approx(0.0)
    assert irt.sigma(1000.0) == pytest.approx(1.0)
    assert irt.sigma(0.0) == pytest.approx(0.5)
    assert math.isfinite(irt.sigma(-745.0))
