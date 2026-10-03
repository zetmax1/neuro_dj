"""
Section 3.4 and the readiness example of section 4, on the pure functions.

The reference course of section 4 is reused: E_L gives Pre(t6) = {t3, t4, t5}
and Pre(t7) = Pre(t8) = {t4, t6}, so the counters are what the spec states.
"""

from __future__ import annotations

import pytest

from neuro_model import readiness as r

TAU, DELTA = 0.95, 0.10

# Topics of section 4. Pre() is taken from E_L, not from E_P: t4 → B3 is
# inherited down to t6, t7 and t8.
PREDECESSORS: dict[int, tuple[int, ...]] = {
    1: (),
    2: (),
    3: (1,),
    4: (2,),
    5: (1,),
    6: (3, 4, 5),
    7: (4, 6),
    8: (4, 6),
}
SUCCESSORS: dict[int, tuple[int, ...]] = {
    1: (3, 5),
    2: (4,),
    3: (6,),
    4: (6, 7, 8),
    5: (6,),
    6: (7, 8),
    7: (),
    8: (),
}


# ---------------------------------------------------------------------------
# M with hysteresis
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("p", "previous", "expected"),
    [
        (0.97, False, True),    # at or above τ
        (0.95, False, True),
        (0.94, False, False),   # inside the band: keeps previous
        (0.94, True, True),
        (0.86, True, True),     # still inside (τ − δ = 0.85)
        (0.85, True, True),
        (0.84, True, False),    # below τ − δ
        (0.62, True, False),
        (0.62, False, False),
    ],
)
def test_mastered_flag_hysteresis(p, previous, expected):
    assert r.mastered_flag(p_mastery=p, tau=TAU, delta=DELTA, previous=previous) is expected


def test_the_band_prevents_flapping():
    """Inside the band the flag never changes, whichever side it came from."""
    flag = False
    for p in (0.90, 0.86, 0.94, 0.88):
        flag = r.mastered_flag(p_mastery=p, tau=TAU, delta=DELTA, previous=flag)
        assert flag is False
    flag = True
    for p in (0.90, 0.86, 0.94, 0.88):
        flag = r.mastered_flag(p_mastery=p, tau=TAU, delta=DELTA, previous=flag)
        assert flag is True


# ---------------------------------------------------------------------------
# R, r and the counter
# ---------------------------------------------------------------------------

def test_readiness_needs_every_predecessor():
    assert r.is_ready([True, True]) is True
    assert r.is_ready([True, False]) is False
    assert r.is_ready([]) is True, "Pre(w) = ∅ means ready"


def test_readiness_score_is_the_weakest_prerequisite():
    assert r.readiness_score([0.98, 0.62, 0.96]) == pytest.approx(0.62)
    assert r.readiness_score([]) == pytest.approx(1.0)


def test_missing_count():
    assert r.missing_count([True, True, True]) == 0
    assert r.missing_count([True, False, True]) == 1
    assert r.missing_count([False, False]) == 2
    assert r.missing_count([]) == 0


def test_a_new_learner_starts_at_the_size_of_pre():
    counters = r.recompute_counters(predecessors=PREDECESSORS, flags={})
    assert counters == {1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 3, 7: 2, 8: 2}


def test_recompute_treats_an_unknown_topic_as_not_mastered():
    counters = r.recompute_counters(predecessors={6: (3, 4, 5)}, flags={3: True})
    assert counters == {6: 2}


# ---------------------------------------------------------------------------
# The readiness example of section 4
# ---------------------------------------------------------------------------

INITIAL_MASTERY = {1: 0.97, 2: 0.96, 3: 0.98, 5: 0.96, 4: 0.62}


def initial_flags() -> dict[int, bool]:
    return {
        topic: r.mastered_flag(p_mastery=p, tau=TAU, delta=DELTA, previous=False)
        for topic, p in INITIAL_MASTERY.items()
    }


def test_the_initial_flags_of_section_four():
    flags = initial_flags()
    assert flags == {1: True, 2: True, 3: True, 5: True, 4: False}


def test_the_initial_counters_of_section_four():
    counters = r.recompute_counters(predecessors=PREDECESSORS, flags=initial_flags())
    # t6 waits only on t4; t7 and t8 wait on t4 and t6.
    assert counters[6] == 1
    assert counters[7] == 2
    assert counters[8] == 2


def test_the_first_correct_answer_leaves_the_counters_alone():
    """P(L) 0.62 → 0.8921 is inside the band, so M stays 0 and nothing moves."""
    flags = initial_flags()
    after = r.mastered_flag(p_mastery=0.8921, tau=TAU, delta=DELTA, previous=flags[4])
    assert after is False
    assert after == flags[4], "M did not change, so Algorithm 2.3 stops at step 2"


def test_the_second_correct_answer_opens_t6_and_moves_t7_t8():
    """P(L) 0.9764 ≥ τ, so M(t4) flips and its successors move by one."""
    flags = initial_flags()
    counters = r.recompute_counters(predecessors=PREDECESSORS, flags=flags)
    statuses = {6: r.CLOSED, 7: r.CLOSED, 8: r.CLOSED}

    became = r.mastered_flag(p_mastery=0.9764, tau=TAU, delta=DELTA, previous=flags[4])
    assert became is True and became != flags[4]

    result = r.propagate(
        became_mastered=True,
        successors=SUCCESSORS[4],
        counters=counters,
        statuses=statuses,
    )

    assert result.counters == {6: 0, 7: 1, 8: 1}
    assert result.opened == (6,)
    assert result.closed == ()


def test_losing_mastery_puts_the_counters_back():
    flags = initial_flags() | {4: True}
    counters = r.recompute_counters(predecessors=PREDECESSORS, flags=flags)
    assert counters[6] == 0

    result = r.propagate(
        became_mastered=False,
        successors=SUCCESSORS[4],
        counters=counters,
        statuses={6: r.OPEN, 7: r.CLOSED, 8: r.CLOSED},
    )

    assert result.counters == {6: 1, 7: 2, 8: 2}
    assert result.closed == (6,), "an open, unstarted topic closes again"
    assert result.opened == ()


def test_a_started_successor_is_not_closed_again():
    """TY5 through the propagation: in_progress is not reported as closing."""
    flags = initial_flags() | {4: True}
    counters = r.recompute_counters(predecessors=PREDECESSORS, flags=flags)

    result = r.propagate(
        became_mastered=False,
        successors=SUCCESSORS[4],
        counters=counters,
        statuses={6: r.IN_PROGRESS, 7: r.CLOSED, 8: r.CLOSED},
    )

    assert result.counters[6] == 1
    assert 6 not in result.closed


def test_the_counter_never_goes_negative():
    result = r.propagate(
        became_mastered=True,
        successors=(6,),
        counters={6: 0},
        statuses={6: r.OPEN},
    )
    assert result.counters == {}, "nothing moved, so nothing is reported"


def test_inheritance_is_only_through_g_l():
    """
    The probe of section 4: a topic under a mastered parent is still closed
    when its own prerequisite is unmastered. There is no parent fallback.
    """
    counters = r.recompute_counters(
        predecessors={100: (200,)}, flags={300: True},  # 300 is the parent, not a predecessor
    )
    assert counters == {100: 1}
    assert r.is_ready([False]) is False


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("current", "mastered", "started", "missing", "expected"),
    [
        (r.CLOSED, False, False, 1, r.CLOSED),
        (r.CLOSED, False, False, 0, r.OPEN),            # the counter reached 0
        (r.OPEN, False, False, 1, r.CLOSED),            # a new prerequisite arrived
        (r.OPEN, False, True, 0, r.IN_PROGRESS),        # the first answer
        (r.IN_PROGRESS, True, True, 0, r.MASTERED),
        (r.IN_PROGRESS, False, True, 0, r.IN_PROGRESS),
        (r.MASTERED, False, True, 0, r.REVIEW),         # M fell back
        (r.REVIEW, True, True, 0, r.MASTERED),          # and returned
        (r.REVIEW, False, True, 0, r.REVIEW),
    ],
)
def test_status_transitions(current, mastered, started, missing, expected):
    assert r.next_status(
        current=current, mastered=mastered, started=started, missing=missing,
    ) == expected


@pytest.mark.parametrize("current", [r.IN_PROGRESS, r.MASTERED, r.REVIEW])
def test_ty5_a_started_topic_is_never_closed(current):
    for missing in (0, 1, 5):
        assert r.next_status(
            current=current, mastered=False, started=True, missing=missing,
        ) != r.CLOSED


def test_mastery_survives_a_missing_prerequisite():
    """
    A mastered topic stays mastered even if a prerequisite is added later:
    the learner has demonstrated it, and TY5 forbids closing it.
    """
    assert r.next_status(
        current=r.MASTERED, mastered=True, started=True, missing=3,
    ) == r.MASTERED


def test_every_status_is_reachable_and_listed():
    assert set(r.STATUSES) == {r.CLOSED, r.OPEN, r.IN_PROGRESS, r.MASTERED, r.REVIEW}
    assert r.STARTED_STATUSES == {r.IN_PROGRESS, r.MASTERED, r.REVIEW}
