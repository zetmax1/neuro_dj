"""
H1 — the readiness rules (D61, D62).

The rules are decisions, so the tests are about decisions: what counts as an
event, what each rule reads, that it reads it from the state **before** the
answer, that the equal-coverage search matches the rule it is compared with on
validation and not on test, and that the reading rule written before the run
is the one applied. The last test runs the whole module on the synthetic log
and checks the table cell by cell (D48).
"""

from __future__ import annotations

import json

import pytest

from experiments import h1, tables
from experiments.datasets import junyi
from experiments.models.classical import BKTFamily
from neuro_model import readiness


def answer(user, skill, correct, *, order, proficiency=False, number=1):
    return junyi.Answer(
        user_id=user,
        order_id=order,
        problem_id=f"{skill}:p0",
        skill_id=skill,
        correct=int(correct),
        exercise=skill,
        problem_number=number,
        earned_proficiency=proficiency,
        review_mode=False,
        time_done=1_400_000_000_000_000 + order,
    )


class Graph:
    """Just enough of ``JunyiGraph`` for ``collect_events``: Pre(w) and ω."""

    WEIGHT = 1.0

    def __init__(self, prerequisites):
        self.prerequisites = prerequisites
        self.skills = tuple(prerequisites)

    def weighted_prerequisites(self):
        return {
            skill: tuple((pre, self.WEIGHT) for pre in values)
            for skill, values in self.prerequisites.items()
        }


def events_of(rows, prerequisites, **kwargs):
    graph = Graph(prerequisites)
    model = BKTFamily("BKT+IRT (λ=0)", use_irt=True, use_prereq_init=False)
    model.fit(rows)
    return h1.collect_events(rows, model=model, graph=graph, fold=0, **kwargs)


CHAIN = {"a": (), "b": ("a",), "c": ("a", "b")}


# ---------------------------------------------------------------------------
# What an event is
# ---------------------------------------------------------------------------

def test_an_event_is_a_first_attempt_with_a_practised_prerequisite():
    rows = [
        answer("1", "a", True, order=0),
        answer("1", "b", True, order=1),    # event: a was practised
        answer("1", "b", True, order=2),    # not a first attempt
    ]

    events = events_of(rows, CHAIN)

    assert [(event.user_id, event.skill) for event in events] == [("1", "b")]
    assert events[0].prerequisites == 1
    assert events[0].answered_prerequisites == 1


def test_a_topic_without_prerequisites_is_not_an_event():
    rows = [answer("1", "a", True, order=0)]

    assert events_of(rows, CHAIN) == []


def test_a_first_attempt_with_no_prerequisite_practised_is_not_an_event():
    """The learner jumped straight in; no rule has anything to read."""
    rows = [answer("1", "b", True, order=0), answer("1", "a", True, order=1)]

    assert events_of(rows, CHAIN) == []


def test_the_event_reads_the_state_before_the_answer():
    """
    The answer at the event itself must not be in the features: that is the
    answer the decision is being judged against.
    """
    rows = [
        answer("1", "a", True, order=0),
        answer("1", "b", False, order=1),
        answer("1", "b", False, order=2),
        answer("1", "b", False, order=3),
    ]

    event = events_of(rows, CHAIN)[0]

    assert event.prerequisite_accuracy == 1.0      # only a's answer
    assert event.answered_prerequisites == 1
    assert event.correct_after == (0, 0, 0)        # and b's answers are the outcome


def test_an_unanswered_prerequisite_enters_as_zero_and_not_mastered():
    """The platform's own reading (``readiness.readiness_at``)."""
    rows = [
        answer("1", "a", True, order=0),
        answer("1", "c", True, order=1),    # c needs a and b; b is untouched
    ]

    event = events_of(rows, CHAIN)[0]

    assert len(event.prerequisite_mastery) == 2
    assert min(event.prerequisite_mastery) == 0.0
    assert event.readiness_score == 0.0
    assert event.answered_prerequisites == 1
    assert event.flags(tau=0.95, delta=0.1)[h1.COMPLETENESS] is False


def test_the_readiness_score_is_the_models_own_function():
    rows = [answer("1", "a", True, order=0), answer("1", "b", True, order=1)]

    event = events_of(rows, CHAIN)[0]

    assert event.readiness_score == readiness.readiness_score(event.prerequisite_mastery)


def test_m_carries_the_hysteresis_of_the_model():
    """
    δ reaches the decision only through M, and M is path-dependent — so the
    flag is tracked along the stream for every (τ, δ) rather than recomputed.
    """
    rows = [answer("1", "a", True, order=0), answer("1", "b", True, order=1)]

    event = events_of(rows, CHAIN, taus=(0.2,), deltas=(0.05, 0.9))[0]

    assert set(event.ready) == {(0.2, 0.05), (0.2, 0.9)}
    assert event.ready[(0.2, 0.05)] == event.ready[(0.2, 0.9)]


def test_earned_proficiency_is_the_platforms_own_rule():
    rows = [
        answer("1", "a", True, order=0, proficiency=True),
        answer("1", "b", True, order=1),
    ]

    event = events_of(rows, CHAIN)[0]

    assert event.proficient_prerequisites == 1
    assert event.flags(tau=0.95, delta=0.1)[h1.PROFICIENCY] is True


def test_the_pass_mark_rule_is_the_accuracy_over_the_prerequisites():
    rows = [
        answer("1", "a", True, order=0),
        answer("1", "a", False, order=1),
        answer("1", "b", True, order=2),
    ]

    event = events_of(rows, CHAIN)[0]

    assert event.prerequisite_accuracy == 0.5
    assert event.flags(tau=0.95, delta=0.1)[h1.PASS_MARK_RULE] is False
    assert h1.PASS_MARK == 0.60


# ---------------------------------------------------------------------------
# Failure, coverage, τ
# ---------------------------------------------------------------------------

def test_a_failure_is_less_than_half_correct_in_the_first_k():
    rows = [
        answer("1", "a", True, order=0),
        answer("1", "b", False, order=1),
        answer("1", "b", True, order=2),
        answer("1", "b", False, order=3),
    ]

    event = events_of(rows, CHAIN)[0]

    assert event.correct_after == (0, 1, 0)
    assert event.failed(3) is True
    assert event.failed(1) is True
    assert event.failed(2) is False       # one of two correct is not below half


def test_an_event_with_no_answer_window_is_not_scored():
    event = h1.Event(
        user_id="1", skill="b", fold=0, prerequisites=1, prerequisite_mastery=(0.9,),
        answered_prerequisites=1, prerequisite_accuracy=1.0, proficient_prerequisites=1,
    )

    assert event.failed(3) is None


def _event(score, *, failed, user="1"):
    """An event with a chosen r and outcome, for the search and the shares."""
    window = (0, 0, 0) if failed else (1, 1, 1)
    return h1.Event(
        user_id=user, skill="b", fold=0, prerequisites=1, prerequisite_mastery=(score,),
        answered_prerequisites=1, prerequisite_accuracy=1.0, proficient_prerequisites=1,
        correct_after=window,
    )


def test_the_equal_coverage_search_matches_the_target():
    events = [_event(score / 10, failed=False) for score in range(1, 11)]

    tau = h1.tau_for_coverage(events, 0.5)

    assert h1.coverage(events, h1.PROBABILISTIC, tau=tau, delta=0.1) == pytest.approx(0.5)


def test_the_search_prefers_the_stricter_tau_on_a_tie():
    """Two τ with the same coverage: the higher one, so coverage is not bought."""
    events = [_event(0.4, failed=False), _event(0.8, failed=False)]

    assert h1.tau_for_coverage(events, 0.5) == 0.8


def test_the_error_share_counts_only_the_flagged_events():
    events = [_event(0.9, failed=True), _event(0.9, failed=False), _event(0.1, failed=True)]
    flags = [event.flags(tau=0.5, delta=0.1) for event in events]

    scores = h1.rule_scores(events, flags, h1.PROBABILISTIC, 3)

    assert scores == {
        "events": 3, "flagged": 2, "failed": 1, "coverage": 0.666667, "error_share": 0.5,
    }


# ---------------------------------------------------------------------------
# The reading rule
# ---------------------------------------------------------------------------

def _entry(rule, low, high):
    return {"rule": rule, "difference": {"estimate": (low + high) / 2,
                                         "ci_low": low, "ci_high": high}}


def test_the_reading_rule_is_supported_only_when_both_intervals_exclude_zero():
    both = h1.reading([_entry("completeness", -0.2, -0.05), _entry("pass_mark", -0.3, -0.1)])
    assert both["status"] == h1.SUPPORTED

    one = h1.reading([_entry("completeness", -0.2, -0.05), _entry("pass_mark", -0.1, 0.1)])
    assert one["status"] == h1.UNDETERMINED

    against = h1.reading([_entry("completeness", 0.05, 0.2), _entry("pass_mark", -0.3, -0.1)])
    assert against["status"] == h1.NOT_SUPPORTED

    missing = h1.reading([{"rule": "completeness", "difference": {}}])
    assert missing["status"] == h1.UNDETERMINED


def test_the_sensitivity_grid_is_tau_times_delta():
    events = [_event(0.9, failed=False), _event(0.1, failed=True)]

    grid = h1.sensitivity(events, k=3)

    assert len(grid) == len(h1.TAU_GRID) * len(h1.DELTA_GRID)
    assert {entry["tau"] for entry in grid} == set(h1.TAU_GRID)
    assert {entry["delta"] for entry in grid} == set(h1.DELTA_GRID)


def test_tau_and_delta_are_chapter_twos():
    settings = pytest.importorskip("django.conf").settings
    if not settings.configured:  # pragma: no cover - plain experiment venv
        pytest.skip("Django is not configured in this environment")

    assert h1.CHAPTER_TWO_DELTA == settings.THESIS_MODEL["DELTA"]
    assert h1.TAU_GRID[-1] == settings.THESIS_MODEL["TAU"]


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------

def test_the_pipeline_writes_a_table_that_verifies_cell_by_cell(junyi_small, tmp_path):
    """
    The whole module on the synthetic log: every number in ``tables.md`` is a
    scalar of ``metrics.json`` (D48) and every cell is the number under its own
    key (the positional check).
    """
    out = tmp_path / "h1"
    code = h1.main([
        "--quick", "--no-verify", "--data", str(junyi_small),
        "--learners", "60", "--replicates", "20", "--workers", "1", "--out", str(out),
    ])

    assert code == 0
    document = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    markdown = (out / "tables.md").read_text(encoding="utf-8")

    assert document["report"] == "h1"
    assert document["thesis_result"] is False
    assert tables.verify(markdown, document) == []
    assert tables.verify_h1_positions(markdown, document) == []
    assert "dissertatsiya natijasi emas" in markdown
    assert {entry["rule"] for entry in document["rules"]} == {
        h1.PROBABILISTIC, h1.CHAPTER_TWO, h1.COMPLETENESS, h1.PASS_MARK_RULE, h1.PROFICIENCY,
    }
    assert document["reading"]["status"] in (h1.SUPPORTED, h1.NOT_SUPPORTED, h1.UNDETERMINED)

    # A cell holding another key's number is caught, even though that number
    # is somewhere in metrics.json (the positional check of D48).
    row = next(line for line in markdown.splitlines() if line.startswith("| ehtimoliy"))
    cells = row.split("|")
    cells[-2] = " 0 "
    broken = markdown.replace(row, "|".join(cells))
    assert tables.verify_h1_positions(broken, document) != []
    assert tables.verify(broken, document) != []


def test_a_missing_dataset_is_a_sentence_not_a_crash(tmp_path):
    assert h1.main(["--quick", "--data", str(tmp_path / "nowhere")]) == 2
