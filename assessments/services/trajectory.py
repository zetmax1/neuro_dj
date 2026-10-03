"""
assessments/services/trajectory.py — the Django side of Algorithm 2.5 (3.5).

The trajectory is the one answer to "what should this learner do next". It
replaces the four independent heuristics the dashboard used to compute
(``recommended_next``, ``needs_revision``, ``ready_to_advance``,
``coming_soon``), each with its own idea of ordering and its own idea of what
"unlocked" meant.

Ordering is topological — the order of G_L — and never ``position``: what a
learner should do next follows the prerequisite graph, not the order the
instructor typed the topics in.

The arithmetic is in ``neuro_model.trajectory`` (rule 7). This module loads
the learner's states and the KB snapshot, calls it, and attaches the names the
API reports. Every item carries a structured reason (``{code, params}``); the
wording lives in the frontend's dictionary (D20).

Query budget: one readiness sync (one SELECT in the steady case) and one query
for the topic names, whatever the size of the course. A test holds it.
"""

from __future__ import annotations

from dataclasses import dataclass

from curriculum.models import Topic
from curriculum.services.graph import KBSnapshot, get_snapshot

from assessments.services import readiness
from neuro_model import trajectory as tr


class UnknownCourse(Exception):
    """The course id does not name an active course."""


class UnknownTopic(Exception):
    """The topic id does not name an active topic."""


@dataclass(frozen=True)
class Item:
    """One trajectory entry, ready to serialise."""
    topic_id: int
    name: str
    slug: str
    group: str
    status: str
    p_mastery: float
    accuracy: float
    reason_code: str
    reason_params: dict
    missing: tuple[dict, ...]

    def payload(self) -> dict:
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "slug": self.slug,
            "group": self.group,
            "status": self.status,
            "p_mastery": self.p_mastery,
            "accuracy": self.accuracy,
            "reason": {"code": self.reason_code, "params": self.reason_params},
            "missing": [dict(item) for item in self.missing],
        }


@dataclass(frozen=True)
class Path:
    """Need_s(g) and the route to it."""
    goal_id: int
    need: tuple[dict, ...]
    path: tuple[dict, ...]
    reachable: bool

    def payload(self) -> dict:
        return {
            "goal_id": self.goal_id,
            "need": [dict(item) for item in self.need],
            "path": [dict(item) for item in self.path],
            "reachable": self.reachable,
        }


# ---------------------------------------------------------------------------
# Shared loading
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Context:
    snapshot: KBSnapshot
    order: tuple[int, ...]
    statuses: dict[int, str]
    flags: dict[int, bool]
    mastery: dict[int, float]
    accuracy: dict[int, float]
    names: dict[int, tuple[str, str]]


def _load(*, user, topic_ids: set[int] | None, snapshot: KBSnapshot | None) -> _Context:
    snapshot = snapshot or get_snapshot()
    states = readiness.states_for(user=user, snapshot=snapshot)

    # ``order`` is already topological (Algorithm 2.2); restricting it keeps
    # that order, so a course view is a window on the same sequence.
    order = tuple(
        topic for topic in snapshot.order
        if topic_ids is None or topic in topic_ids
    )
    names = {
        pk: (name, slug)
        for pk, name, slug in Topic.objects.filter(pk__in=order).values_list("pk", "name", "slug")
    }
    return _Context(
        snapshot=snapshot,
        order=order,
        statuses={topic: state.status for topic, state in states.items()},
        flags={topic: state.mastered_flag for topic, state in states.items()},
        mastery={topic: state.p_mastery for topic, state in states.items()},
        accuracy={topic: state.accuracy for topic, state in states.items()},
        names=names,
    )


def _course_topics(course_id, snapshot: KBSnapshot) -> set[int]:
    try:
        course_id = int(course_id)
    except (TypeError, ValueError):
        raise UnknownCourse(f"Course {course_id!r} is not an id.") from None
    if course_id not in snapshot:
        raise UnknownCourse(f"Course {course_id} does not exist or is archived.")
    leaves = snapshot.leaves_of(course_id)
    if not leaves:
        raise UnknownCourse(f"Node {course_id} holds no topics.")
    return set(leaves)


def _missing_payload(ids, context: _Context) -> tuple[dict, ...]:
    """Unmastered predecessors, in programme order, with their P(L)."""
    ordered = context.snapshot.topics_in_programme_order(ids)
    return tuple(
        {
            "topic_id": topic,
            "name": context.names.get(topic, ("", ""))[0] or str(topic),
            "p_mastery": context.mastery.get(topic, 0.0),
        }
        for topic in ordered
    )


# ---------------------------------------------------------------------------
# Algorithm 2.5
# ---------------------------------------------------------------------------

def for_learner(*, user, course_id=None, snapshot: KBSnapshot | None = None) -> list[Item]:
    """
    The learner's trajectory, in the four groups of Algorithm 2.5.

    ``course_id`` restricts it to the topics of one course (Leaves of that
    node); without it the whole knowledge base is covered.
    """
    snapshot = snapshot or get_snapshot()
    topic_ids = _course_topics(course_id, snapshot) if course_id is not None else None
    context = _load(user=user, topic_ids=topic_ids, snapshot=snapshot)

    descendants = {
        topic: tuple(
            node for node in snapshot.descendants(topic)
            if topic_ids is None or node in topic_ids
        )
        for topic in context.order
    }
    predecessors = {
        topic: tuple(
            source for source in snapshot.pre.get(topic, ())
            if topic_ids is None or source in topic_ids
        )
        for topic in context.order
    }

    steps = tr.trajectory(
        order=context.order,
        statuses=context.statuses,
        flags=context.flags,
        mastery=context.mastery,
        descendants=descendants,
        predecessors=predecessors,
    )

    items: list[Item] = []
    for step in steps:
        name, slug = context.names.get(step.topic, (str(step.topic), ""))
        items.append(Item(
            topic_id=step.topic,
            name=name,
            slug=slug,
            group=step.group,
            status=context.statuses.get(step.topic, tr.CLOSED),
            p_mastery=context.mastery.get(step.topic, 0.0),
            accuracy=context.accuracy.get(step.topic, 0.0),
            reason_code=step.reason.code,
            reason_params=dict(step.reason.params),
            missing=_missing_payload(step.missing, context),
        ))
    return items


def next_step(*, user, course_id=None, snapshot: KBSnapshot | None = None) -> Item | None:
    """The head of the trajectory — what the dashboard shows as "next"."""
    items = for_learner(user=user, course_id=course_id, snapshot=snapshot)
    return items[0] if items else None


# ---------------------------------------------------------------------------
# Need_s(g) and the path
# ---------------------------------------------------------------------------

def path_to_topic(*, user, topic_id, snapshot: KBSnapshot | None = None) -> Path:
    """
    Need_s(g) and the route to ``topic_id``, both in topological order.

    ``reachable`` is False when the goal needs topics that are outside the
    knowledge base — which cannot happen for an active topic, so it is there
    to make the contract explicit rather than to be hit.
    """
    snapshot = snapshot or get_snapshot()
    try:
        goal = int(topic_id)
    except (TypeError, ValueError):
        raise UnknownTopic(f"Topic {topic_id!r} is not an id.") from None
    if goal not in snapshot.order:
        raise UnknownTopic(f"Topic {goal} is not an active topic.")

    context = _load(user=user, topic_ids=None, snapshot=snapshot)
    needed = tr.need(
        goal=goal,
        statuses=context.statuses,
        flags=context.flags,
        predecessors=snapshot.pre,
    )
    route = tr.path_to(goal=goal, needed=needed, order=context.order)

    def describe(topic: int) -> dict:
        name, slug = context.names.get(topic, (str(topic), ""))
        return {
            "topic_id": topic,
            "name": name,
            "slug": slug,
            "status": context.statuses.get(topic, tr.CLOSED),
            "p_mastery": context.mastery.get(topic, 0.0),
        }

    return Path(
        goal_id=goal,
        need=tuple(describe(topic) for topic in route[:-1]),
        path=tuple(describe(topic) for topic in route),
        reachable=all(topic in context.statuses for topic in route),
    )
