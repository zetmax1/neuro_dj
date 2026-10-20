"""
assessments/services/readiness.py — the one readiness service (TY1–TY6).

It replaces the four implementations stage 4 removes: the global
``Topic.is_unlocked`` flag with its parent-to-children cascade,
``curriculum.services.graph.is_unlocked_dag`` with its parent fallback, the
per-request check inside the graph view, and the unlock the test-session
endpoint performed. There is now exactly one place that decides whether a
learner may answer a topic.

Responsibilities (3.4):

- the initial state of a new learner: ``missing_count`` = |Pre(w)| and the
  status that follows from it;
- Algorithm 2.3 on every answer, incrementally;
- TY5 — a started topic never returns to closed, enforced here and by a
  database constraint on ``StudentTopicState``;
- TY6 — a state computed under an older KB version is not trusted: the
  counters are recomputed from the M flags in O(n + m).

Inheritance runs through G_L only. A topic is not open because its parent is
mastered; it is open because every u ∈ Pre(w) is mastered, where Pre comes
from the knowledge-base snapshot's inherited graph.

The arithmetic is in ``neuro_model.readiness`` (rule 7); this module loads
rows, calls it and stores the result.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from curriculum.models import Topic
from curriculum.services.graph import KBSnapshot, get_snapshot

from assessments.models import StudentTopicState, TopicStatus
from neuro_model import readiness as r


def thresholds() -> tuple[float, float]:
    """τ and δ from the one source of truth."""
    values = settings.THESIS_MODEL
    return values["TAU"], values["DELTA"]


# ---------------------------------------------------------------------------
# Loading state
# ---------------------------------------------------------------------------

def _defaults_for(topic_id: int, snapshot: KBSnapshot, version: int) -> dict:
    missing = len(snapshot.pre.get(topic_id, ()))
    return {
        "p_mastery": 0.0,
        "mastered_flag": False,
        "status": TopicStatus.OPEN if missing == 0 else TopicStatus.CLOSED,
        "missing_count": missing,
        "started_at": None,
        "kb_version": version,
        "attempts": 0,
        "correct": 0,
        "accuracy": 0.0,
    }


def states_for(*, user, snapshot: KBSnapshot | None = None) -> dict[int, StudentTopicState]:
    """
    Every topic state of this learner, keyed by topic id.

    Rows that do not exist yet are created with the initial state, and a state
    stored under an older KB version has its counters recomputed (TY6). In the
    steady case this is a single SELECT and no write.
    """
    snapshot = snapshot or get_snapshot()
    topic_ids = set(snapshot.topics)
    states = {
        state.topic_id: state
        for state in StudentTopicState.objects.filter(user=user, topic_id__in=topic_ids)
    }

    missing_rows = topic_ids - states.keys()
    if missing_rows:
        StudentTopicState.objects.bulk_create(
            [
                StudentTopicState(
                    user=user, topic_id=topic_id,
                    **_defaults_for(topic_id, snapshot, snapshot.version),
                )
                for topic_id in sorted(missing_rows)
            ],
            ignore_conflicts=True,
        )
        states = {
            state.topic_id: state
            for state in StudentTopicState.objects.filter(user=user, topic_id__in=topic_ids)
        }

    if any(state.kb_version != snapshot.version for state in states.values()):
        states = resync(user=user, snapshot=snapshot, states=states)
    return states


def resync(
    *,
    user,
    snapshot: KBSnapshot,
    states: dict[int, StudentTopicState] | None = None,
) -> dict[int, StudentTopicState]:
    """
    TY6: recompute every counter from the M flags and re-derive the statuses.

    Called when the knowledge base moved under a stored state — a new
    prerequisite can close an unstarted topic and a removed one can open it.
    O(n + m) in the size of G_L.
    """
    if states is None:
        states = {
            state.topic_id: state
            for state in StudentTopicState.objects.filter(
                user=user, topic_id__in=set(snapshot.topics),
            )
        }

    flags = {topic_id: state.mastered_flag for topic_id, state in states.items()}
    counters = r.recompute_counters(
        predecessors={topic: snapshot.pre.get(topic, ()) for topic in snapshot.topics},
        flags=flags,
    )

    changed: list[StudentTopicState] = []
    for topic_id, state in states.items():
        missing = counters.get(topic_id, 0)
        status = r.next_status(
            current=state.status,
            mastered=state.mastered_flag,
            started=state.started_at is not None,
            missing=missing,
        )
        if (state.missing_count, state.status, state.kb_version) != (
            missing, status, snapshot.version,
        ):
            state.missing_count = missing
            state.status = status
            state.kb_version = snapshot.version
            changed.append(state)

    if changed:
        StudentTopicState.objects.bulk_update(
            changed, ["missing_count", "status", "kb_version"],
        )
    return states


# ---------------------------------------------------------------------------
# Can this learner answer this topic?
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Blocked:
    """Why a topic cannot be answered, in the shape the 403 body needs."""
    topic_id: int
    missing: tuple[dict, ...]

    def payload(self) -> dict:
        return {"missing": [dict(item) for item in self.missing]}


def check_open(
    *,
    user,
    topic_id: int,
    snapshot: KBSnapshot | None = None,
    states: dict[int, StudentTopicState] | None = None,
) -> Blocked | None:
    """
    None when the learner may answer this topic, otherwise the unmet
    prerequisites. A started topic is always answerable (TY5).

    ``states`` lets a caller that has just loaded them with ``states_for``
    (under the same snapshot) pass them in instead of reading them again.
    """
    snapshot = snapshot or get_snapshot()
    if states is None:
        states = states_for(user=user, snapshot=snapshot)
    state = states.get(topic_id)
    if state is None or state.is_started or not state.is_closed:
        return None
    return Blocked(topic_id=topic_id, missing=missing_prerequisites(
        topic_id=topic_id, states=states, snapshot=snapshot,
    ))


def missing_prerequisites(
    *,
    topic_id: int,
    states: dict[int, StudentTopicState],
    snapshot: KBSnapshot,
) -> tuple[dict, ...]:
    """The unmastered members of Pre(w), in programme order, with their P(L)."""
    unmet = [
        source for source in snapshot.pre.get(topic_id, ())
        if not (states[source].mastered_flag if source in states else False)
    ]
    names = dict(
        Topic.objects.filter(pk__in=unmet).values_list("pk", "name")
    )
    ordered = snapshot.topics_in_programme_order(unmet)
    return tuple(
        {
            "topic_id": source,
            "name": names.get(source, str(source)),
            "p_mastery": states[source].p_mastery if source in states else 0.0,
        }
        for source in ordered
    )


# ---------------------------------------------------------------------------
# Readiness at answer time
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReadinessAtAnswer:
    """r_s(w) and R_s(w) as they stood when the question was answered."""
    score: float
    was_ready: bool


def readiness_at(
    *,
    topic_id: int,
    states: dict[int, StudentTopicState],
    snapshot: KBSnapshot,
) -> ReadinessAtAnswer:
    """r_s(w) = min P(L) over Pre(w) and R_s(w); both 1/True for Pre = ∅."""
    pre = snapshot.pre.get(topic_id, ())
    mastery = [states[u].p_mastery if u in states else 0.0 for u in pre]
    flags = [states[u].mastered_flag if u in states else False for u in pre]
    return ReadinessAtAnswer(
        score=r.readiness_score(mastery),
        was_ready=r.is_ready(flags),
    )


# ---------------------------------------------------------------------------
# Algorithm 2.3
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Applied:
    """The answered topic's new state and what the propagation changed."""
    state: StudentTopicState
    opened: tuple[int, ...]
    closed: tuple[int, ...]
    flag_changed: bool


def apply_answer(
    *,
    user,
    topic_id: int,
    p_mastery: float,
    is_correct: bool,
    snapshot: KBSnapshot | None = None,
    answered_at=None,
    states: dict[int, StudentTopicState] | None = None,
) -> Applied:
    """
    Algorithm 2.3 after one answer.

    1. M is recomputed for the answered topic;
    2. if M did not change, only that topic's own row moves;
    3. otherwise every w ∈ Succ(v) has its counter adjusted by one;
    4. a successor whose counter reaches 0 while closed opens;
    5. a topic that stops being mastered becomes ``review``.

    Must run inside the caller's transaction. The answered topic's row is
    locked here; the successors are updated in one bulk write.

    ``states`` lets a caller that already holds the learner's states pass them
    in — a test session applies many answers in a row and must not re-read
    them once per answer. The dict is updated in place.
    """
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("apply_answer must run inside transaction.atomic().")

    snapshot = snapshot or get_snapshot()
    tau, delta = thresholds()
    if states is None:
        states = states_for(user=user, snapshot=snapshot)

    state = StudentTopicState.objects.select_for_update().get(user=user, topic_id=topic_id)
    previous_flag = state.mastered_flag
    new_flag = r.mastered_flag(
        p_mastery=p_mastery, tau=tau, delta=delta, previous=previous_flag,
    )

    state.p_mastery = p_mastery
    state.mastered_flag = new_flag
    state.attempts += 1
    if is_correct:
        state.correct += 1
    state.accuracy = state.correct / state.attempts
    if state.started_at is None:
        state.started_at = answered_at or timezone.now()
    state.status = r.next_status(
        current=state.status,
        mastered=new_flag,
        started=True,  # this answer started it, if nothing else did
        missing=state.missing_count,
    )
    state.kb_version = snapshot.version
    state.save(update_fields=[
        "p_mastery", "mastered_flag", "status", "attempts", "correct",
        "accuracy", "started_at", "kb_version", "updated_at",
    ])
    states[topic_id] = state

    if new_flag == previous_flag:
        # Step 2: nothing downstream can have changed.
        return Applied(state=state, opened=(), closed=(), flag_changed=False)

    propagation = r.propagate(
        became_mastered=new_flag,
        successors=snapshot.succ.get(topic_id, ()),
        counters={t: s.missing_count for t, s in states.items()},
        statuses={t: s.status for t, s in states.items()},
    )

    touched: list[StudentTopicState] = []
    for successor, missing in propagation.counters.items():
        successor_state = states[successor]
        successor_state.missing_count = missing
        successor_state.status = r.next_status(
            current=successor_state.status,
            mastered=successor_state.mastered_flag,
            started=successor_state.started_at is not None,
            missing=missing,
        )
        successor_state.kb_version = snapshot.version
        touched.append(successor_state)

    if touched:
        StudentTopicState.objects.bulk_update(
            touched, ["missing_count", "status", "kb_version"],
        )

    return Applied(
        state=state,
        opened=propagation.opened,
        closed=propagation.closed,
        flag_changed=True,
    )
