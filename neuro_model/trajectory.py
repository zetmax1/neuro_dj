"""
neuro_model/trajectory.py — Algorithm 2.5 and the goal path (chapter II, 3.5).

The trajectory is one ordered list in four groups, so that "what should I do
next" has a single answer rather than four competing heuristics:

- **A — review.** Topics whose mastery has fallen back. Ordered by impact
  descending, then by P(L) ascending: the topic that blocks the most work and
  is weakest comes first. impact(v) = |{w ∈ Desc*(v) : M_s(w) = 0}|.
- **B — in_progress**, in topological order.
- **C — open**, in topological order.
- **D — closed**, in topological order, each carrying the immediate
  predecessors that are still unmastered.

Every item comes back with a structured reason, ``{code, params}``, never a
sentence: the wording belongs to one dictionary file in the frontend (D20), so
the backend states the facts and nothing else.

The goal path answers "what do I have to do to reach g". Need_s(g) walks back
from a closed g through the unmastered members of Pre, recursing only while
the topic it reaches is itself closed — a mastered topic is not needed and an
open one is needed but needs nothing further. The path is Need_s(g) in
topological order with g last; an open g has an empty Need and the path [g].

Ordering is topological, never by ``position``: a learner's next step follows
the prerequisite graph, not the order the instructor happened to type the
topics in.

All functions are pure.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from neuro_model.readiness import CLOSED, IN_PROGRESS, OPEN, REVIEW

__all__ = [
    "GROUPS", "GROUP_REVIEW", "GROUP_IN_PROGRESS", "GROUP_OPEN", "GROUP_CLOSED",
    "Reason", "Step", "impact", "trajectory", "need", "path_to",
]

GROUP_REVIEW = "A"
GROUP_IN_PROGRESS = "B"
GROUP_OPEN = "C"
GROUP_CLOSED = "D"
GROUPS = (GROUP_REVIEW, GROUP_IN_PROGRESS, GROUP_OPEN, GROUP_CLOSED)

# Which status goes in which group. ``mastered`` is in none of them: there is
# nothing to do next on a topic the learner has mastered.
_GROUP_OF_STATUS = {
    REVIEW: GROUP_REVIEW,
    IN_PROGRESS: GROUP_IN_PROGRESS,
    OPEN: GROUP_OPEN,
    CLOSED: GROUP_CLOSED,
}


@dataclass(frozen=True)
class Reason:
    """
    Why an item is where it is: a stable code and the numbers behind it.

    The frontend turns the code into text (D20). ``params`` holds only values
    the learner can be shown, so a reason never has to be recomputed.
    """
    code: str
    params: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Step:
    """One entry of the trajectory."""
    topic: int
    group: str
    reason: Reason
    missing: tuple[int, ...] = ()


def impact(*, topic: int, descendants: Mapping[int, Sequence[int]], flags: Mapping[int, bool]) -> int:
    """impact(v) = how many topics below v in G_L are still unmastered."""
    return sum(1 for node in descendants.get(topic, ()) if not flags.get(node, False))


def _unmastered_predecessors(
    topic: int,
    predecessors: Mapping[int, Sequence[int]],
    flags: Mapping[int, bool],
) -> tuple[int, ...]:
    return tuple(u for u in predecessors.get(topic, ()) if not flags.get(u, False))


def trajectory(
    *,
    order: Sequence[int],
    statuses: Mapping[int, str],
    flags: Mapping[int, bool],
    mastery: Mapping[int, float],
    descendants: Mapping[int, Sequence[int]],
    predecessors: Mapping[int, Sequence[int]],
) -> list[Step]:
    """
    Algorithm 2.5 over the topics of ``order`` (which is topological).

    Topics missing from ``statuses`` are treated as closed, which is what a
    learner who has never been given a state for them means. Mastered topics
    are left out: the list is what to do next.
    """
    position = {topic: index for index, topic in enumerate(order)}
    groups: dict[str, list[int]] = {group: [] for group in GROUPS}

    for topic in order:
        group = _GROUP_OF_STATUS.get(statuses.get(topic, CLOSED))
        if group is not None:
            groups[group].append(topic)

    steps: list[Step] = []

    # A — review: impact descending, then P(L) ascending, then topological.
    for topic in sorted(
        groups[GROUP_REVIEW],
        key=lambda t: (
            -impact(topic=t, descendants=descendants, flags=flags),
            mastery.get(t, 0.0),
            position.get(t, 0),
        ),
    ):
        steps.append(Step(
            topic=topic,
            group=GROUP_REVIEW,
            reason=Reason("review_impact", {
                "impact": impact(topic=topic, descendants=descendants, flags=flags),
                "p": mastery.get(topic, 0.0),
            }),
        ))

    # B — in_progress, topological.
    for topic in groups[GROUP_IN_PROGRESS]:
        steps.append(Step(
            topic=topic,
            group=GROUP_IN_PROGRESS,
            reason=Reason("in_progress", {"p": mastery.get(topic, 0.0)}),
        ))

    # C — open, topological.
    for topic in groups[GROUP_OPEN]:
        steps.append(Step(
            topic=topic,
            group=GROUP_OPEN,
            reason=Reason("ready", {"p": mastery.get(topic, 0.0)}),
        ))

    # D — closed, topological, with the predecessors that are in the way.
    for topic in groups[GROUP_CLOSED]:
        missing = _unmastered_predecessors(topic, predecessors, flags)
        steps.append(Step(
            topic=topic,
            group=GROUP_CLOSED,
            reason=Reason("blocked", {"missing": len(missing)}),
            missing=missing,
        ))

    return steps


def need(
    *,
    goal: int,
    statuses: Mapping[int, str],
    flags: Mapping[int, bool],
    predecessors: Mapping[int, Sequence[int]],
) -> frozenset[int]:
    """
    Need_s(g): the topics the learner must still master to reach ``goal``.

    Empty when ``goal`` is not closed — there is nothing in the way. The walk
    adds every unmastered u ∈ Pre(node) and continues through u only while u
    is itself closed; a mastered u is not needed at all, and an open one is
    needed but opens no further requirement.
    """
    if statuses.get(goal, CLOSED) != CLOSED:
        return frozenset()

    needed: set[int] = set()
    expanded: set[int] = {goal}
    frontier = [goal]
    while frontier:
        node = frontier.pop()
        for u in _unmastered_predecessors(node, predecessors, flags):
            needed.add(u)
            if statuses.get(u, CLOSED) == CLOSED and u not in expanded:
                expanded.add(u)
                frontier.append(u)
    return frozenset(needed)


def path_to(*, goal: int, needed: Iterable[int], order: Sequence[int]) -> tuple[int, ...]:
    """Need_s(g) in topological order, with ``goal`` last."""
    position = {topic: index for index, topic in enumerate(order)}
    ordered = sorted(needed, key=lambda t: (position.get(t, len(order)), t))
    return (*ordered, goal)
