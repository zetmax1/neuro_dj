"""
Property-based tests of the KB service and the answer path on PostgreSQL
(stage 10, SN2, P1-9).

The pure counterpart is ``neuro_model/tests/test_properties.py``; this one
drives the real writers. Hypothesis builds a random course through
``curriculum.services.kb`` and then runs a random sequence of operations:
add, remove and re-weight a prerequisite, move, reorder, create and archive a
node, and answer a question through ``process_submission`` as one of two
learners. Every operation goes through the code production uses, and each is
either accepted or refused there (``KBError``, ``TopicClosed``, or the 400
path for an archived topic).

After every accepted operation, read back from the database:

- the tree is a forest of courses, topics are leaves and hold every question
  (Y1, Y4), and no relation joins a node and its ancestor (Y2);
- G_L recomputed with SQL (django-tree-queries' CTE for Leaves) equals the
  snapshot's, and has no cycle (Y3; an independent DFS);
- the Algorithm 2.2 order holds every active topic once and respects every edge;
- the KB version moved by exactly one for a KB change and not at all otherwise;
- counters: ``missing_count`` equals its recomputation from the M flags, for
  the rows stored under the current version before any resync (Algorithm 2.3,
  incremental) and for every row after ``states_for`` (TY6); attempts,
  correct, accuracy, θ's and b_q's answer counts equal the ledger's;
- every probability is in [0, 1] and θ within ±THETA_CLAMP;
- assertion 2.5 holds for every recorded answer;
- TY5: a started topic is never closed, and every status is the one the
  transition table gives.

A refused operation leaves every one of these rows exactly as it was.

Hypothesis runs it as a state machine: each example is one savepoint that is
rolled back, with the snapshot cache cleared (KB versions repeat between
examples). Deterministic: ``derandomize=True``, no example database on disk.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule, run_state_machine_as_test

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    Question,
    StudentTopicState,
    TopicStatus,
    UserAbility,
)
from assessments.services import readiness
from assessments.services.orchestrator import TopicClosed, process_submission
from assessments.services.student_model import OBSERVED_SOURCES
from curriculum.models import KnowledgeBaseVersion, Topic, TopicKind, TopicPrerequisite
from curriculum.services import kb
from curriculum.services.graph import build_snapshot, clear_local_cache, get_snapshot
from neuro_model import bkt
from neuro_model import readiness as r
from neuro_model.tests.test_properties import ROUNDING, STRICT_MARGIN, has_cycle

User = get_user_model()

QUESTIONS_PER_TOPIC = 3
THETA_CLAMP = 4.0

PICK = st.integers(min_value=0, max_value=10_000)
# Weights include invalid ones: ω ∉ (0, 1] must be refused without a trace.
WEIGHTS = st.sampled_from((0.25, 0.5, 1.0, 0.0, 1.5))
# Simulated answers are never downgraded to review_repeat (D25 applies to
# adaptive ones), so they are the ones that move a topic to τ and back.
SOURCES = st.sampled_from((AttemptSource.ADAPTIVE, AttemptSource.SIMULATED, AttemptSource.SIMULATED))
CORRECTNESS = st.integers(0, 3).map(bool)  # three in four correct

KB_CHANGES = st.one_of(
    st.tuples(st.just("add"), PICK, PICK, WEIGHTS),
    st.tuples(st.just("remove"), PICK),
    st.tuples(st.just("weight"), PICK, WEIGHTS),
    st.tuples(st.just("move"), PICK, PICK),
    st.tuples(st.just("reorder"), PICK, st.sampled_from(kb.SIBLING_DIRECTIONS)),
    st.tuples(st.just("create"), PICK, st.sampled_from((TopicKind.TOPIC, TopicKind.SECTION))),
    st.tuples(st.just("archive"), PICK),
)
# A run of answers by one learner on one topic: mixed, or a streak of one kind
# long enough to cross τ (or fall below τ − δ).
# ``via_menu``: the learner picks among the topics the interface offers (not
# closed), as the UI does; otherwise any topic, as a direct API call may.
ANSWER_RUNS = st.tuples(
    st.just("answer"), st.integers(0, 1), PICK, SOURCES, st.integers(0, 3).map(bool),
    st.one_of(
        st.lists(st.tuples(PICK, CORRECTNESS), min_size=1, max_size=6),
        st.tuples(st.booleans(), st.integers(1, 10)).map(
            lambda run: [(i, run[0]) for i in range(run[1])]
        ),
    ),
)
KB_OPERATIONS = frozenset({"add", "remove", "weight", "move", "reorder", "create", "archive"})

PROPERTY_SETTINGS = settings(
    max_examples=40,
    stateful_step_count=20,
    derandomize=True,
    database=None,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@st.composite
def courses(draw):
    """A random forest (parent indices), and topic-to-topic relations to try."""
    n = draw(st.integers(min_value=2, max_value=8))
    parents: list[int | None] = [None]
    for node in range(1, n):
        choice = draw(st.integers(-1, node - 1))  # -1: a new course
        parents.append(None if choice < 0 else choice)
    relations = draw(st.lists(st.tuples(PICK, PICK, WEIGHTS), max_size=8))
    return parents, relations


class World:
    """The database under test, with the handful of helpers the operations need."""

    def __init__(self) -> None:
        self._slugs = count(1)
        self.learners = [
            User.objects.create_user(email=f"kb-prop-{i}@example.org", password=None, is_simulated=True)
            for i in range(2)
        ]

    # --- building ---------------------------------------------------------
    def build(self, parents) -> None:
        has_children = {p for p in parents if p is not None}
        made: list[Topic] = []
        for index, parent in enumerate(parents):
            kind = (
                TopicKind.COURSE if parent is None
                else TopicKind.SECTION if index in has_children
                else TopicKind.TOPIC
            )
            made.append(self.create(None if parent is None else made[parent].pk, kind))

    def create(self, parent_id: int | None, kind: str) -> Topic:
        n = next(self._slugs)
        node = kb.create_node(name=f"node {n}", slug=f"kb-prop-{n}", parent=parent_id, kind=kind)
        if kind == TopicKind.TOPIC:
            for q in range(QUESTIONS_PER_TOPIC):
                question = Question.objects.create(topic=node, text=f"{node.slug} q{q}", irt_difficulty=0.0)
                Choice.objects.create(question=question, text="right", is_correct=True)
                Choice.objects.create(question=question, text="wrong", is_correct=False)
        return node

    # --- picking ----------------------------------------------------------
    @staticmethod
    def node(pick: int) -> int:
        """Any node, archived ones included: those must be refused."""
        nodes = list(Topic.objects.order_by("pk").values_list("pk", flat=True))
        return nodes[pick % len(nodes)]

    @staticmethod
    def topic(pick: int) -> int | None:
        topics = list(Topic.objects.filter(kind=TopicKind.TOPIC).order_by("pk").values_list("pk", flat=True))
        return topics[pick % len(topics)] if topics else None

    @staticmethod
    def relation(pick: int) -> int | None:
        rels = list(TopicPrerequisite.objects.order_by("pk").values_list("pk", flat=True))
        return rels[pick % len(rels)] if rels else None

    # --- the state a refusal must not touch --------------------------------
    @staticmethod
    def fingerprint():
        return (
            KnowledgeBaseVersion.current(),
            list(Topic.objects.order_by("pk").values_list(
                "pk", "parent_id", "kind", "position", "is_archived", "slug",
            )),
            list(TopicPrerequisite.objects.order_by("pk").values_list(
                "pk", "prerequisite_id", "topic_id", "weight",
            )),
            list(StudentTopicState.objects.order_by("pk").values_list(
                "pk", "p_mastery", "mastered_flag", "status", "missing_count",
                "started_at", "kb_version", "attempts", "correct", "accuracy",
            )),
            list(AssessmentAttempt.objects.order_by("pk").values_list("pk", flat=True)),
            list(UserAbility.objects.order_by("pk").values_list("pk", "theta", "n_answers")),
            list(Question.objects.order_by("pk").values_list("pk", "irt_difficulty", "n_answers")),
        )

    def attempt(self, operation, *, kb_change: bool) -> bool:
        """Run one operation; a refusal must leave the fingerprint unchanged."""
        before = self.fingerprint()
        try:
            operation()
        except (kb.KBError, TopicClosed, Choice.DoesNotExist):
            assert self.fingerprint() == before, "a refused operation changed the database"
            return False
        moved = KnowledgeBaseVersion.current() - before[0]
        assert moved == (1 if kb_change else 0), f"the KB version moved by {moved}"
        return True

    # --- operations -------------------------------------------------------
    def apply(self, op) -> None:
        name = op[0]
        if name == "answer":
            _, who, topic_pick, source, via_menu, run = op
            learner = self.learners[who]
            if via_menu:
                offered = sorted(
                    t for t, s in readiness.states_for(user=learner).items() if not s.is_closed
                )
                topic_id = offered[topic_pick % len(offered)] if offered else None
            else:
                topic_id = self.topic(topic_pick)
            if topic_id is None:
                return
            questions = list(Question.objects.filter(topic_id=topic_id).order_by("pk"))
            for question_pick, is_correct in run:
                question = questions[question_pick % len(questions)]
                choice = question.choices.get(is_correct=is_correct)
                accepted = self.attempt(lambda: process_submission(
                    user=learner, question_id=question.pk,
                    choice_id=choice.pk, source=source,
                ), kb_change=False)
                if not accepted:
                    return
                self.check()
            return

        if name == "add":
            _, x_pick, y_pick, weight = op
            x, y = self.node(x_pick), self.node(y_pick)
            operation = lambda: kb.add_prerequisite(prerequisite=x, topic=y, weight=weight)  # noqa: E731
        elif name == "remove":
            rel = self.relation(op[1])
            if rel is None:
                return
            operation = lambda: kb.remove_prerequisite(rel)  # noqa: E731
        elif name == "weight":
            rel = self.relation(op[1])
            if rel is None:
                return
            operation = lambda: kb.update_weight(rel, op[2])  # noqa: E731
        elif name == "move":
            node, parent = self.node(op[1]), self.node(op[2])
            operation = lambda: kb.move_node(node, parent)  # noqa: E731
        elif name == "reorder":
            node = self.node(op[1])
            operation = lambda: kb.reorder_sibling(node, direction=op[2])  # noqa: E731
        elif name == "create":
            parent = self.node(op[1])
            operation = lambda: self.create(parent, op[2])  # noqa: E731
        elif name == "archive":
            node = self.node(op[1])
            operation = lambda: kb.archive_node(node)  # noqa: E731
        else:  # pragma: no cover - the strategy has no other names
            raise AssertionError(name)
        if self.attempt(operation, kb_change=name in KB_OPERATIONS):
            self.check()

    # --- invariants -------------------------------------------------------
    def check(self) -> None:
        snapshot = build_snapshot()  # raises CycleError if G_L had a cycle
        self.check_knowledge_base(snapshot)
        for learner in self.learners:
            self.check_learner(learner, snapshot)
        self.check_ledger()

    @staticmethod
    def check_knowledge_base(snapshot) -> None:
        rows = {
            pk: (parent, kind, archived)
            for pk, parent, kind, archived in Topic.objects.values_list("pk", "parent_id", "kind", "is_archived")
        }

        def ancestors(pk):
            chain, current = [], rows[pk][0]
            while current is not None:
                assert current not in chain and current != pk, "Y1: a parent loop"
                chain.append(current)
                current = rows[current][0]
            return chain

        active = {pk for pk in rows if not rows[pk][2] and not any(rows[a][2] for a in ancestors(pk))}
        topics = {pk for pk in active if rows[pk][1] == TopicKind.TOPIC}

        # Y1 and the kinds of 3.1; Y4: questions live on topics only.
        for pk in active:
            parent, kind, _ = rows[pk]
            assert (kind == TopicKind.COURSE) == (parent is None)
            if parent is not None:
                assert rows[parent][1] != TopicKind.TOPIC, "a topic has a child"
        assert not Question.objects.exclude(topic__kind=TopicKind.TOPIC).exists(), "Y4"

        # G_L from the database: Leaves by the tree-queries CTE, not neuro_model.
        def leaves(pk):
            subtree = Topic.objects.descendants(pk, include_self=True).values_list("pk", flat=True)
            return {n for n in subtree if n in topics}

        weights: dict[tuple[int, int], float] = {}
        for x, y, w in TopicPrerequisite.objects.values_list("prerequisite_id", "topic_id", "weight"):
            if x not in active or y not in active:
                continue
            assert x not in ancestors(y) and y not in ancestors(x) and x != y, "Y2"
            for a in leaves(x):
                for b in leaves(y):
                    if a != b:
                        weights[(a, b)] = max(weights.get((a, b), 0.0), w)
        assert {e: le.weight for e, le in snapshot.edges.items()} == weights

        # Y3 and Algorithm 2.2.
        assert not has_cycle(sorted(topics), weights)
        assert sorted(snapshot.order) == sorted(topics)
        rank = {t: i for i, t in enumerate(snapshot.order)}
        assert all(rank[a] < rank[b] for a, b in weights)

    @staticmethod
    def check_learner(learner, snapshot) -> None:
        pre = {t: snapshot.pre.get(t, ()) for t in snapshot.topics}

        def recomputed(states):
            return r.recompute_counters(
                predecessors=pre, flags={t: s.mastered_flag for t, s in states.items()},
            )

        # Rows the incremental Algorithm 2.3 maintained, before any resync.
        current = {
            s.topic_id: s for s in StudentTopicState.objects.filter(
                user=learner, topic_id__in=pre, kb_version=snapshot.version,
            )
        }
        if len(current) == len(pre):
            expected = recomputed(current)
            assert {t: s.missing_count for t, s in current.items()} == expected

        # Every row, after the read path's TY6 resync.
        states = readiness.states_for(user=learner, snapshot=get_snapshot())
        assert set(states) == set(pre)
        expected = recomputed(states)
        counted = defaultdict(list)
        for topic_id, is_correct, p_after in (
            AssessmentAttempt.objects.filter(user=learner, source__in=OBSERVED_SOURCES)
            .order_by("attempt_no").values_list("topic_id", "is_correct", "p_after")
        ):
            counted[topic_id].append((is_correct, p_after))

        for topic_id, state in states.items():
            assert state.missing_count == expected[topic_id]
            assert 0.0 <= state.p_mastery <= 1.0 and 0.0 <= state.accuracy <= 1.0
            rows = counted.get(topic_id, [])
            assert state.attempts == len(rows)
            assert state.correct == sum(1 for ok, _ in rows if ok)
            assert state.accuracy == pytest.approx(state.correct / state.attempts if rows else 0.0)
            assert state.p_mastery == (rows[-1][1] if rows else 0.0)
            if state.started_at is not None:
                assert state.status != TopicStatus.CLOSED, "TY5: a started topic was closed"
                if state.mastered_flag:
                    assert state.status == TopicStatus.MASTERED
                else:
                    assert state.status in (TopicStatus.IN_PROGRESS, TopicStatus.REVIEW)
            else:
                assert state.attempts == 0
                assert state.status == (
                    TopicStatus.OPEN if state.missing_count == 0 else TopicStatus.CLOSED
                )

    @staticmethod
    def check_ledger() -> None:
        observed = AssessmentAttempt.objects.filter(source__in=OBSERVED_SOURCES)
        for row in observed:
            values = (row.p_before, row.p_hat, row.p_after, row.guess_used, row.slip_used)
            assert all(0.0 <= v <= 1.0 for v in values)
            assert abs(row.theta_after) <= THETA_CLAMP
            assert row.guess_used + row.slip_used < 1.0
            assert row.p_hat == pytest.approx(
                bkt.predict(p_l=row.p_before, guess=row.guess_used, slip=row.slip_used), abs=1e-12,
            )
            # Assertion 2.5 on the posterior of this very answer.
            post = bkt.posterior(
                p_l=row.p_before, guess=row.guess_used, slip=row.slip_used, is_correct=row.is_correct,
            )
            p = row.p_before
            assert post >= p - ROUNDING if row.is_correct else post <= p + ROUNDING
            if STRICT_MARGIN < p < 1.0 - STRICT_MARGIN:
                assert post > p if row.is_correct else post < p
        repeats = AssessmentAttempt.objects.filter(source=AttemptSource.REVIEW_REPEAT)
        assert not repeats.filter(p_after__isnull=False).exists(), "a review_repeat moved P(L)"

        per_course = defaultdict(int)
        per_question = defaultdict(int)
        for user_id, course_id, question_id in observed.values_list("user_id", "course_id", "question_id"):
            per_course[(user_id, course_id)] += 1
            per_question[question_id] += 1
        abilities = {
            (a.user_id, a.course_id): a for a in UserAbility.objects.all()
        }
        assert {k: a.n_answers for k, a in abilities.items()} == dict(per_course)
        assert all(abs(a.theta) <= THETA_CLAMP for a in abilities.values())
        for question_id, n_answers in Question.objects.values_list("pk", "n_answers"):
            assert n_answers == per_question.get(question_id, 0)


class KnowledgeBaseService(RuleBasedStateMachine):
    """
    One example = one savepoint that never commits, with the snapshot cache
    emptied on both sides (KB versions repeat between examples).
    """

    def __init__(self) -> None:
        super().__init__()
        cache.clear()
        clear_local_cache()
        self.savepoint = transaction.atomic()
        self.savepoint.__enter__()
        self.world = World()

    @initialize(course=courses())
    def build(self, course):
        parents, relations = course
        world = self.world
        world.build(parents)
        world.check()
        for x_pick, y_pick, weight in relations:
            x, y = world.topic(x_pick), world.topic(y_pick)
            if x is None:
                break
            if world.attempt(
                lambda: kb.add_prerequisite(prerequisite=x, topic=y, weight=weight), kb_change=True,
            ):
                world.check()

    @rule(op=KB_CHANGES)
    def change_the_knowledge_base(self, op):
        self.world.apply(op)

    # Answers are the bulk of real traffic, so two rules of three are answers.
    @rule(op=ANSWER_RUNS)
    def answer(self, op):
        self.world.apply(op)

    @rule(op=ANSWER_RUNS)
    def answer_again(self, op):
        self.world.apply(op)

    def teardown(self):
        transaction.set_rollback(True)
        self.savepoint.__exit__(None, None, None)
        cache.clear()
        clear_local_cache()


@pytest.mark.django_db
def test_kb_service_and_answer_path_keep_every_invariant():
    run_state_machine_as_test(KnowledgeBaseService, settings=PROPERTY_SETTINGS)
