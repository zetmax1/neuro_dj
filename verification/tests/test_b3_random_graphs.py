"""
V-B3 — 500 random forests with random prerequisite sets, compared against the
``networkx`` oracle.

Checked per case: G_L (plain expansion), the add/reject decision
(``is_directed_acyclic_graph``) and the reported chain, the Algorithm 2.2 order
(edges respected and lexicographically smallest for (pos, id)), lev (longest
path), Desc* (``descendants``) and redundant edges (``transitive_reduction``),
plus kappa.

Seed: ``settings.VERIFICATION_SEED``; case i uses ``Random(SEED + i)``.
These are the pure functions of ``neuro_model.graph`` plus ``snapshot_from``,
so no database is needed.
"""

from __future__ import annotations

import random

import pytest
from django.conf import settings

from verification.oracle import graph as og
from verification.oracle.tree import OracleTree

CASES = 500
SEED = settings.VERIFICATION_SEED


def _random_forest(rng: random.Random) -> OracleTree:
    """
    A random ordered forest: roots are courses, internal nodes are sections,
    leaves are topics (a leaf is left as an empty section in 15% of cases, so
    Leaves(n) = {} is exercised too). Node ids are shuffled so that id order
    differs from creation order, and positions repeat so that the (position, id)
    tie-break matters.
    """
    size = rng.randint(4, 14)
    ids = rng.sample(range(100, 999), size)
    roots = ids[: rng.randint(1, min(3, size))]
    parent: dict[int, int | None] = {r: None for r in roots}
    placed = list(roots)
    for node in ids[len(roots):]:
        parent[node] = rng.choice(placed)
        placed.append(node)

    has_child = {p for p in parent.values() if p is not None}
    kind: dict[int, str] = {}
    for node in ids:
        if parent[node] is None:
            kind[node] = "course"
        elif node in has_child:
            kind[node] = "section"
        else:
            kind[node] = "topic" if rng.random() > 0.15 else "section"
    position = {node: rng.randint(0, 2) for node in ids}
    return OracleTree(parent=parent, kind=kind, position=position)


def _to_prototype(tree: OracleTree, prereqs):
    from neuro_model import graph as g

    proto_tree = g.Tree(parent=dict(tree.parent), kind=dict(tree.kind), position=dict(tree.position))
    proto_rels = tuple(g.Prerequisite(id=i, source=x, target=y, weight=w) for i, x, y, w in prereqs)
    return proto_tree, proto_rels


def _grow(rng: random.Random, tree: OracleTree):
    """
    Offer random candidate relations one by one. For each, the prototype's
    Algorithm 2.1 decision is compared with the oracle; accepted ones are kept.
    Returns (relations, decisions_compared).
    """
    from neuro_model import graph as g

    nodes = list(tree.parent)
    prereqs: list[tuple[int, int, int, float]] = []
    compared = 0
    next_id = 1
    for _ in range(2 * len(nodes)):
        x, y = rng.choice(nodes), rng.choice(nodes)
        if any((x, y) == (r[1], r[2]) for r in prereqs):
            continue
        expected = og.rejection_reason(tree, prereqs, x, y)

        proto_tree, proto_rels = _to_prototype(tree, prereqs)
        leaf_sets = g.leaves(proto_tree)
        if x == y:
            actual = "self"
        elif g.is_nested(proto_tree, x, y):
            actual = "nested"
        else:
            chain = g.find_cycle_chain(proto_tree, proto_rels, leaf_sets, x, y)
            actual = "cycle" if chain is not None else None
            if chain is not None:
                assert og.cycle_chain_is_valid(tree, prereqs, x, y, chain), (
                    f"invalid cycle chain {chain} for ({x}, {y})"
                )
        compared += 1
        assert actual == expected, f"({x}, {y}): prototype said {actual!r}, oracle {expected!r}"
        if expected is None:
            prereqs.append((next_id, x, y, round(rng.uniform(0.05, 1.0), 3)))
            next_id += 1
    return prereqs, compared


@pytest.mark.parametrize("case", range(CASES))
def test_v_b3_random_case(case):
    from curriculum.services.graph import snapshot_from

    rng = random.Random(SEED + case)
    tree = _random_forest(rng)
    prereqs, compared = _grow(rng, tree)
    assert compared > 0

    pos = tree.pos()
    digraph = og.digraph(tree, prereqs)
    proto_tree, proto_rels = _to_prototype(tree, prereqs)
    snap = snapshot_from(0, proto_tree, proto_rels)

    # pos and Leaves
    assert snap.pos == pos
    for node in tree.parent:
        assert snap.leaves_of(node) == tree.leaves(node)

    # G_L with weights
    oracle_edges = og.inherited_edges(tree, prereqs)
    assert {e: le.weight for e, le in snap.edges.items()} == pytest.approx(oracle_edges, abs=1e-12)
    assert set(snap.edges) == set(digraph.edges)

    # Algorithm 2.2
    assert og.order_respects_edges(digraph, snap.order)
    assert list(snap.order) == og.lexicographic_order(digraph, pos)
    assert snap.lev == og.lev(digraph)

    # Desc*, redundancy, kappa
    oracle_desc = og.desc_star(digraph)
    for topic in snap.order:
        assert set(snap.descendants(topic)) == oracle_desc[topic]
    assert set(snap.redundant) == og.redundant_edges(digraph)
    assert set(snap.conflicts) == og.kappa_edges(snap.edges, pos)
    assert snap.kappa == len(og.kappa_edges(snap.edges, pos))


def test_v_b3_cycle_error_names_the_unordered_topics():
    """
    Algorithm 2.2 must raise CycleError with the topics left out, never append
    them silently (3.2). Built by hand because the service refuses such a KB.
    """
    from neuro_model import graph as g

    tree = g.Tree(
        parent={1: None, 2: 1, 3: 1, 4: 1},
        kind={1: "course", 2: "topic", 3: "topic", 4: "topic"},
        position={1: 0, 2: 0, 3: 1, 4: 2},
    )
    pos = g.preorder_positions(tree)
    edges = {(2, 3): None, (3, 4): None, (4, 2): None}
    with pytest.raises(g.CycleError) as exc:
        g.topological_order([2, 3, 4], edges, pos)
    assert exc.value.remaining == [2, 3, 4]


def _big_forest(rng: random.Random) -> OracleTree:
    """A deeper, wider forest (25-60 nodes) for the same comparisons."""
    size = rng.randint(25, 60)
    ids = rng.sample(range(1000, 9999), size)
    roots = ids[: rng.randint(1, 4)]
    parent: dict[int, int | None] = {r: None for r in roots}
    placed = list(roots)
    for node in ids[len(roots):]:
        # Prefer recent nodes so the tree gets deep rather than flat.
        parent[node] = rng.choice(placed[-6:] if rng.random() < 0.6 else placed)
        placed.append(node)
    has_child = {p for p in parent.values() if p is not None}
    kind = {
        node: "course" if parent[node] is None else ("section" if node in has_child else "topic")
        for node in ids
    }
    return OracleTree(parent=parent, kind=kind, position={n: rng.randint(0, 4) for n in ids})


@pytest.mark.parametrize("case", range(60))
def test_v_b3_random_large_case(case):
    """Same comparisons on 25-60 node forests (seed SEED + 10_000 + case)."""
    from curriculum.services.graph import snapshot_from

    rng = random.Random(SEED + 10_000 + case)
    tree = _big_forest(rng)
    prereqs, compared = _grow(rng, tree)
    assert compared > 0

    pos = tree.pos()
    digraph = og.digraph(tree, prereqs)
    proto_tree, proto_rels = _to_prototype(tree, prereqs)
    snap = snapshot_from(0, proto_tree, proto_rels)

    assert snap.pos == pos
    assert {e: le.weight for e, le in snap.edges.items()} == pytest.approx(
        og.inherited_edges(tree, prereqs), abs=1e-12
    )
    assert list(snap.order) == og.lexicographic_order(digraph, pos)
    assert og.order_respects_edges(digraph, snap.order)
    assert snap.lev == og.lev(digraph)
    oracle_desc = og.desc_star(digraph)
    for topic in snap.order:
        assert set(snap.descendants(topic)) == oracle_desc[topic]
    assert set(snap.redundant) == og.redundant_edges(digraph)
    assert set(snap.conflicts) == og.kappa_edges(snap.edges, pos)
