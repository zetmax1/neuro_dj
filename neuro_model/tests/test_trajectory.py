"""
Algorithm 2.5 and the goal path (3.5), on the reference course of section 4.

Expected values the specification fixes:

- Need(t7) = {t4, t6} and the path t4 → t6 → t7;
- the review priority case: t1 = 0.80 and t3 = 0.70 in review, t5 mastered,
  t6–t8 unmastered → t1 first (impact 4), then t3 (impact 3).
"""

from __future__ import annotations

import pytest

from neuro_model import readiness as r
from neuro_model import trajectory as tr

# E_L of section 4: t4 → B3 is inherited down to t6, t7 and t8.
PREDECESSORS: dict[int, tuple[int, ...]] = {
    1: (), 2: (), 3: (1,), 4: (2,), 5: (1,),
    6: (3, 4, 5), 7: (4, 6), 8: (4, 6),
}
# Desc*(v), the transitive closure in G_L.
DESCENDANTS: dict[int, tuple[int, ...]] = {
    1: (3, 5, 6, 7, 8),
    2: (4, 6, 7, 8),
    3: (6, 7, 8),
    4: (6, 7, 8),
    5: (6, 7, 8),
    6: (7, 8),
    7: (),
    8: (),
}
ORDER = (1, 2, 3, 4, 5, 6, 7, 8)


def test_the_reference_descendant_counts_match_section_four():
    """|Desc*| = 5, 4, 3, 3, 3, 2, 0, 0 — the fixture is the right graph."""
    assert [len(DESCENDANTS[t]) for t in ORDER] == [5, 4, 3, 3, 3, 2, 0, 0]


# ---------------------------------------------------------------------------
# impact
# ---------------------------------------------------------------------------

def test_impact_counts_unmastered_descendants():
    flags = {5: True}
    assert tr.impact(topic=1, descendants=DESCENDANTS, flags=flags) == 4
    assert tr.impact(topic=3, descendants=DESCENDANTS, flags=flags) == 3
    assert tr.impact(topic=7, descendants=DESCENDANTS, flags=flags) == 0


def test_impact_is_zero_when_everything_below_is_mastered():
    flags = {node: True for node in ORDER}
    assert tr.impact(topic=1, descendants=DESCENDANTS, flags=flags) == 0


# ---------------------------------------------------------------------------
# The review priority case of section 4
# ---------------------------------------------------------------------------

def review_case() -> dict:
    """t1=0.80 and t3=0.70 in review, t5 mastered, t6–t8 unmastered."""
    statuses = {
        1: r.REVIEW, 2: r.MASTERED, 3: r.REVIEW, 4: r.MASTERED,
        5: r.MASTERED, 6: r.OPEN, 7: r.CLOSED, 8: r.CLOSED,
    }
    flags = {1: False, 2: True, 3: False, 4: True, 5: True, 6: False, 7: False, 8: False}
    mastery = {1: 0.80, 2: 0.99, 3: 0.70, 4: 0.99, 5: 0.99, 6: 0.1, 7: 0.0, 8: 0.0}
    return {
        "order": ORDER,
        "statuses": statuses,
        "flags": flags,
        "mastery": mastery,
        "descendants": DESCENDANTS,
        "predecessors": PREDECESSORS,
    }


def test_review_priority_of_section_four():
    steps = tr.trajectory(**review_case())
    group_a = [step for step in steps if step.group == tr.GROUP_REVIEW]

    assert [step.topic for step in group_a] == [1, 3]
    assert group_a[0].reason.code == "review_impact"
    assert group_a[0].reason.params == {"impact": 4, "p": 0.80}
    assert group_a[1].reason.params == {"impact": 3, "p": 0.70}


def test_a_weaker_topic_wins_an_impact_tie():
    case = review_case()
    # Give t3 the same impact as t1 by mastering t3 itself out of t1's set.
    case["statuses"] = {**case["statuses"], 5: r.REVIEW}
    case["flags"] = {**case["flags"], 5: False}
    case["mastery"] = {**case["mastery"], 1: 0.90, 5: 0.50}
    steps = [s for s in tr.trajectory(**case) if s.group == tr.GROUP_REVIEW]
    impacts = {s.topic: s.reason.params["impact"] for s in steps}

    # Equal impact resolves on P(L) ascending.
    for earlier, later in zip(steps, steps[1:]):
        if impacts[earlier.topic] == impacts[later.topic]:
            assert earlier.reason.params["p"] <= later.reason.params["p"]


def test_mastered_topics_are_not_in_the_trajectory():
    steps = tr.trajectory(**review_case())
    assert 2 not in [step.topic for step in steps]
    assert 4 not in [step.topic for step in steps]


def test_the_groups_come_in_order_a_b_c_d():
    case = review_case()
    case["statuses"] = {**case["statuses"], 6: r.IN_PROGRESS}
    steps = tr.trajectory(**case)
    groups = [step.group for step in steps]
    assert groups == sorted(groups), "A before B before C before D"
    assert groups == ["A", "A", "B", "D", "D"]


def test_closed_items_carry_their_unmastered_predecessors():
    steps = tr.trajectory(**review_case())
    blocked = {step.topic: step for step in steps if step.group == tr.GROUP_CLOSED}

    assert blocked[7].missing == (6,), "t4 is mastered, so only t6 is in the way"
    assert blocked[7].reason.code == "blocked"
    assert blocked[7].reason.params == {"missing": 1}
    assert blocked[8].missing == (6,)


def test_open_and_in_progress_keep_topological_order():
    statuses = {t: r.OPEN for t in ORDER}
    statuses[4] = r.IN_PROGRESS
    case = {
        "order": ORDER,
        "statuses": statuses,
        "flags": {},
        "mastery": {},
        "descendants": DESCENDANTS,
        "predecessors": PREDECESSORS,
    }
    steps = tr.trajectory(**case)
    assert [s.topic for s in steps if s.group == tr.GROUP_IN_PROGRESS] == [4]
    assert [s.topic for s in steps if s.group == tr.GROUP_OPEN] == [1, 2, 3, 5, 6, 7, 8]


def test_a_topic_with_no_state_is_treated_as_closed():
    case = {
        "order": ORDER,
        "statuses": {},
        "flags": {},
        "mastery": {},
        "descendants": DESCENDANTS,
        "predecessors": PREDECESSORS,
    }
    steps = tr.trajectory(**case)
    assert {step.group for step in steps} == {tr.GROUP_CLOSED}
    assert [step.topic for step in steps] == list(ORDER)


def test_every_reason_is_a_code_and_numbers_not_a_sentence():
    case = review_case()
    case["statuses"] = {**case["statuses"], 6: r.IN_PROGRESS}
    for step in tr.trajectory(**case):
        assert step.reason.code in {"review_impact", "in_progress", "ready", "blocked"}
        assert step.reason.code.replace("_", "").isalpha()
        assert all(isinstance(value, (int, float)) for value in step.reason.params.values())


# ---------------------------------------------------------------------------
# Need(g) and the path — the value of section 4
# ---------------------------------------------------------------------------

def readiness_case() -> dict:
    """
    The readiness example's learner before the two answers on t4:
    t1, t2, t3, t5 mastered and t4 in_progress at 0.62.
    """
    statuses = {
        1: r.MASTERED, 2: r.MASTERED, 3: r.MASTERED, 5: r.MASTERED,
        4: r.IN_PROGRESS, 6: r.CLOSED, 7: r.CLOSED, 8: r.CLOSED,
    }
    flags = {1: True, 2: True, 3: True, 5: True, 4: False, 6: False, 7: False, 8: False}
    return {"statuses": statuses, "flags": flags, "predecessors": PREDECESSORS}


def test_need_of_t7_is_t4_and_t6():
    assert tr.need(goal=7, **readiness_case()) == frozenset({4, 6})


def test_the_path_to_t7_is_t4_t6_t7():
    case = readiness_case()
    needed = tr.need(goal=7, **case)
    assert tr.path_to(goal=7, needed=needed, order=ORDER) == (4, 6, 7)


def test_need_stops_at_a_topic_that_is_already_open():
    """t4 is in_progress, so it is needed but its own Pre is not walked."""
    needed = tr.need(goal=6, **readiness_case())
    assert needed == frozenset({4})
    assert 2 not in needed, "t2 is mastered and behind an open topic"


def test_need_of_an_open_goal_is_empty_and_the_path_is_just_the_goal():
    case = readiness_case()
    assert tr.need(goal=4, **case) == frozenset()
    assert tr.path_to(goal=4, needed=(), order=ORDER) == (4,)


def test_need_of_a_mastered_goal_is_empty():
    case = readiness_case()
    assert tr.need(goal=1, **case) == frozenset()


def test_need_recurses_through_a_chain_of_closed_topics():
    """Nothing mastered: reaching t7 needs everything that leads to it."""
    statuses = {t: r.CLOSED for t in ORDER}
    needed = tr.need(goal=7, statuses=statuses, flags={}, predecessors=PREDECESSORS)
    assert needed == frozenset({1, 2, 3, 4, 5, 6})
    assert tr.path_to(goal=7, needed=needed, order=ORDER) == (1, 2, 3, 4, 5, 6, 7)


def test_need_never_includes_the_goal():
    statuses = {t: r.CLOSED for t in ORDER}
    for goal in ORDER:
        assert goal not in tr.need(
            goal=goal, statuses=statuses, flags={}, predecessors=PREDECESSORS,
        )


def test_need_terminates_on_a_diamond():
    """t6 is reached through t3, t4 and t5; it must be visited once."""
    statuses = {t: r.CLOSED for t in ORDER}
    needed = tr.need(goal=8, statuses=statuses, flags={}, predecessors=PREDECESSORS)
    assert needed == frozenset({1, 2, 3, 4, 5, 6})


@pytest.mark.parametrize("goal", ORDER)
def test_the_path_always_ends_at_the_goal(goal):
    statuses = {t: r.CLOSED for t in ORDER}
    needed = tr.need(goal=goal, statuses=statuses, flags={}, predecessors=PREDECESSORS)
    path = tr.path_to(goal=goal, needed=needed, order=ORDER)
    assert path[-1] == goal
    assert len(set(path)) == len(path), "no topic appears twice"
