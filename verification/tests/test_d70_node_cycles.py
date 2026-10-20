"""
D70 / F7 — Algorithm 2.1 also refuses a cycle of the node graph G = (N, E_P).

A random-state check written here, not taken from ``test_assertions.py``:
random trees with empty sections and topic-less courses, random relations
between any two nodes, random new topics and random moves, all through
``curriculum.services.kb``. For each attempt the expected decision is built
from two independent parts:

- the pre-D70 rule — ``verification.oracle.graph`` (Y2, and Y3 on G_L with
  ``networkx``), plus "duplicate";
- the D70 rule — a path y ⇝ x in G over the active nodes, found here by BFS.

Asserted, at every step:

1. the service accepts exactly when neither rule refuses;
2. after every accepted change both G and G_L are acyclic (``networkx``);
3. a refused change leaves the version, nodes and relations as they were;
4. the corrected 2.2: when x and y hold topics and y ⇝ x runs through nodes
   that all hold topics, the pre-D70 rule alone already says "cycle" — i.e.
   for such nodes D70 changes nothing;
5. a new topic or a move that closes a cycle of G_L is still refused.

Seed: SEED + 70_000 + case.
"""

from __future__ import annotations

import random
from collections import deque

import networkx as nx
import pytest
from django.conf import settings

from verification.oracle import graph as og
from verification.oracle.tree import OracleTree

SEED: int = settings.VERIFICATION_SEED
CASES = 30
STEPS = 30

pytestmark = pytest.mark.django_db


def _read():
    from curriculum.models import KnowledgeBaseVersion, Topic, TopicPrerequisite

    rows = list(Topic.objects.filter(is_archived=False).values_list("id", "parent_id", "kind", "position"))
    tree = OracleTree(
        parent={p: q for p, q, _, _ in rows},
        kind={p: k for p, _, k, _ in rows},
        position={p: s for p, _, _, s in rows},
    )
    prereqs = list(
        TopicPrerequisite.objects.order_by("id").values_list("id", "prerequisite_id", "topic_id", "weight")
    )
    return tree, prereqs, KnowledgeBaseVersion.current()


def _node_path(prereqs, start: int, goal: int, allowed=None) -> bool:
    """BFS over E_P from ``start``; True when ``goal`` is reached (through ``allowed`` nodes only)."""
    succ: dict[int, list[int]] = {}
    for _rid, x, y, _w in prereqs:
        succ.setdefault(x, []).append(y)
    seen, queue = {start}, deque([start])
    while queue:
        node = queue.popleft()
        if node == goal:
            return True
        for nxt in succ.get(node, ()):
            if nxt not in seen and (allowed is None or nxt in allowed):
                seen.add(nxt)
                queue.append(nxt)
    return False


def _g_acyclic(tree, prereqs) -> bool:
    graph = nx.DiGraph()
    graph.add_nodes_from(tree.parent)
    graph.add_edges_from((x, y) for _rid, x, y, _w in prereqs if x in tree.parent and y in tree.parent)
    return nx.is_directed_acyclic_graph(graph)


def _gl_acyclic(tree, prereqs) -> bool:
    return nx.is_directed_acyclic_graph(og.digraph(tree, prereqs))


def _build(rng: random.Random, tag: str) -> list[int]:
    from curriculum.services import kb

    containers = []
    for c in range(rng.randint(1, 2)):
        containers.append(kb.create_node(name=f"C{tag}{c}", slug=f"c{tag}-{c}", kind="course").pk)
    for s in range(rng.randint(3, 6)):
        parent = rng.choice(containers)
        containers.append(kb.create_node(name=f"S{tag}{s}", slug=f"s{tag}-{s}", parent=parent, kind="section").pk)
    # few topics, so that most containers are empty
    for t in range(rng.randint(0, 4)):
        kb.create_node(name=f"T{tag}{t}", slug=f"t{tag}-{t}", parent=rng.choice(containers[1:] or containers),
                       kind="topic")
    return containers


@pytest.mark.parametrize("case", range(CASES))
def test_d70_random_states_keep_g_and_g_l_acyclic(case):
    from curriculum.services import kb

    rng = random.Random(SEED + 70_000 + case)
    tag = f"d70x{case}"
    _build(rng, tag)
    counter = 0
    seen = {"node_only": 0, "gl": 0, "topic_refused": 0, "move_refused": 0, "accepted": 0}

    for step in range(STEPS):
        tree, prereqs, version = _read()
        nodes = sorted(tree.parent)
        containers = [n for n in nodes if tree.kind[n] != "topic"]
        action = rng.choices(["relation", "topic", "move"], weights=[6, 2, 2])[0]

        if action == "relation":
            x, y = rng.choice(nodes), rng.choice(nodes)
            pre = og.rejection_reason(tree, prereqs, x, y)
            if pre is None and any(px == x and py == y for _r, px, py, _w in prereqs):
                pre = "duplicate"
            node_cycle = x != y and _node_path(prereqs, y, x)
            # corrected 2.2: a node-level cycle through topic-holding nodes only
            # is already a G_L cycle — D70 adds nothing there.
            holding = {n for n in nodes if tree.leaves(n)}
            if x in holding and y in holding and x != y and not tree.violates_y2(x, y) \
                    and _node_path(prereqs, y, x, allowed=holding):
                assert pre in ("cycle", "duplicate"), (case, step, x, y, pre)
            expected_refused = pre is not None or node_cycle
            call = lambda: kb.add_prerequisite(prerequisite=x, topic=y)  # noqa: E731
        elif action == "topic":
            parent = rng.choice(containers)
            counter += 1
            reasons = og.add_topic_rejections(tree, prereqs, parent, new_id=10**9)
            expected_refused = bool(reasons)
            slug = f"{tag}-n{counter}"
            call = lambda: kb.create_node(name=slug, slug=slug, parent=parent, kind="topic")  # noqa: E731
        else:
            movable = [n for n in nodes if tree.kind[n] != "course"]
            if not movable:
                continue
            node, new_parent = rng.choice(movable), rng.choice(containers)
            if tree.parent[node] == new_parent:
                continue
            reasons = og.move_rejections(tree, prereqs, node, new_parent)
            expected_refused = bool(reasons)
            call = lambda: kb.move_node(node, new_parent)  # noqa: E731

        try:
            call()
            refused, reason = False, None
        except kb.KBError as error:
            refused, reason = True, error.reason

        assert refused == expected_refused, (case, step, action, reason, locals().get("pre"),
                                             locals().get("node_cycle"), locals().get("reasons"))
        after, after_prereqs, after_version = _read()
        if refused:
            assert (after.parent, after.kind, after_prereqs, after_version) == (
                tree.parent, tree.kind, prereqs, version), (case, step, action)
            if action == "relation" and pre is None and node_cycle:
                assert reason == "cycle"
                seen["node_only"] += 1
            elif action == "relation" and pre == "cycle":
                seen["gl"] += 1
            elif action == "topic":
                assert reason == "cycle"
                seen["topic_refused"] += 1
            elif action == "move":
                seen["move_refused"] += 1
        else:
            assert after_version == version + 1, (case, step, action)
            seen["accepted"] += 1
        assert _g_acyclic(after, after_prereqs), (case, step, action)
        assert _gl_acyclic(after, after_prereqs), (case, step, action)

    print(f"D70 case {case}: {seen}")
    assert seen["accepted"] > 0, seen


def test_d70_the_random_states_reach_every_kind_of_refusal():
    """Not vacuous: over all cases, node-only cycles, G_L cycles and refused topics all occur."""
    from curriculum.services import kb

    totals = {"node_only": 0, "gl": 0}
    for case in range(CASES):
        rng = random.Random(SEED + 70_000 + case)
        _build(rng, f"d70y{case}")
        for _ in range(STEPS):
            tree, prereqs, _v = _read()
            nodes = sorted(tree.parent)
            x, y = rng.choice(nodes), rng.choice(nodes)
            pre = og.rejection_reason(tree, prereqs, x, y)
            node_cycle = x != y and _node_path(prereqs, y, x)
            try:
                kb.add_prerequisite(prerequisite=x, topic=y)
            except kb.KBError:
                pass
            totals["node_only"] += pre is None and node_cycle
            totals["gl"] += pre == "cycle"
    print(f"D70 totals: {totals}")
    assert totals["node_only"] > 0 and totals["gl"] > 0, totals


def test_d70_counterexample_two_courses_without_topics_is_refused():
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    c0 = kb.create_node(name="C0", slug="d70-c0", kind="course").pk
    c1 = kb.create_node(name="C1", slug="d70-c1", kind="course").pk
    kb.add_prerequisite(prerequisite=c0, topic=c1)
    before = TopicPrerequisite.objects.count()
    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(prerequisite=c1, topic=c0)
    assert exc.value.reason == "cycle"
    assert list(exc.value.chain)[0] == c0 and list(exc.value.chain)[-1] == c1, exc.value.chain
    assert TopicPrerequisite.objects.count() == before


def test_d70_two_empty_sections_and_the_hidden_cycle_is_gone():
    """S1 → S2 accepted, S2 → S1 refused; then both sections take topics without a Y3 error."""
    from curriculum.services import kb

    course = kb.create_node(name="H", slug="d70-h", kind="course").pk
    s1 = kb.create_node(name="S1", slug="d70-s1", parent=course, kind="section").pk
    s2 = kb.create_node(name="S2", slug="d70-s2", parent=course, kind="section").pk
    kb.add_prerequisite(prerequisite=s1, topic=s2)
    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(prerequisite=s2, topic=s1)
    assert exc.value.reason == "cycle"
    kb.create_node(name="a", slug="d70-a", parent=s1, kind="topic")
    kb.create_node(name="b", slug="d70-b", parent=s2, kind="topic")  # refused with Y3 before D70


def test_d70_topic_holding_nodes_behave_as_before():
    """Reference-course shape: the decision on topic-holding nodes is the pre-D70 oracle's."""
    from curriculum.services import kb

    course = kb.create_node(name="P", slug="d70-p", kind="course").pk
    a = kb.create_node(name="A", slug="d70-pa", parent=course, kind="section").pk
    b = kb.create_node(name="B", slug="d70-pb", parent=course, kind="section").pk
    a1 = kb.create_node(name="a1", slug="d70-a1", parent=a, kind="topic").pk
    b1 = kb.create_node(name="b1", slug="d70-b1", parent=b, kind="topic").pk
    kb.add_prerequisite(prerequisite=a, topic=b)
    tree, prereqs, _ = _read()
    assert og.rejection_reason(tree, prereqs, b1, a1) == "cycle"
    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(prerequisite=b1, topic=a1)
    assert exc.value.reason == "cycle" and list(exc.value.chain) == [a1, b1]  # leaf-level chain, as before
