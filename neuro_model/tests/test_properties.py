"""
Property-based tests of the pure model (stage 10, SN2, P1-9).

Hypothesis builds a random forest and then runs a random sequence of the
operations the platform performs on it: add or remove a prerequisite, move a
node, reorder it, add a topic or a section, and answer a question. Each one
is accepted or refused by ``neuro_model`` itself — Y1–Y3 through
``is_nested``, ``find_cycle_chain`` (Algorithm 2.1) and
``topological_order`` (Algorithm 2.2), TY1–TY4 through the learner's status —
exactly as the KB service and the answer path decide.

After every accepted operation:

- G_L has no cycle (an independent DFS, not Algorithm 2.2 checking itself),
  and neither has the node graph G = (N, E_P) (D70);
- the Algorithm 2.2 order holds every topic once and respects every edge;
- the counters Algorithm 2.3 keeps incrementally equal ``recompute_counters``;
- every probability is in [0, 1];
- assertion 2.5 holds for the answer just processed;
- TY5: a started topic is never closed, and every status is the one the
  transition table gives.

A refused operation leaves the state exactly as it was. The functions are
handed the machine's own mappings, so one that mutated its input while
refusing would be caught.

Deterministic: ``derandomize=True`` and no example database on disk. The
Django-side counterpart is ``curriculum/tests/test_kb_properties.py``.
"""

from __future__ import annotations

import copy
from collections import defaultdict
from dataclasses import dataclass

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, precondition, rule

from neuro_model import bkt
from neuro_model import graph as g
from neuro_model import readiness as r
from neuro_model import student as s
from neuro_model.init import Prerequisite as PriorInput

# The constants of D6 (config.settings.THESIS_MODEL); they are not varied here.
CONSTANTS = s.Constants(
    g_max=0.30, s_max=0.10, a_q=1.0,
    elo_alpha=0.8, elo_beta=0.05,
    lam=0.5, tau=0.95, c_offset=0.05, theta_clamp=4.0,
)
DELTA = 0.10

# Assertion 2.5 is strict on the open interval 0 < P(L) < 1. At the ends the
# posterior is a fixed point, and next to them a double cannot resolve the
# change, so the strict form is checked away from 0 and 1 and the weak form
# (up to rounding) everywhere.
STRICT_MARGIN = 1e-9
ROUNDING = 1e-12

PICK = st.integers(min_value=0, max_value=10_000)
WEIGHTS = st.sampled_from((0.25, 0.5, 0.75, 1.0))
# Three answers in four are correct, and some runs are long streaks of one
# kind, so topics reach τ and fall back below τ − δ often enough for
# Algorithm 2.3 to open and close successors, not only to count.
CORRECTNESS = st.integers(0, 3).map(bool)
ANSWER_RUNS = st.one_of(
    st.lists(CORRECTNESS, min_size=1, max_size=8),
    st.tuples(st.booleans(), st.integers(1, 15)).map(lambda run: [run[0]] * run[1]),
)
TOPIC_PARAMS = st.builds(
    s.TopicParams,
    p0=st.floats(0.01, 0.9),
    pt=st.floats(0.0, 0.5),
    g0=st.floats(0.01, 0.29),   # G0 < G_MAX
    s0=st.floats(0.005, 0.095),  # S0 < S_MAX
)

PROPERTY_SETTINGS = settings(
    max_examples=200,
    stateful_step_count=50,
    derandomize=True,
    database=None,
    deadline=None,
)


@st.composite
def forests(draw):
    """A random ordered forest; kinds follow 3.1 (course = root, topic = leaf)."""
    n = draw(st.integers(min_value=2, max_value=10))
    parent: dict[int, int | None] = {0: None}
    for node in range(1, n):
        choice = draw(st.integers(-1, node - 1))  # -1: a new root (course)
        parent[node] = None if choice < 0 else choice
    has_children = {p for p in parent.values() if p is not None}
    kind = {
        node: g.COURSE if parent[node] is None else (g.SECTION if node in has_children else g.TOPIC)
        for node in parent
    }
    position = {node: draw(st.integers(0, 3)) for node in parent}
    return parent, kind, position


def has_cycle(topics, edges) -> bool:
    """Iterative three-colour DFS; independent of Algorithm 2.2."""
    succ = defaultdict(list)
    for a, b in edges:
        succ[a].append(b)
    colour = dict.fromkeys(topics, 0)  # 0 unseen, 1 on the stack, 2 done
    for start in topics:
        if colour[start]:
            continue
        colour[start] = 1
        stack = [(start, iter(succ[start]))]
        while stack:
            node, rest = stack[-1]
            for nxt in rest:
                if colour[nxt] == 1:
                    return True
                if colour[nxt] == 0:
                    colour[nxt] = 1
                    stack.append((nxt, iter(succ[nxt])))
                    break
            else:
                colour[node] = 2
                stack.pop()
    return False


@dataclass
class TopicState:
    """One learner's row for one topic, as ``StudentTopicState`` keeps it."""
    p_l: float | None
    flag: bool
    status: str
    counter: int
    attempts: int = 0


class Refused(Exception):
    """The operation was refused; the state must be untouched."""


class KnowledgeBaseMachine(RuleBasedStateMachine):

    # ------------------------------------------------------------------
    # Setup and derived quantities
    # ------------------------------------------------------------------

    @initialize(
        forest=forests(),
        params=st.lists(TOPIC_PARAMS, min_size=10, max_size=10),
        relations=st.lists(st.tuples(PICK, PICK, WEIGHTS), max_size=12),
    )
    def build(self, forest, params, relations):
        self.parent, self.kind, self.position = forest
        self.rels: list[g.Prerequisite] = []
        self.next_rel = 1
        self.params = {t: params[t % len(params)] for t in self.topics()}
        self.b = dict.fromkeys(self.topics(), 0.0)      # one item per topic
        self.n_question = dict.fromkeys(self.topics(), 0)
        self.theta = 0.0
        self.n_student = 0
        self.learner: dict[int, TopicState] = {}
        self.last: tuple[s.StepResult, bool] | None = None
        self.resync()
        # Topic-to-topic relations, the common case in a real course, through
        # the same accept/refuse path as the rule below; without them G_L is
        # mostly empty and Algorithm 2.3 has nothing to propagate along.
        topics = self.topics()
        for x_pick, y_pick, weight in relations if topics else ():
            self.add(topics[x_pick % len(topics)], topics[y_pick % len(topics)], weight)
            self.verify_invariants()

    def topics(self) -> list[int]:
        return sorted(n for n, k in self.kind.items() if k == g.TOPIC)

    def tree(self) -> g.Tree:
        # The machine's own mappings, not copies: a function that mutated its
        # input would show up in ``fingerprint``.
        return g.Tree(parent=self.parent, kind=self.kind, position=self.position)

    def graph(self):
        tree = self.tree()
        leaf_sets = g.leaves(tree)
        edges = g.expand(self.rels, leaf_sets)
        pos = g.preorder_positions(tree)
        order, _lev = g.topological_order(self.topics(), edges, pos)
        pre: dict[int, list[int]] = {t: [] for t in order}
        for a, b in edges:
            pre[b].append(a)
        return leaf_sets, edges, order, pre, g.successors(order, edges)

    def fingerprint(self):
        return copy.deepcopy((
            self.parent, self.kind, self.position, self.rels, self.next_rel,
            self.params, self.b, self.n_question, self.theta, self.n_student,
            self.learner,
        ))

    def resync(self) -> None:
        """TY6 after a KB change: counters from the M flags, statuses re-derived."""
        _, _, order, pre, _ = self.graph()
        self.learner = {t: st_ for t, st_ in self.learner.items() if t in pre}
        for t in order:
            if t not in self.learner:
                missing = len(pre[t])
                self.learner[t] = TopicState(
                    p_l=None, flag=False, counter=missing,
                    status=r.OPEN if missing == 0 else r.CLOSED,
                )
        counters = r.recompute_counters(
            predecessors=pre, flags={t: st_.flag for t, st_ in self.learner.items()},
        )
        for t, st_ in self.learner.items():
            st_.counter = counters[t]
            st_.status = r.next_status(
                current=st_.status, mastered=st_.flag,
                started=st_.attempts > 0, missing=st_.counter,
            )

    def attempt(self, operation) -> bool:
        """Run ``operation``; on refusal assert nothing moved. True if accepted."""
        before = self.fingerprint()
        try:
            operation()
        except Refused:
            assert self.fingerprint() == before, "a refused operation changed the state"
            return False
        return True

    # ------------------------------------------------------------------
    # Knowledge-base operations (the KB service's decisions)
    # ------------------------------------------------------------------

    @rule(x_pick=PICK, y_pick=PICK, weight=WEIGHTS)
    def add_prerequisite(self, x_pick, y_pick, weight):
        nodes = sorted(self.parent)
        self.add(nodes[x_pick % len(nodes)], nodes[y_pick % len(nodes)], weight)

    def add(self, x: int, y: int, weight: float) -> None:
        def run():
            tree = self.tree()
            if g.is_nested(tree, x, y):  # self and Y2
                raise Refused
            if any((rel.source, rel.target) == (x, y) for rel in self.rels):
                raise Refused
            leaf_sets = g.leaves(tree)
            chain = g.find_cycle_chain(tree, self.rels, leaf_sets, x, y)
            candidate = [*self.rels, g.Prerequisite(self.next_rel, x, y, weight)]
            closes = has_cycle(self.topics(), g.expand(candidate, leaf_sets))
            assert (chain is not None) == closes, "Algorithm 2.1 disagrees with G_L"
            if chain is not None:
                raise Refused
            # D70: a cycle in G = (N, E_P) through a node with no topic.
            node_chain = g.find_node_cycle_chain(self.rels, x, y)
            nodes = sorted(self.parent)
            closes_g = has_cycle(nodes, [(p.source, p.target) for p in candidate])
            assert (node_chain is not None) == closes_g, "D70's check disagrees with G"
            if node_chain is not None:
                raise Refused
            self.rels = candidate
            self.next_rel += 1

        if self.attempt(run):
            self.kb_changed()

    @precondition(lambda self: bool(self.rels))
    @rule(pick=PICK)
    def remove_prerequisite(self, pick):
        del self.rels[pick % len(self.rels)]
        self.kb_changed()

    @rule(node_pick=PICK, parent_pick=PICK)
    def move_node(self, node_pick, parent_pick):
        nodes = sorted(self.parent)
        node, new_parent = nodes[node_pick % len(nodes)], nodes[parent_pick % len(nodes)]

        def run():
            tree = self.tree()
            if self.kind[node] == g.COURSE:  # courses are exactly the roots
                raise Refused
            if self.kind[new_parent] == g.TOPIC:  # topics are leaves
                raise Refused
            if new_parent == node or node in g.ancestors(tree, new_parent):  # Y1
                raise Refused
            parent = {**self.parent, node: new_parent}
            position = {**self.position, node: self.next_position(new_parent)}
            moved = g.Tree(parent=parent, kind=self.kind, position=position)
            if any(g.is_nested(moved, rel.source, rel.target) for rel in self.rels):  # Y2
                raise Refused
            if self.cyclic(moved, self.topics()):  # Y3 on the changed tree
                raise Refused
            self.parent, self.position = parent, position

        if self.attempt(run):
            self.kb_changed()

    @rule(node_pick=PICK, position=st.integers(0, 5))
    def reorder(self, node_pick, position):
        nodes = sorted(self.parent)
        self.position = {**self.position, nodes[node_pick % len(nodes)]: position}
        self.kb_changed()

    @rule(parent_pick=PICK, is_topic=st.booleans(), params=TOPIC_PARAMS)
    def add_node(self, parent_pick, is_topic, params):
        nodes = sorted(self.parent)
        parent_node = nodes[parent_pick % len(nodes)]
        node = max(self.parent) + 1
        kind = g.TOPIC if is_topic else g.SECTION

        def run():
            if self.kind[parent_node] == g.TOPIC:
                raise Refused
            parent = {**self.parent, node: parent_node}
            kinds = {**self.kind, node: kind}
            position = {**self.position, node: self.next_position(parent_node)}
            grown = g.Tree(parent=parent, kind=kinds, position=position)
            topics = sorted(n for n, k in kinds.items() if k == g.TOPIC)
            # A new topic inherits its ancestors' relations, which can close a
            # cycle that no single relation closed (hence _fresh() in create_node).
            if self.cyclic(grown, topics):
                raise Refused
            self.parent, self.kind, self.position = parent, kinds, position
            if is_topic:
                self.params = {**self.params, node: params}
                self.b = {**self.b, node: 0.0}
                self.n_question = {**self.n_question, node: 0}

        if self.attempt(run):
            self.kb_changed()

    def next_position(self, parent_node) -> int:
        siblings = [self.position[n] for n, p in self.parent.items() if p == parent_node]
        return max(siblings, default=-1) + 1

    def cyclic(self, tree: g.Tree, topics: list[int]) -> bool:
        try:
            g.topological_order(topics, g.expand(self.rels, g.leaves(tree)), g.preorder_positions(tree))
        except g.CycleError:
            return True
        return False

    def kb_changed(self) -> None:
        self.last = None
        self.resync()

    # ------------------------------------------------------------------
    # One answer: Algorithm 2.4, then Algorithm 2.3
    # ------------------------------------------------------------------

    @precondition(lambda self: bool(self.topics()))
    @rule(pick=PICK, answers=ANSWER_RUNS)
    def study(self, pick, answers):
        """A run of answers on one topic, each one an operation of its own."""
        topics = self.topics()
        topic = topics[pick % len(topics)]
        for is_correct in answers:
            if not self.answer(topic, is_correct):
                break
            self.verify_invariants()

    def answer(self, topic: int, is_correct: bool) -> bool:
        outcome: dict = {}

        def run():
            state = self.learner[topic]
            if state.status == r.CLOSED:  # TY1–TY4: the 403 path
                raise Refused
            _, edges, _, pre, succ = self.graph()
            prior_inputs = tuple(
                PriorInput(
                    weight=edges[(u, topic)].weight,
                    p_l=self.learner[u].p_l,
                    p0=self.params[u].p0,
                )
                for u in pre[topic]
            )
            result = s.observe(
                params=self.params[topic],
                constants=CONSTANTS,
                observation=s.Observation(
                    is_correct=is_correct,
                    p_l=state.p_l,
                    theta=self.theta,
                    b_q=self.b[topic],
                    n_student=self.n_student,
                    n_question=self.n_question[topic],
                    prerequisites=prior_inputs,
                ),
            )
            self.theta, self.b[topic] = result.theta_after, result.b_after
            self.n_student += 1
            self.n_question[topic] += 1

            previous = state.flag
            state.flag = r.mastered_flag(
                p_mastery=result.p_after, tau=CONSTANTS.tau, delta=DELTA, previous=previous,
            )
            state.p_l = result.p_after
            state.attempts += 1
            state.status = r.next_status(
                current=state.status, mastered=state.flag, started=True, missing=state.counter,
            )
            if state.flag != previous:
                moved = r.propagate(
                    became_mastered=state.flag,
                    successors=succ[topic],
                    counters={t: st_.counter for t, st_ in self.learner.items()},
                    statuses={t: st_.status for t, st_ in self.learner.items()},
                )
                for t, counter in moved.counters.items():
                    other = self.learner[t]
                    other.counter = counter
                    other.status = r.next_status(
                        current=other.status, mastered=other.flag,
                        started=other.attempts > 0, missing=counter,
                    )
            outcome["result"] = result

        accepted = self.attempt(run)
        self.last = (outcome["result"], is_correct) if accepted else None
        return accepted

    # ------------------------------------------------------------------
    # Invariants, after every accepted operation
    # ------------------------------------------------------------------

    @invariant()
    def verify_invariants(self):
        self.g_l_is_acyclic_and_ordered()
        self.counters_equal_their_recomputation()
        self.probabilities_are_in_the_unit_interval()
        self.assertion_2_5_holds_for_the_last_answer()
        self.statuses_follow_the_table_and_ty5()

    def g_l_is_acyclic_and_ordered(self):
        tree = self.tree()
        edges = g.expand(self.rels, g.leaves(tree))
        topics = self.topics()
        assert not has_cycle(topics, edges)
        order, _lev = g.topological_order(topics, edges, g.preorder_positions(tree))
        assert sorted(order) == topics
        rank = {t: i for i, t in enumerate(order)}
        assert all(rank[a] < rank[b] for a, b in edges)
        # D70: the node graph is acyclic too, not only G_L.
        assert not has_cycle(sorted(self.parent), [(p.source, p.target) for p in self.rels])

    def counters_equal_their_recomputation(self):
        _, _, _, pre, _ = self.graph()
        expected = r.recompute_counters(
            predecessors=pre, flags={t: st_.flag for t, st_ in self.learner.items()},
        )
        assert {t: st_.counter for t, st_ in self.learner.items()} == expected

    def probabilities_are_in_the_unit_interval(self):
        for st_ in self.learner.values():
            assert st_.p_l is None or 0.0 <= st_.p_l <= 1.0
        if self.last is not None:
            step, _ = self.last
            # Hypothesis found that once P(L) has rounded to exactly 1.0, a
            # wrong answer gave a posterior of 1 + O(1e-15) (D65a); it is
            # clamped now, so every quantity is a probability exactly.
            for value in (step.p_before, step.p_hat, step.posterior, step.p_after, step.guess, step.slip):
                assert 0.0 <= value <= 1.0

    def assertion_2_5_holds_for_the_last_answer(self):
        if self.last is None:
            return
        step, is_correct = self.last
        assert step.guess + step.slip < 1.0
        assert step.posterior == bkt.posterior(
            p_l=step.p_before, guess=step.guess, slip=step.slip, is_correct=is_correct,
        )
        p = step.p_before
        if is_correct:
            assert step.posterior >= p - ROUNDING
        else:
            assert step.posterior <= p + ROUNDING
        if STRICT_MARGIN < p < 1.0 - STRICT_MARGIN:
            assert (step.posterior > p) if is_correct else (step.posterior < p)

    def statuses_follow_the_table_and_ty5(self):
        for st_ in self.learner.values():
            started = st_.attempts > 0
            if started:
                assert st_.status != r.CLOSED, "TY5: a started topic was closed"
                if st_.flag:
                    assert st_.status == r.MASTERED
                else:
                    assert st_.status in (r.IN_PROGRESS, r.REVIEW)
            else:
                assert st_.status == (r.OPEN if st_.counter == 0 else r.CLOSED)


TestKnowledgeBaseProperties = KnowledgeBaseMachine.TestCase
TestKnowledgeBaseProperties.settings = PROPERTY_SETTINGS
