"""
neuro_model/tests/test_p_l_max.py — the optional ceiling on P(L)' (D72).

Two things are pinned here, and they are the two halves of the decision.

**At the default the model does not move.** ``p_max=1.0`` has to reproduce the
pre-D72 transition bit for bit, because every result in the dissertation was
produced without the parameter and the experiments still run without it. The
old expression is written out again in this file rather than imported, so a
change to ``bkt.transition`` cannot quietly redefine what "unchanged" means.

**At the recommended setting the saturation ends.** With ``p_max=0.999`` and
the default parameters (P(T)=0.20, G=0.20, S=0.05), a topic sitting at the
ceiling comes back under tau - delta = 0.85 after three consecutive wrong
answers and not after two. That boundary is the reason 0.999 is the
recommended value, so it is a test and not a comment.
"""

from __future__ import annotations

import pytest

from neuro_model import bkt
from neuro_model import student as s

# The chapter II hysteresis: a topic drops out of "mastered" below tau - delta.
TAU, DELTA = 0.95, 0.10
BELOW_MASTERY = TAU - DELTA

# settings._THESIS_DEFAULTS: DEFAULT_PT, DEFAULT_G0, DEFAULT_S0.
PT, GUESS, SLIP = 0.20, 0.20, 0.05

RECOMMENDED_P_MAX = 0.999


def _transition_before_d72(*, posterior: float, pt: float) -> float:
    """``bkt.transition`` as it stood before the parameter was added."""
    updated = posterior + (1.0 - posterior) * pt
    return min(1.0, max(0.0, updated))


# ---------------------------------------------------------------------------
# p_max = 1.0 changes nothing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("posterior", [0.0, 1e-12, 0.1, 0.5, 0.84, 0.95, 1.0 - 1e-15, 1.0])
@pytest.mark.parametrize("pt", [0.0, 0.05, 0.1, 0.2, 0.5, 1.0])
def test_the_default_ceiling_reproduces_the_old_transition_bit_for_bit(posterior, pt):
    assert bkt.transition(posterior=posterior, pt=pt) == _transition_before_d72(
        posterior=posterior, pt=pt,
    )
    assert bkt.transition(posterior=posterior, pt=pt, p_max=1.0) == _transition_before_d72(
        posterior=posterior, pt=pt,
    )


@pytest.mark.parametrize("is_correct", [True, False])
@pytest.mark.parametrize("p_l", [0.0, 0.15, 0.5, 0.9, 0.999, 1.0])
def test_step_is_unchanged_when_the_ceiling_is_not_given(p_l, is_correct):
    given = bkt.step(
        p_l=p_l, guess=GUESS, slip=SLIP, pt=PT, is_correct=is_correct, p_max=1.0,
    )
    omitted = bkt.step(p_l=p_l, guess=GUESS, slip=SLIP, pt=PT, is_correct=is_correct)

    assert given == omitted
    assert omitted.p_after == _transition_before_d72(posterior=omitted.posterior, pt=PT)


def test_the_engines_default_constants_carry_the_neutral_ceiling():
    """``Constants`` built without the field behaves as before (D72, experiments)."""
    constants = s.Constants(
        g_max=0.30, s_max=0.10, a_q=1.0,
        elo_alpha=0.8, elo_beta=0.05,
        lam=0.5, tau=TAU, c_offset=0.05, theta_clamp=4.0,
    )
    assert constants.p_l_max == 1.0


def test_the_ceiling_never_raises_p_l():
    """min() only ever lowers: no p_max can push P(L)' above the old value."""
    for p_max in (0.0, 0.5, 0.9, 0.999, 1.0):
        for posterior in (0.0, 0.3, 0.84, 0.999, 1.0):
            capped = bkt.transition(posterior=posterior, pt=PT, p_max=p_max)
            assert capped <= _transition_before_d72(posterior=posterior, pt=PT)
            assert 0.0 <= capped <= 1.0


# ---------------------------------------------------------------------------
# p_max = 0.999: three wrong answers, not two
# ---------------------------------------------------------------------------

def _wrong_answers(n: int, *, p_max: float) -> float:
    """P(L) after ``n`` consecutive wrong answers, starting at the ceiling."""
    p_l = p_max
    for _ in range(n):
        p_l = bkt.step(
            p_l=p_l, guess=GUESS, slip=SLIP, pt=PT, is_correct=False, p_max=p_max,
        ).p_after
    return p_l


def test_three_wrong_answers_bring_a_saturated_topic_back_under_tau_minus_delta():
    assert _wrong_answers(1, p_max=RECOMMENDED_P_MAX) > BELOW_MASTERY
    assert _wrong_answers(2, p_max=RECOMMENDED_P_MAX) > BELOW_MASTERY
    assert _wrong_answers(3, p_max=RECOMMENDED_P_MAX) < BELOW_MASTERY


def test_without_the_ceiling_the_same_three_answers_leave_the_topic_mastered():
    """The limitation D72 answers, stated as a test.

    From P(L) = 1 the Bayes step returns 1 to within rounding, so three wrong
    answers leave the topic still saturated. What finally moves it is not the
    model but accumulated floating-point error — each step multiplies the
    residual 1 - P(L) by about 13 — and on this build that takes 14 wrong
    answers. The count is an artefact of the arithmetic, not a teaching
    decision, which is the whole argument for a real ceiling; the assertion
    is therefore only that it is far more than three.
    """
    assert _wrong_answers(3, p_max=1.0) == pytest.approx(1.0, abs=1e-9)

    needed = next(
        n for n in range(1, 200) if _wrong_answers(n, p_max=1.0) < BELOW_MASTERY
    )
    assert needed > 10


def test_a_run_of_correct_answers_stops_at_the_ceiling():
    p_l = 0.15
    for _ in range(200):
        p_l = bkt.step(
            p_l=p_l, guess=GUESS, slip=SLIP, pt=PT,
            is_correct=True, p_max=RECOMMENDED_P_MAX,
        ).p_after
    assert p_l == pytest.approx(RECOMMENDED_P_MAX)
    assert p_l <= RECOMMENDED_P_MAX
