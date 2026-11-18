"""
Randomised cross-checks of neuro_model.graph against brute force (fixed seed).

- Algorithm 2.1: a chain is returned exactly when adding the relation makes
  the expanded G_L cyclic, and the chain is a real path from Leaves(y) to Leaves(x).
- Algorithm 2.2: the order respects every edge, is the lexicographically
  smallest by (pos, id), and lev is the longest-path depth.
- Desc* equals plain reachability; redundant edges match the definition.
"""

from __future__ import annotations

import heapq
import random

import pytest

from neuro_model import graph as g

SEED = 20261003
CASES = 300


def random_forest(rng: random.Random, n: int) -> g.Tree:
    parent: dict[int, int | None] = {}
    for node in range(n):
        parent[node] = None if node == 0 or rng.random() < 0.15 else rng.randrange(node)
    has_children = {p for p in parent.values() if p is not None}
    kind = {
        node: g.COURSE if parent[node] is None else (g.SECTION if node in has_children else g.TOPIC)
        for node in parent
    }
    position = {node: rng.randrange(4) for node in parent}
    return g.Tree(parent=parent, kind=kind, position=position)


def acyclic_relations(rng, tree, leaf_sets, tries):
    rels: list[g.Prerequisite] = []
    nodes = list(tree.parent)
    for i in range(tries):
        x, y = rng.choice(nodes), rng.choice(nodes)
        if g.is_nested(tree, x, y):
            continue
        candidate = [*rels, g.Prerequisite(len(rels) + 1, x, y)]
        if not has_cycle(tree, candidate, leaf_sets):
            rels = candidate
    return rels


def has_cycle(tree, rels, leaf_sets) -> bool:
    edges = g.expand(rels, leaf_sets)
    topics = [n for n, k in tree.kind.items() if k == g.TOPIC]
    try:
        g.topological_order(topics, edges, g.preorder_positions(tree))
    except g.CycleError:
        return True
    return False


def reachable(succ, start):
    seen, stack = set(), [start]
    while stack:
        for w in succ.get(stack.pop(), ()):
            if w not in seen:
                seen.add(w)
                stack.append(w)
    return seen


@pytest.mark.parametrize("case", range(CASES))
def test_random_knowledge_bases(case):
    rng = random.Random(SEED + case)
    tree = random_forest(rng, rng.randrange(3, 14))
    leaf_sets = g.leaves(tree)
    rels = acyclic_relations(rng, tree, leaf_sets, tries=rng.randrange(1, 12))
    pos = g.preorder_positions(tree)
    topics = [n for n, k in tree.kind.items() if k == g.TOPIC]
    edges = g.expand(rels, leaf_sets)

    # Algorithm 2.2
    order, lev = g.topological_order(topics, edges, pos)
    rank = {t: i for i, t in enumerate(order)}
    assert sorted(order) == sorted(topics)
    assert all(rank[a] < rank[b] for a, b in edges)
    indeg = {t: 0 for t in topics}
    for _, b in edges:
        indeg[b] += 1
    succ = g.successors(topics, edges)
    heap = [((pos[t], t), t) for t in topics if indeg[t] == 0]
    heapq.heapify(heap)
    smallest = []
    while heap:
        v = heapq.heappop(heap)[1]
        smallest.append(v)
        for w in succ[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                heapq.heappush(heap, ((pos[w], w), w))
    assert order == smallest
    for t in order:
        preds = [a for a, b in edges if b == t]
        assert lev[t] == (max(lev[a] for a in preds) + 1 if preds else 0)

    # Desc* and redundant edges
    desc = g.descendant_bitsets(order, succ)
    for t in topics:
        assert set(g.bitset_members(desc[t], order)) == reachable(succ, t)
    expected_redundant = {
        (a, b) for a, b in edges
        if any(w != b and b in reachable(succ, w) for w in succ[a])
    }
    assert set(g.redundant_edges(order, succ, desc)) == expected_redundant

    # Algorithm 2.1 against brute force, for every non-nested candidate
    for x in tree.parent:
        for y in tree.parent:
            if g.is_nested(tree, x, y):
                continue
            chain = g.find_cycle_chain(tree, rels, leaf_sets, x, y)
            assert (chain is not None) == has_cycle(tree, [*rels, g.Prerequisite(999, x, y)], leaf_sets)
            if chain is not None:
                assert chain[0] in leaf_sets[y] and chain[-1] in leaf_sets[x]
                assert all((a, b) in edges for a, b in zip(chain, chain[1:]))
