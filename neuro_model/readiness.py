"""
neuro_model/readiness.py — mastery flags, readiness and statuses (3.4).

The mastery flag M is deliberately not a plain threshold test. It carries
hysteresis of width δ:

- P ≥ τ          → M = 1
- P < τ − δ      → M = 0
- in between     → M keeps its previous value

so a learner hovering around τ does not flip the topics that depend on them
open and closed on every answer.

Readiness is inherited only through G_L, never from the tree:

- R_s(w) = 1 exactly when M_s(u) = 1 for every u ∈ Pre(w); R = 1 for Pre = ∅;
- r_s(w) = min_{u ∈ Pre(w)} P(L_{s,u}), and 1 for Pre = ∅;
- missing_count_s(w) counts the immediate predecessors with M = 0, so a new
  learner starts at |Pre(w)|.

Algorithm 2.3 keeps the counters rather than recomputing readiness: an answer
changes M for one topic at most, so only its immediate successors need to move
(``propagate``). ``recompute_counters`` is the O(n + m) fallback for TY6, when
the knowledge base has changed under a stored state.

Statuses are closed, open, in_progress, mastered and review. ``next_status``
is the whole transition table, and it enforces TY5: a topic that has been
started never returns to closed.

All functions are pure: they take plain mappings and return new values.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

__all__ = [
    "CLOSED", "OPEN", "IN_PROGRESS", "MASTERED", "REVIEW",
    "STATUSES", "STARTED_STATUSES",
    "mastered_flag", "is_ready", "readiness_score", "missing_count",
    "next_status", "recompute_counters", "Propagation", "propagate",
]

CLOSED = "closed"
OPEN = "open"
IN_PROGRESS = "in_progress"
MASTERED = "mastered"
REVIEW = "review"

STATUSES = (CLOSED, OPEN, IN_PROGRESS, MASTERED, REVIEW)

# TY5: once a topic is in one of these, it never goes back to closed.
STARTED_STATUSES = frozenset({IN_PROGRESS, MASTERED, REVIEW})


# ---------------------------------------------------------------------------
# The mastery flag M
# ---------------------------------------------------------------------------

def mastered_flag(*, p_mastery: float, tau: float, delta: float, previous: bool) -> bool:
    """M with hysteresis of width δ (3.4); ``previous`` holds inside the band."""
    if p_mastery >= tau:
        return True
    if p_mastery < tau - delta:
        return False
    return previous


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------

def is_ready(predecessor_flags: Iterable[bool]) -> bool:
    """R_s(w): every predecessor mastered. True when Pre(w) is empty."""
    return all(predecessor_flags)


def readiness_score(predecessor_mastery: Sequence[float]) -> float:
    """r_s(w) = min P(L) over Pre(w); 1 when Pre(w) is empty."""
    return 1.0 if not predecessor_mastery else min(predecessor_mastery)


def missing_count(predecessor_flags: Iterable[bool]) -> int:
    """How many immediate predecessors still have M = 0."""
    return sum(1 for flag in predecessor_flags if not flag)


# ---------------------------------------------------------------------------
# Statuses
# ---------------------------------------------------------------------------

def next_status(*, current: str, mastered: bool, started: bool, missing: int) -> str:
    """
    The transition table of 3.4, as one expression.

    - closed → open when the counter reaches 0;
    - open → in_progress on the first answer;
    - in_progress → mastered when M = 1;
    - mastered → review when M falls to 0, and review → mastered when it
      returns;
    - open → closed when a new prerequisite arrives and nothing was answered.

    TY5 is the ``started`` branch: a started topic is never closed again, no
    matter what the counter says.
    """
    if started:
        if mastered:
            return MASTERED
        # Falling back out of mastery is review, not a fresh in_progress.
        if current in (MASTERED, REVIEW):
            return REVIEW
        return IN_PROGRESS
    return OPEN if missing == 0 else CLOSED


# ---------------------------------------------------------------------------
# Algorithm 2.3
# ---------------------------------------------------------------------------

def recompute_counters(
    *,
    predecessors: Mapping[int, Sequence[int]],
    flags: Mapping[int, bool],
) -> dict[int, int]:
    """
    Every topic's ``missing_count`` from the M flags — the O(n + m) rebuild
    TY6 falls back to when the stored state predates the current KB version.

    Topics absent from ``flags`` count as M = 0, which is what a learner who
    has never answered them means.
    """
    return {
        topic: missing_count(flags.get(u, False) for u in pre)
        for topic, pre in predecessors.items()
    }


@dataclass(frozen=True)
class Propagation:
    """What one application of Algorithm 2.3 changed."""
    counters: dict[int, int]
    opened: tuple[int, ...]
    closed: tuple[int, ...]

    @property
    def changed(self) -> bool:
        return bool(self.counters)


def propagate(
    *,
    became_mastered: bool,
    successors: Sequence[int],
    counters: Mapping[int, int],
    statuses: Mapping[int, str],
) -> Propagation:
    """
    Steps 3–4 of Algorithm 2.3, for a topic whose M has just changed.

    ``became_mastered`` says which way it moved: each immediate successor's
    counter goes down by one when the topic became mastered and up by one when
    it stopped being mastered. A successor whose counter reaches 0 while it is
    closed opens; one that leaves 0 closes again, unless it has been started
    (TY5), which ``next_status`` decides.

    The caller applies step 1 (recomputing M) and step 2 (stopping when M did
    not change) and passes only the successors of the one topic that moved.
    """
    delta = -1 if became_mastered else 1
    updated: dict[int, int] = {}
    opened: list[int] = []
    closed: list[int] = []

    for topic in successors:
        before = counters.get(topic, 0)
        after = max(0, before + delta)
        if after == before:
            continue
        updated[topic] = after
        status = statuses.get(topic, CLOSED)
        started = status in STARTED_STATUSES
        if after == 0 and status == CLOSED:
            opened.append(topic)
        elif after > 0 and status == OPEN and not started:
            closed.append(topic)

    return Propagation(
        counters=updated,
        opened=tuple(opened),
        closed=tuple(closed),
    )
