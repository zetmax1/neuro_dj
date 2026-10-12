"""
Group A — the pure student model (``neuro_model``), stage 3.

V-A1  every number of section 4 comes out to 1e-3;
V-A2  differential test: 10 000 random inputs agree with the oracle to 1e-9;
V-A3  properties: the bounds, assertion 2.5, [0, 1], the θ clamp, and
      a_q = 0 with λ = 0 reproducing classical BKT.

The expected values are quoted from NEUROLEARN_REMEDIATION.md section 4 and
§3.3-3.4; the comparison values come from ``verification.oracle.model``, an
independent transcription of the same formulas. This module never imports a
test helper of the prototype.
"""

from __future__ import annotations

import math
from random import Random

import pytest
from django.conf import settings

from neuro_model import bkt, elo, init, irt, readiness, student
from verification.oracle import model as oracle

SEED: int = settings.VERIFICATION_SEED
THESIS = settings.THESIS_MODEL

# Section 4 fixes these; the constants live in settings and are checked in V-A3.
G_MAX = 0.30
S_MAX = 0.10


def _constants(**overrides) -> student.Constants:
    """Chapter II's constants, as the prototype assembles them from settings."""
    values = dict(
        g_max=THESIS["G_MAX"],
        s_max=THESIS["S_MAX"],
        a_q=THESIS["A_Q"],
        elo_alpha=THESIS["ELO_ALPHA"],
        elo_beta=THESIS["ELO_BETA"],
        lam=THESIS["LAMBDA"],
        tau=THESIS["TAU"],
        c_offset=THESIS["C_OFFSET"],
        theta_clamp=THESIS["THETA_CLAMP"],
    )
    values.update(overrides)
    return student.Constants(**values)


# ---------------------------------------------------------------------------
# V-A1 — section 4, to 1e-3
# ---------------------------------------------------------------------------


def test_v_a1_the_bkt_sequence_of_section_four():
    """P0=0.3, G=0.2, S=0.1, T=0.1, four correct answers: 0.6927 … 0.9965."""
    expected = [0.6927, 0.9192, 0.9828, 0.9965]

    p_l = 0.3
    produced = []
    for _ in range(4):
        step = bkt.step(p_l=p_l, guess=0.2, slip=0.1, pt=0.1, is_correct=True)
        p_l = step.p_after
        produced.append(p_l)

    assert produced == pytest.approx(expected, abs=1e-3)
    # the same sequence from the oracle, so the table is checked twice
    p_l = 0.3
    for want in expected:
        post = oracle.posterior(p_l=p_l, guess=0.2, slip=0.1, is_correct=True)
        p_l = oracle.transition(post=post, pt=0.1)
        assert p_l == pytest.approx(want, abs=1e-3)


@pytest.mark.parametrize(
    "case, b_q, a_q, want_guess, want_slip, want_p_hat, want_correct, want_wrong",
    [
        ("hard", 1.5, 1.0, 0.1272, 0.0731, 0.6070, 0.9246, 0.2005),
        ("easy", -0.5, 1.0, 0.2534, 0.0269, 0.6852, 0.8669, 0.1461),
        ("a=0", 1.5, 0.0, 0.20, 0.05, 0.65, 0.8892, 0.1771),
    ],
)
def test_v_a1_guess_and_slip_adapt_as_section_four_says(
    case, b_q, a_q, want_guess, want_slip, want_p_hat, want_correct, want_wrong
):
    """θ=0.5, P(L)=0.6, PT=0.1, G0=0.2, S0=0.05, G_MAX=0.3, S_MAX=0.1."""
    theta, p_l, pt = 0.5, 0.6, 0.1
    g = irt.guess(g0=0.2, g_max=G_MAX, a_q=a_q, theta=theta, b_q=b_q)
    s = irt.slip(s0=0.05, s_max=S_MAX, a_q=a_q, theta=theta, b_q=b_q)

    assert g == pytest.approx(want_guess, abs=1e-3), case
    assert s == pytest.approx(want_slip, abs=1e-3), case
    assert bkt.predict(p_l=p_l, guess=g, slip=s) == pytest.approx(want_p_hat, abs=1e-3)
    after_correct = bkt.step(p_l=p_l, guess=g, slip=s, pt=pt, is_correct=True)
    after_wrong = bkt.step(p_l=p_l, guess=g, slip=s, pt=pt, is_correct=False)
    assert after_correct.p_after == pytest.approx(want_correct, abs=1e-3)
    assert after_wrong.p_after == pytest.approx(want_wrong, abs=1e-3)


def test_v_a1_elo_of_section_four():
    """θ=0.5, b=1.5, K=0.4, correct answer: p=0.2689, θ=0.7924, b=1.2076."""
    assert elo.expected(theta=0.5, b=1.5) == pytest.approx(0.2689, abs=1e-3)
    moved = elo.update(
        theta=0.5, b=1.5, is_correct=True, k_student=0.4, k_question=0.4,
        theta_clamp=THESIS["THETA_CLAMP"],
    )
    assert moved.theta == pytest.approx(0.7924, abs=1e-3)
    assert moved.b == pytest.approx(1.2076, abs=1e-3)


@pytest.mark.parametrize(
    "values, want_mean, want_p_l0",
    [((0.98, 0.96, 0.976), 0.972, 0.636), ((0.4, 0.5, 0.3), 0.4, 0.35)],
)
def test_v_a1_initial_mastery_from_the_prerequisites(values, want_mean, want_p_l0):
    """P0=0.3, λ=0.5, equal weights; the cap τ − C_OFFSET does not bind here."""
    prerequisites = [init.Prerequisite(weight=1.0, p_l=v, p0=0.3) for v in values]
    mean = init.mean_prerequisite_mastery(prerequisites)
    assert mean == pytest.approx(want_mean, abs=1e-3)
    produced = init.initial_mastery(
        p0=0.3, prerequisites=prerequisites, lam=0.5,
        cap=THESIS["TAU"] - THESIS["C_OFFSET"],
    )
    assert produced == pytest.approx(want_p_l0, abs=1e-3)


def test_v_a1_the_readiness_example_reaches_0_8921_then_0_9764():
    """
    t4 with G=0.2, S=0.1, T=0.1 and two correct answers from P(L)=0.62.

    Section 4 gives 0.8921 and then 0.9764, and τ=0.95, δ=0.10, so M flips to 1
    only on the second answer — which is what opens t6 in V-C.
    """
    p_l = 0.62
    produced = []
    for _ in range(2):
        p_l = bkt.step(p_l=p_l, guess=0.2, slip=0.1, pt=0.1, is_correct=True).p_after
        produced.append(p_l)

    assert produced == pytest.approx([0.8921, 0.9764], abs=1e-3)
    tau, delta = THESIS["TAU"], THESIS["DELTA"]
    assert readiness.mastered_flag(
        p_mastery=produced[0], tau=tau, delta=delta, previous=False
    ) is False
    assert readiness.mastered_flag(
        p_mastery=produced[1], tau=tau, delta=delta, previous=False
    ) is True


# ---------------------------------------------------------------------------
# V-A2 — differential test against the oracle
# ---------------------------------------------------------------------------


def _random_case(rng: Random) -> dict:
    """One admissible input of algorithm 2.4 (G0 < G_MAX, S0 < S_MAX, ω > 0)."""
    g_max, s_max = THESIS["G_MAX"], THESIS["S_MAX"]
    prerequisites = [
        (round(rng.uniform(0.05, 1.0), 6), rng.choice([None, rng.random()]), rng.random())
        for _ in range(rng.randint(0, 4))
    ]
    return dict(
        p0=rng.uniform(0.01, 0.99),
        pt=rng.uniform(0.0, 0.5),
        g0=rng.uniform(0.01, g_max - 0.01),
        s0=rng.uniform(0.005, s_max - 0.005),
        is_correct=rng.random() < 0.5,
        p_l=None if rng.random() < 0.25 else rng.uniform(0.001, 0.999),
        theta=rng.uniform(-5.0, 5.0),
        b_q=rng.uniform(-5.0, 5.0),
        n_student=rng.randint(0, 200),
        n_question=rng.randint(0, 200),
        prerequisites=prerequisites,
        use_irt=rng.random() < 0.8,
        use_prereq_init=rng.random() < 0.8,
    )


def test_v_a2_ten_thousand_random_answers_agree_with_the_oracle_to_1e_9():
    """
    The whole of algorithm 2.4, not only the leaf formulas: p̂, the posterior,
    P(L)′, P(G), P(S), θ and b after the Elo move, for both ablation flags.
    """
    constants = _constants()
    rng = Random(SEED + 1)
    worst = 0.0

    for index in range(10_000):
        case = _random_case(rng)
        params = student.TopicParams(
            p0=case["p0"], pt=case["pt"], g0=case["g0"], s0=case["s0"],
        )
        observation = student.Observation(
            is_correct=case["is_correct"],
            p_l=case["p_l"],
            theta=case["theta"],
            b_q=case["b_q"],
            n_student=case["n_student"],
            n_question=case["n_question"],
            prerequisites=tuple(
                init.Prerequisite(weight=w, p_l=p, p0=p0)
                for w, p, p0 in case["prerequisites"]
            ),
        )
        produced = student.observe(
            params=params,
            constants=constants,
            observation=observation,
            flags=student.Flags(
                use_irt=case["use_irt"], use_prereq_init=case["use_prereq_init"],
            ),
        )
        expected = oracle.observe(
            p0=case["p0"], pt=case["pt"], g0=case["g0"], s0=case["s0"],
            g_max=constants.g_max, s_max=constants.s_max, a_q=constants.a_q,
            elo_alpha=constants.elo_alpha, elo_beta=constants.elo_beta,
            lam=constants.lam, cap=constants.prior_cap,
            theta_clamp=constants.theta_clamp,
            is_correct=case["is_correct"], p_l=case["p_l"],
            theta=case["theta"], b_q=case["b_q"],
            n_student=case["n_student"], n_question=case["n_question"],
            prerequisites=tuple(
                oracle.Pre(weight=w, p_l=p, p0=p0) for w, p, p0 in case["prerequisites"]
            ),
            use_irt=case["use_irt"], use_prereq_init=case["use_prereq_init"],
        )
        for field in (
            "p_before", "p_hat", "posterior", "p_after", "guess", "slip",
            "theta_after", "b_after",
        ):
            mine = getattr(produced, field)
            theirs = getattr(expected, field)
            worst = max(worst, abs(mine - theirs))
            assert mine == pytest.approx(theirs, abs=1e-9, rel=0.0), (
                f"case {index}, {field}: {mine} vs oracle {theirs} ({case})"
            )

    assert worst < 1e-9


def test_v_a2_the_leaf_formulas_agree_on_their_own_grids():
    """
    γ, K(n), the Elo expectation and the two-threshold M, swept separately so
    that a disagreement points at one formula rather than at the whole step.
    """
    rng = Random(SEED + 2)
    for _ in range(2_000):
        base, bound = rng.uniform(0.01, 0.29), rng.choice([0.3, 0.1, 0.5])
        if base >= bound:
            continue
        assert irt.gamma(base, bound) == pytest.approx(
            oracle.gamma(base, bound), abs=1e-12
        )
    for n in range(0, 500):
        assert elo.k_factor(
            n, alpha=THESIS["ELO_ALPHA"], beta=THESIS["ELO_BETA"]
        ) == pytest.approx(
            oracle.k_factor(n, alpha=THESIS["ELO_ALPHA"], beta=THESIS["ELO_BETA"]),
            abs=1e-12,
        )
    for _ in range(2_000):
        theta, b = rng.uniform(-8.0, 8.0), rng.uniform(-8.0, 8.0)
        assert elo.expected(theta=theta, b=b) == pytest.approx(
            oracle.elo_expected(theta=theta, b=b), abs=1e-12
        )
        p = rng.random()
        previous = rng.random() < 0.5
        assert readiness.mastered_flag(
            p_mastery=p, tau=THESIS["TAU"], delta=THESIS["DELTA"], previous=previous
        ) == oracle.mastered_flag(
            p_mastery=p, tau=THESIS["TAU"], delta=THESIS["DELTA"], previous=previous
        )


# ---------------------------------------------------------------------------
# V-A3 — properties
# ---------------------------------------------------------------------------


def test_v_a3_the_constants_are_chapter_twos_and_bound_guess_and_slip():
    """P(G) ≤ 0.3 and P(S) ≤ 0.1, so P(G) + P(S) < 1 always."""
    assert (THESIS["G_MAX"], THESIS["S_MAX"]) == (G_MAX, S_MAX)
    rng = Random(SEED + 3)
    for _ in range(5_000):
        g = irt.guess(
            g0=rng.uniform(0.01, G_MAX - 0.01), g_max=G_MAX, a_q=THESIS["A_Q"],
            theta=rng.uniform(-20.0, 20.0), b_q=rng.uniform(-20.0, 20.0),
        )
        s = irt.slip(
            s0=rng.uniform(0.005, S_MAX - 0.005), s_max=S_MAX, a_q=THESIS["A_Q"],
            theta=rng.uniform(-20.0, 20.0), b_q=rng.uniform(-20.0, 20.0),
        )
        assert 0.0 < g <= G_MAX and 0.0 < s <= S_MAX
        assert g + s < 1.0


def test_v_a3_assertion_2_5_holds_for_the_posterior_before_the_transition():
    """
    P(G) + P(S) < 1 ⇒ P(L|1) > P(L) and P(L|0) < P(L), stated for the
    posterior and not for P(L)′: after the PT transition a wrong answer can
    still raise P(L), which section 4 asks the tests to document.
    """
    rng = Random(SEED + 4)
    transition_raised_after_a_wrong_answer = 0
    for _ in range(5_000):
        p_l = rng.uniform(0.001, 0.999)
        g = rng.uniform(0.001, G_MAX)
        s = rng.uniform(0.001, S_MAX)
        correct = bkt.step(p_l=p_l, guess=g, slip=s, pt=rng.uniform(0.0, 0.5), is_correct=True)
        wrong = bkt.step(p_l=p_l, guess=g, slip=s, pt=rng.uniform(0.0, 0.5), is_correct=False)
        assert correct.posterior > p_l
        assert wrong.posterior < p_l
        if wrong.p_after > p_l:
            transition_raised_after_a_wrong_answer += 1
    assert transition_raised_after_a_wrong_answer > 0, (
        "with PT > 0 some wrong answers must still end above P(L); if none do, "
        "the transition is not being applied"
    )


def test_v_a3_every_probability_stays_in_the_unit_interval():
    constants = _constants()
    rng = Random(SEED + 5)
    for _ in range(5_000):
        case = _random_case(rng)
        produced = student.observe(
            params=student.TopicParams(
                p0=case["p0"], pt=case["pt"], g0=case["g0"], s0=case["s0"],
            ),
            constants=constants,
            observation=student.Observation(
                is_correct=case["is_correct"], p_l=case["p_l"],
                theta=case["theta"], b_q=case["b_q"],
                n_student=case["n_student"], n_question=case["n_question"],
                prerequisites=tuple(
                    init.Prerequisite(weight=w, p_l=p, p0=p0)
                    for w, p, p0 in case["prerequisites"]
                ),
            ),
            flags=student.Flags(
                use_irt=case["use_irt"], use_prereq_init=case["use_prereq_init"],
            ),
        )
        for field in ("p_before", "p_hat", "posterior", "p_after", "guess", "slip"):
            value = getattr(produced, field)
            assert 0.0 <= value <= 1.0, (field, value, case)
            assert math.isfinite(value)


def test_v_a3_theta_never_leaves_the_clamp():
    """
    |θ| ≤ THETA_CLAMP however many answers arrive, in either direction.

    ``k_question=0`` holds the item still, so θ keeps being pushed the same way
    and the clamp is actually reached; when b moves as well, θ − b grows, the
    residual (x − p) decays and θ settles below the clamp on its own.
    """
    clamp = THESIS["THETA_CLAMP"]
    reached = []
    for correct in (True, False):
        theta, b = 0.0, 0.0
        for n in range(500):
            moved = elo.update(
                theta=theta, b=b, is_correct=correct,
                k_student=elo.k_factor(0, alpha=THESIS["ELO_ALPHA"], beta=0.0),
                k_question=0.0,
                theta_clamp=clamp,
            )
            theta, b = moved.theta, moved.b
            assert -clamp <= theta <= clamp, n
        reached.append(theta)
    assert reached == pytest.approx([clamp, -clamp], abs=1e-6), (
        "500 answers in one direction, with the item held still, should reach "
        "the clamp at both ends"
    )


def test_v_a3_a_q_zero_and_lambda_zero_reproduce_classical_bkt():
    """
    With a_q = 0 the guess and slip stop moving, and with λ = 0 the prior is
    P0: the model is then exactly the BKT sequence of section 4.
    """
    constants = _constants(a_q=0.0, lam=0.0)
    params = student.TopicParams(p0=0.3, pt=0.1, g0=0.2, s0=0.05)
    p_l = None
    classical = 0.3
    for _ in range(4):
        produced = student.observe(
            params=params,
            constants=constants,
            observation=student.Observation(
                is_correct=True, p_l=p_l, theta=2.5, b_q=-1.0,
                prerequisites=(init.Prerequisite(weight=1.0, p_l=0.9, p0=0.9),),
            ),
            flags=student.Flags(use_irt=False, use_prereq_init=False),
        )
        # guess and slip are the topic's own base values, untouched by θ and b
        assert produced.guess == pytest.approx(0.2, abs=1e-12)
        assert produced.slip == pytest.approx(0.05, abs=1e-12)
        assert produced.theta_after == 2.5 and produced.b_after == -1.0
        classical = bkt.step(
            p_l=classical, guess=0.2, slip=0.05, pt=0.1, is_correct=True
        ).p_after
        assert produced.p_after == pytest.approx(classical, abs=1e-12)
        p_l = produced.p_after
