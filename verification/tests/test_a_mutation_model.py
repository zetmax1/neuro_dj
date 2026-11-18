"""
Mutation score of the student model (V-A4, stage 3 part).

``mutmut`` is not used — a full run is slower than the 30 minutes V-A4 allows
and would mutate code paths the groups below do not claim to check. Instead
each mutant here breaks one rule of specification §3.3 on purpose (a wrong
order inside algorithm 2.4, a dropped factor, a missing cap) and the test
asserts that the differential comparison of V-A2 notices. A surviving mutant
would mean V-A1/V-A2 prove less than they claim.

The mutants patch the leaf functions ``neuro_model.student`` calls, so the
module under test is the real one; nothing is written to ``neuro_model``.
"""

from __future__ import annotations

from random import Random

import pytest
from django.conf import settings

from neuro_model import bkt, elo, init, irt, student
from verification.oracle import model as oracle

SEED: int = settings.VERIFICATION_SEED
THESIS = settings.THESIS_MODEL


def _constants() -> student.Constants:
    return student.Constants(
        g_max=THESIS["G_MAX"], s_max=THESIS["S_MAX"], a_q=THESIS["A_Q"],
        elo_alpha=THESIS["ELO_ALPHA"], elo_beta=THESIS["ELO_BETA"],
        lam=THESIS["LAMBDA"], tau=THESIS["TAU"], c_offset=THESIS["C_OFFSET"],
        theta_clamp=THESIS["THETA_CLAMP"],
    )


def _disagreements(cases: int = 400) -> int:
    """
    How many of ``cases`` random answers disagree with the oracle beyond 1e-9.

    This is V-A2's comparison in miniature: the same inputs, the same fields.
    """
    constants = _constants()
    rng = Random(SEED + 11)
    found = 0
    for index in range(cases):
        # Every fourth case is a strong one — a high P0 over well-known
        # prerequisites — so that the cap c = τ − C_OFFSET actually binds in
        # part of the sample and a mutant that drops it has somewhere to show.
        strong = index % 4 == 0
        case = dict(
            p0=rng.uniform(0.9, 0.99) if strong else rng.uniform(0.05, 0.9),
            pt=rng.uniform(0.01, 0.4),
            g0=rng.uniform(0.02, THESIS["G_MAX"] - 0.02),
            s0=rng.uniform(0.01, THESIS["S_MAX"] - 0.01),
            is_correct=rng.random() < 0.5,
            p_l=None if rng.random() < 0.3 else rng.uniform(0.05, 0.95),
            theta=rng.uniform(-2.0, 2.0),
            b_q=rng.uniform(-2.0, 2.0),
            n_student=rng.randint(0, 50),
            n_question=rng.randint(0, 50),
        )
        prerequisites = tuple(
            (
                rng.uniform(0.2, 1.0),
                rng.uniform(0.95, 0.999) if strong else rng.uniform(0.1, 0.99),
                rng.uniform(0.9, 0.99) if strong else rng.uniform(0.1, 0.9),
            )
            for _ in range(rng.randint(1, 3))
        )
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
                    init.Prerequisite(weight=w, p_l=p, p0=p0) for w, p, p0 in prerequisites
                ),
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
                oracle.Pre(weight=w, p_l=p, p0=p0) for w, p, p0 in prerequisites
            ),
        )
        for field in (
            "p_before", "p_hat", "posterior", "p_after", "guess", "slip",
            "theta_after", "b_after",
        ):
            if abs(getattr(produced, field) - getattr(expected, field)) > 1e-9:
                found += 1
                break
    return found


# --- the mutants -----------------------------------------------------------


def _mutant_p_hat_after_the_update(monkeypatch):
    """Step 3 after step 4: p̂ from the posterior instead of the old P(L)."""
    original = bkt.step

    def mutated(*, p_l, guess, slip, pt, is_correct):
        step = original(p_l=p_l, guess=guess, slip=slip, pt=pt, is_correct=is_correct)
        wrong = bkt.predict(p_l=step.posterior, guess=guess, slip=slip)
        return bkt.BKTStep(
            p_hat=wrong, posterior=step.posterior, p_after=step.p_after,
        )

    monkeypatch.setattr(bkt, "step", mutated)


def _mutant_posterior_drops_one_minus_slip(monkeypatch):
    """P(L|1) = P(L) / p̂, the (1 − P(S)) factor dropped."""
    original = bkt.posterior

    def mutated(*, p_l, guess, slip, is_correct):
        if is_correct:
            return p_l / bkt.predict(p_l=p_l, guess=guess, slip=slip)
        return original(p_l=p_l, guess=guess, slip=slip, is_correct=is_correct)

    monkeypatch.setattr(bkt, "posterior", mutated)
    _rebuild_step(monkeypatch, posterior=mutated)


def _mutant_transition_before_bayes(monkeypatch):
    """Steps 4 and 5 swapped: the PT transition applied to P(L), then Bayes."""
    def mutated(*, p_l, guess, slip, pt, is_correct):
        moved = bkt.transition(posterior=p_l, pt=pt)
        post = bkt.posterior(p_l=moved, guess=guess, slip=slip, is_correct=is_correct)
        return bkt.BKTStep(
            p_hat=bkt.predict(p_l=moved, guess=guess, slip=slip),
            posterior=post,
            p_after=post,
        )

    monkeypatch.setattr(bkt, "step", mutated)


def _mutant_slip_uses_the_guess_sign(monkeypatch):
    """P(S) = S_MAX·σ(γ_S + a(θ − b)): the sign of the IRT term flipped."""
    def mutated(*, s0, s_max, a_q, theta, b_q):
        return s_max * irt.sigma(irt.gamma(s0, s_max) + a_q * (theta - b_q))

    monkeypatch.setattr(irt, "slip", mutated)


def _mutant_k_ignores_the_answer_count(monkeypatch):
    """K(n) = ELO_ALPHA: the 1 / (1 + β·n) decay dropped."""
    monkeypatch.setattr(elo, "k_factor", lambda n, *, alpha, beta: alpha)


def _mutant_gamma_without_the_complement(monkeypatch):
    """γ = ln(base / bound) instead of ln(base / (bound − base))."""
    import math

    monkeypatch.setattr(irt, "gamma", lambda base, bound: math.log(base / bound))


def _mutant_initial_mastery_without_the_cap(monkeypatch):
    """P(L0) without min{…, τ − C_OFFSET}, so a strong prerequisite set runs over c."""
    def mutated(*, p0, prerequisites, lam, cap):
        mean = init.mean_prerequisite_mastery(prerequisites)
        if mean is None:
            return p0
        return (1.0 - lam) * p0 + lam * mean

    monkeypatch.setattr(student, "initial_mastery", mutated)


def _rebuild_step(monkeypatch, *, posterior):
    """``bkt.step`` recomposed over a patched leaf, as the module composes it."""
    def mutated(*, p_l, guess, slip, pt, is_correct):
        post = posterior(p_l=p_l, guess=guess, slip=slip, is_correct=is_correct)
        return bkt.BKTStep(
            p_hat=bkt.predict(p_l=p_l, guess=guess, slip=slip),
            posterior=post,
            p_after=bkt.transition(posterior=post, pt=pt),
        )

    monkeypatch.setattr(bkt, "step", mutated)


MUTANTS = {
    "p_hat_after_the_update": _mutant_p_hat_after_the_update,
    "posterior_drops_one_minus_slip": _mutant_posterior_drops_one_minus_slip,
    "transition_before_bayes": _mutant_transition_before_bayes,
    "slip_uses_the_guess_sign": _mutant_slip_uses_the_guess_sign,
    "k_ignores_the_answer_count": _mutant_k_ignores_the_answer_count,
    "gamma_without_the_complement": _mutant_gamma_without_the_complement,
    "initial_mastery_without_the_cap": _mutant_initial_mastery_without_the_cap,
}


def test_the_unmutated_model_agrees_with_the_oracle():
    """The baseline: without a mutant there is nothing to notice."""
    assert _disagreements() == 0


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_of_the_model_is_caught(name, monkeypatch):
    MUTANTS[name](monkeypatch)
    assert _disagreements() > 0, f"mutant {name} survived the V-A2 comparison"


def test_the_section_four_numbers_also_catch_the_mutants(monkeypatch):
    """
    V-A1 is not only a smoke test: the published BKT sequence alone already
    separates the two mutants that touch its path.
    """
    for name in ("posterior_drops_one_minus_slip", "transition_before_bayes"):
        with monkeypatch.context() as patch:
            MUTANTS[name](patch)
            p_l = 0.3
            produced = []
            for _ in range(4):
                p_l = bkt.step(
                    p_l=p_l, guess=0.2, slip=0.1, pt=0.1, is_correct=True
                ).p_after
                produced.append(round(p_l, 4))
            assert produced != [0.6927, 0.9192, 0.9828, 0.9965], name
