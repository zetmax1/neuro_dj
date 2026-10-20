"""
Chapter II's assertions 2.1–2.4 and 2.6, as properties of ``neuro_model``.

Each test states the assertion as the chapter does and checks it on random
knowledge bases of the kind the KB service admits: a forest whose roots are
courses and whose leaves are topics or empty sections (``kb.create_node``
accepts a section with no children), with prerequisites accepted by the
service's own rules — Y2 (``is_nested``), Algorithm 2.1 (``find_cycle_chain``),
D70's node-graph check (``find_node_cycle_chain``) and Algorithm 2.2 on the
result (``topological_order``, which is ``kb._fresh``). Assertion 2.2 is also
checked on knowledge bases admitted by the chapter's rules alone (no D70), the
only place a cycle through an empty node can arise. Assertion 2.5 is tested in
``test_student.py`` and ``test_properties.py``.

Deterministic: ``derandomize=True`` and no example database on disk. A test
that fails here is a counterexample to the assertion as stated, to be reported,
not a test to be adjusted.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from neuro_model import graph as g
from neuro_model import readiness as r
from neuro_model import student as s
from neuro_model import trajectory as tr
from neuro_model.tests.test_properties import CONSTANTS, DELTA, TOPIC_PARAMS, has_cycle

PICK = st.integers(min_value=0, max_value=10_000)
ASSERTION_SETTINGS = settings(max_examples=300, derandomize=True, database=None, deadline=None)


# ---------------------------------------------------------------------------
# Knowledge bases the service admits
# ---------------------------------------------------------------------------

def admit(tree: g.Tree, rels: list[g.Prerequisite], x: int, y: int, *, node_graph: bool = True) -> bool:
    """
    ``kb.add_prerequisite``'s decision: Y2, no duplicate, Algorithm 2.1, D70's
    node-graph check, then 2.2. ``node_graph=False`` is the chapter's rule
    without D70.
    """
    if g.is_nested(tree, x, y) or any((p.source, p.target) == (x, y) for p in rels):
        return False
    leaf_sets = g.leaves(tree)
    if g.find_cycle_chain(tree, rels, leaf_sets, x, y) is not None:
        return False
    if node_graph and g.find_node_cycle_chain(rels, x, y) is not None:
        return False
    return not cyclic_g_l(tree, [*rels, g.Prerequisite(len(rels) + 1, x, y)])


def topics_of(tree: g.Tree) -> list[int]:
    return sorted(n for n, k in tree.kind.items() if k == g.TOPIC)


def cyclic_g_l(tree: g.Tree, rels) -> bool:
    try:
        g.topological_order(topics_of(tree), g.expand(rels, g.leaves(tree)), g.preorder_positions(tree))
    except g.CycleError:
        return True
    return False


@st.composite
def knowledge_bases(draw, node_graph: bool = True):
    n = draw(st.integers(min_value=2, max_value=10))
    parent: dict[int, int | None] = {0: None}
    for node in range(1, n):
        choice = draw(st.integers(-1, node - 1))  # -1: a new course
        parent[node] = None if choice < 0 else choice
    has_children = {p for p in parent.values() if p is not None}
    kind = {}
    for node in parent:
        if parent[node] is None:
            kind[node] = g.COURSE
        elif node in has_children:
            kind[node] = g.SECTION
        else:  # a leaf: a topic, or now and then an empty section
            kind[node] = g.SECTION if draw(st.integers(0, 5)) == 0 else g.TOPIC
    tree = g.Tree(parent=parent, kind=kind, position={node: draw(st.integers(0, 3)) for node in parent})
    rels: list[g.Prerequisite] = []
    nodes = sorted(parent)
    for x_pick, y_pick in draw(st.lists(st.tuples(PICK, PICK), max_size=14)):
        x, y = nodes[x_pick % n], nodes[y_pick % n]
        if admit(tree, rels, x, y, node_graph=node_graph):
            rels.append(g.Prerequisite(len(rels) + 1, x, y))
    return tree, rels


def graph_of(tree, rels):
    """Topics, G_L edges, Pre and Succ, the Algorithm 2.2 order and lev."""
    topics = topics_of(tree)
    edges = g.expand(rels, g.leaves(tree))
    order, lev = g.topological_order(topics, edges, g.preorder_positions(tree))
    pre = {t: [a for a, b in edges if b == t] for t in topics}
    succ = {t: [b for a, b in edges if a == t] for t in topics}
    return topics, edges, order, lev, pre, succ


@st.composite
def learner_states(draw, topics):
    """M flags and statuses as the platform keeps them (TY5, the 3.4 table)."""
    started = {t for t in topics if draw(st.booleans())}
    flags = {t: (t in started and draw(st.booleans())) for t in topics}
    current = {
        t: (r.MASTERED if flags[t] else draw(st.sampled_from((r.IN_PROGRESS, r.REVIEW))))
        for t in started
    }
    return started, flags, current


def statuses(topics, pre, flags, started, current):
    counters = r.recompute_counters(predecessors=pre, flags=flags)
    return {
        t: r.next_status(current=current.get(t, r.CLOSED), mastered=flags[t],
                         started=t in started, missing=counters[t])
        for t in topics
    }


# ---------------------------------------------------------------------------
# 2.1 — one answer changes readiness only on Succ(v)
# ---------------------------------------------------------------------------

@ASSERTION_SETTINGS
@given(kb=knowledge_bases(), data=st.data())
def test_assertion_2_1_one_answer_changes_readiness_only_on_its_successors(kb, data):
    tree, rels = kb
    topics, _edges, _order, _lev, pre, succ = graph_of(tree, rels)
    if not topics:
        return
    started, flags, current = data.draw(learner_states(topics))
    status = statuses(topics, pre, flags, started, current)
    answerable = [t for t in topics if status[t] != r.CLOSED]
    if not answerable:
        return
    v = data.draw(st.sampled_from(answerable))
    # P(L) consistent with M under the τ/δ hysteresis; None before the first answer.
    p_l = None
    if v in started:
        p_l = data.draw(st.floats(CONSTANTS.tau - DELTA, 1.0) if flags[v] else st.floats(0.0, CONSTANTS.tau - 1e-9))
    step = s.observe(
        params=data.draw(TOPIC_PARAMS), constants=CONSTANTS,
        observation=s.Observation(is_correct=data.draw(st.booleans()), p_l=p_l, theta=0.0, b_q=0.0),
    )
    after = dict(flags)
    after[v] = r.mastered_flag(p_mastery=step.p_after, tau=CONSTANTS.tau, delta=DELTA, previous=flags[v])

    def readiness(f):
        return {w: r.is_ready(f[u] for u in pre[w]) for w in topics}

    before_r, after_r = readiness(flags), readiness(after)
    changed = {w for w in topics if before_r[w] != after_r[w]}
    assert changed <= set(succ[v]), f"readiness changed outside Succ({v}): {changed - set(succ[v])}"
    if after[v] == flags[v]:
        assert changed == set(), "M_s(v) did not change, yet readiness did"


# ---------------------------------------------------------------------------
# 2.2 — G_L acyclic ⇒ G = (N, E_P) acyclic, for cycles whose nodes hold
# topics; with an empty node it fails (D70); the converse fails
# ---------------------------------------------------------------------------

def nonempty_nodes(tree: g.Tree) -> list[int]:
    leaf_sets = g.leaves(tree)
    return sorted(n for n in tree.parent if leaf_sets[n])


@ASSERTION_SETTINGS
@given(kb=knowledge_bases(node_graph=False))
def test_assertion_2_2_holds_for_cycles_whose_every_node_holds_a_topic(kb):
    """
    The corrected statement (D70): on knowledge bases the chapter's rules admit
    (Algorithm 2.1 on G_L only, so cycles through empty nodes do arise), an
    acyclic G_L leaves no cycle in G among the nodes that hold a topic.
    """
    tree, rels = kb
    assert not cyclic_g_l(tree, rels)
    kept = set(nonempty_nodes(tree))
    among = [(p.source, p.target) for p in rels if p.source in kept and p.target in kept]
    assert not has_cycle(sorted(kept), among)


@ASSERTION_SETTINGS
@given(kb=knowledge_bases())
def test_with_d70_both_g_l_and_g_are_acyclic(kb):
    tree, rels = kb
    assert not cyclic_g_l(tree, rels)
    assert not has_cycle(sorted(tree.parent), [(p.source, p.target) for p in rels])


@ASSERTION_SETTINGS
@given(kb=knowledge_bases(node_graph=False), x_pick=PICK, y_pick=PICK)
def test_the_node_graph_check_refuses_exactly_the_edges_that_close_a_cycle_in_g(kb, x_pick, y_pick):
    """D70's check against a full rebuild of G = (N, E_P)."""
    tree, rels = kb
    nodes = sorted(tree.parent)
    x, y = nodes[x_pick % len(nodes)], nodes[y_pick % len(nodes)]
    if x == y:
        return
    chain = g.find_node_cycle_chain(rels, x, y)
    edges = [(p.source, p.target) for p in rels]
    closes = has_cycle(nodes, [*edges, (x, y)]) and not has_cycle(nodes, edges)
    if not has_cycle(nodes, edges):
        assert (chain is not None) == closes
    if chain is not None:
        assert chain[0] == y and chain[-1] == x
        assert all(pair in edges for pair in zip(chain, chain[1:]))


def test_assertion_2_2_as_first_stated_fails_on_empty_nodes():
    """
    Why D70 exists: two courses with no topics, each a prerequisite of the
    other. G has the cycle C0 → C1 → C0, G_L has no edge at all, so the
    unconditional 2.2 fails and Algorithm 2.1 on G_L accepts the second
    relation; D70's node-graph check refuses it with the chain [C0, C1].
    """
    c0, c1 = 0, 1
    tree = g.Tree(parent={c0: None, c1: None}, kind={c0: g.COURSE, c1: g.COURSE}, position={c0: 0, c1: 1})
    first = [g.Prerequisite(1, c0, c1)]
    both = [*first, g.Prerequisite(2, c1, c0)]
    assert not cyclic_g_l(tree, both) and g.expand(both, g.leaves(tree)) == {}
    assert has_cycle([c0, c1], [(p.source, p.target) for p in both])
    assert g.find_cycle_chain(tree, first, g.leaves(tree), c1, c0) is None
    assert g.find_node_cycle_chain(first, c1, c0) == [c0, c1]


def test_assertion_2_2_the_converse_fails_section_four_probe_one():
    """
    Probe 1 of section 4: “B requires A” and “a1 requires b1”. At node level
    A → B and b1 → a1 form no cycle, but G_L has a1 → b1 → a1; Algorithm 2.1
    refuses the second relation with that chain.
    """
    c, a, b, a1, b1 = 1, 2, 3, 4, 5
    tree = g.Tree(
        parent={c: None, a: c, b: c, a1: a, b1: b},
        kind={c: g.COURSE, a: g.SECTION, b: g.SECTION, a1: g.TOPIC, b1: g.TOPIC},
        position={c: 0, a: 0, b: 1, a1: 0, b1: 0},
    )
    rels = [g.Prerequisite(1, a, b), g.Prerequisite(2, b1, a1)]
    assert not has_cycle(sorted(tree.parent), [(p.source, p.target) for p in rels])
    assert cyclic_g_l(tree, rels)
    assert g.find_cycle_chain(tree, rels[:1], g.leaves(tree), b1, a1) == [a1, b1]


# ---------------------------------------------------------------------------
# 2.3 — the basis of Algorithm 2.1
# ---------------------------------------------------------------------------

@ASSERTION_SETTINGS
@given(kb=knowledge_bases(), x_pick=PICK, y_pick=PICK)
def test_assertion_2_3_algorithm_2_1_refuses_exactly_the_edges_that_close_a_cycle(kb, x_pick, y_pick):
    tree, rels = kb
    nodes = sorted(tree.parent)
    x, y = nodes[x_pick % len(nodes)], nodes[y_pick % len(nodes)]
    if g.is_nested(tree, x, y):  # the assertion assumes Y2
        return
    leaf_sets = g.leaves(tree)
    chain = g.find_cycle_chain(tree, rels, leaf_sets, x, y)
    rebuilt = g.expand([*rels, g.Prerequisite(len(rels) + 1, x, y)], leaf_sets)
    assert (chain is not None) == has_cycle(topics_of(tree), rebuilt)
    if chain is not None:
        current = g.expand(rels, leaf_sets)
        assert chain[0] in leaf_sets[y] and chain[-1] in leaf_sets[x]
        assert all((a, b) in current for a, b in zip(chain, chain[1:])), "the chain is a path of the current G_L"


# ---------------------------------------------------------------------------
# 2.4 — G_L acyclic ⇔ A^n = 0; A^h = 0 and A^{h−1} ≠ 0 with h levels
# ---------------------------------------------------------------------------

def matrix_power(a: list[list[int]], k: int) -> list[list[int]]:
    n = len(a)
    out = [[int(i == j) for j in range(n)] for i in range(n)]
    for _ in range(k):
        out = [[sum(out[i][m] * a[m][j] for m in range(n)) for j in range(n)] for i in range(n)]
    return out


def is_zero(m) -> bool:
    return all(v == 0 for row in m for v in row)


def adjacency(topics, edges):
    index = {t: i for i, t in enumerate(topics)}
    a = [[0] * len(topics) for _ in topics]
    for x, y in edges:
        a[index[x]][index[y]] = 1
    return a


@ASSERTION_SETTINGS
@given(kb=knowledge_bases())
def test_assertion_2_4_levels_bound_the_powers_of_the_adjacency_matrix(kb):
    tree, rels = kb
    topics, edges, _order, lev, _pre, _succ = graph_of(tree, rels)
    if not topics:
        return
    a = adjacency(topics, edges)
    h = max(lev.values()) + 1  # the number of levels of Algorithm 2.2
    assert is_zero(matrix_power(a, h))
    assert not is_zero(matrix_power(a, h - 1))
    assert is_zero(matrix_power(a, len(topics)))


@ASSERTION_SETTINGS
@given(n=st.integers(1, 7), pairs=st.lists(st.tuples(st.integers(0, 6), st.integers(0, 6)), max_size=16))
def test_assertion_2_4_acyclic_exactly_when_a_to_the_n_vanishes(n, pairs):
    topics = list(range(n))
    edges = {(x % n, y % n) for x, y in pairs if x % n != y % n}
    try:
        g.topological_order(topics, edges, {t: t for t in topics})
        acyclic = True
    except g.CycleError:
        acyclic = False
    assert acyclic == is_zero(matrix_power(adjacency(topics, edges), n))


# ---------------------------------------------------------------------------
# 2.6 — Need_s(g) is necessary and sufficient
# ---------------------------------------------------------------------------

def master_in_order(order, goal, topics, pre, flags, started, current) -> str:
    """
    Master ``order`` one topic at a time, as a learner can: a topic is answered
    only when it is not closed (TY1–TY4), and once mastered it stays so (the
    assertion's “does not fall below τ − δ”). Returns the goal's status.
    """
    flags, started, current = dict(flags), set(started), dict(current)
    for u in order:
        if statuses(topics, pre, flags, started, current)[u] == r.CLOSED:
            continue  # cannot be answered, so cannot be mastered
        flags[u] = True
        started.add(u)
        current[u] = r.MASTERED
    return statuses(topics, pre, flags, started, current)[goal]


@ASSERTION_SETTINGS
@given(kb=knowledge_bases(), data=st.data())
def test_assertion_2_6_need_is_the_smallest_set_that_opens_the_goal(kb, data):
    tree, rels = kb
    topics, _edges, order, _lev, pre, _succ = graph_of(tree, rels)
    if not topics:
        return
    started, flags, current = data.draw(learner_states(topics))
    status = statuses(topics, pre, flags, started, current)
    closed = [t for t in topics if status[t] == r.CLOSED]
    if not closed:
        return
    goal = data.draw(st.sampled_from(closed))
    needed = tr.need(goal=goal, statuses=status, flags=flags, predecessors=pre)
    path = tr.path_to(goal=goal, needed=needed, order=order)[:-1]

    # Sufficient: mastered in topological order, the goal opens.
    assert master_in_order(path, goal, topics, pre, flags, started, current) != r.CLOSED
    # Necessary: without any one of them, mastering the rest leaves it closed.
    for left_out in needed:
        rest = [u for u in path if u != left_out]
        assert master_in_order(rest, goal, topics, pre, flags, started, current) == r.CLOSED, (
            f"goal {goal} opened without {left_out}"
        )
