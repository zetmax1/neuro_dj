"""
Mutation score of the implemented part of ``neuro_model`` (V-A4, graph module).

``mutmut`` is not used: the formulas V-A4 names (BKT, IRT, Elo, P(L0)) belong to
stage 3 and do not exist yet. What does exist is ``neuro_model/graph.py``, so
each mutant below breaks one rule of specification 3.1/3.2 on purpose, and the
test asserts that the oracle comparison of V-B1/V-B3 notices. A mutant that
survived would mean the graph checks prove less than they claim.
"""

from __future__ import annotations

import random

import pytest
from django.conf import settings

from verification.oracle import graph as og
from verification.tests.test_b3_random_graphs import _grow, _random_forest, _to_prototype

SEED = settings.VERIFICATION_SEED


# --- the mutants -----------------------------------------------------------

def _mutant_fifo_order(monkeypatch):
    """Algorithm 2.2 with a plain FIFO queue instead of the (pos, id) heap."""
    from neuro_model import graph as g

    original = g.topological_order
    monkeypatch.setattr(
        g, "topological_order",
        lambda topics, edges, pos, *, queue="priority": original(topics, edges, pos, queue="fifo"),
    )


def _mutant_lev_overwrites(monkeypatch):
    """lev(w) = lev(v) + 1 instead of max(lev(w), lev(v) + 1): not the longest path."""
    from neuro_model import graph as g

    def mutated(topics, edges, pos, *, queue="priority"):
        order, _ = g.__dict__["_pristine_topological_order"](topics, edges, pos, queue=queue)
        succ = g.successors(order, edges)
        lev = {t: 0 for t in order}
        for v in order:
            for w in succ[v]:
                lev[w] = lev[v] + 1
        return order, lev

    monkeypatch.setitem(g.__dict__, "_pristine_topological_order", g.topological_order)
    monkeypatch.setattr(g, "topological_order", mutated)


def _mutant_weight_minimum(monkeypatch):
    """The inherited weight becomes the minimum instead of the maximum."""
    from neuro_model import graph as g

    original = g.expand

    def mutated(prerequisites, leaf_sets):
        prerequisites = list(prerequisites)
        edges = original(prerequisites, leaf_sets)
        out = {}
        for edge, leaf_edge in edges.items():
            producing = [r.weight for r in prerequisites if r.id in leaf_edge.via]
            out[edge] = g.LeafEdge(weight=min(producing), via=leaf_edge.via, direct=leaf_edge.direct)
        return out

    monkeypatch.setattr(g, "expand", mutated)


def _mutant_redundant_includes_self(monkeypatch):
    """Drop the ``w != b`` guard, so every edge looks redundant through itself."""
    from neuro_model import graph as g

    def mutated(order, succ, desc):
        index = {t: i for i, t in enumerate(order)}
        out = []
        for a in order:
            direct = list(succ.get(a, ()))
            for b in direct:
                bit = 1 << index[b]
                if any(desc[w] & bit for w in direct):
                    out.append((a, b))
        return out

    monkeypatch.setattr(g, "redundant_edges", mutated)


def _mutant_desc_direct_only(monkeypatch):
    """Desc* becomes the direct successors only (no transitive closure)."""
    from neuro_model import graph as g

    def mutated(order, succ):
        index = {t: i for i, t in enumerate(order)}
        return {v: sum(1 << index[w] for w in succ.get(v, ())) for v in order}

    monkeypatch.setattr(g, "descendant_bitsets", mutated)


def _mutant_kappa_counts_equal(monkeypatch):
    """kappa uses pos(b) <= pos(a) instead of pos(b) < pos(a)."""
    from neuro_model import graph as g

    monkeypatch.setattr(
        g, "order_conflicts",
        lambda edges, pos: sorted((a, b) for a, b in edges if pos[b] <= pos[a]),
    )


def _mutant_pos_ignores_position(monkeypatch):
    """Preorder visits siblings by id only, ignoring ``position`` (D4 broken)."""
    from neuro_model import graph as g

    original = g.preorder_positions

    def mutated(tree):
        flat = g.Tree(parent=tree.parent, kind=tree.kind, position={n: 0 for n in tree.parent})
        return original(flat)

    monkeypatch.setattr(g, "preorder_positions", mutated)


def _mutant_leaves_of_a_section_is_itself(monkeypatch):
    """Leaves(n) returns {n} for every node, so nothing is inherited."""
    from neuro_model import graph as g

    monkeypatch.setattr(g, "leaves", lambda tree: {n: frozenset((n,)) for n in tree.parent})


# Mutants that change behaviour and therefore must be killed.
MUTANTS = {
    "2.2 uses a FIFO queue": _mutant_fifo_order,
    "lev overwrites instead of max": _mutant_lev_overwrites,
    "inherited weight takes the minimum": _mutant_weight_minimum,
    "Desc* keeps only direct successors": _mutant_desc_direct_only,
    "pos ignores position (D4)": _mutant_pos_ignores_position,
    "Leaves(n) = {n} for every node": _mutant_leaves_of_a_section_is_itself,
}

# Equivalent mutants: they cannot be killed because they compute the same thing.
# ``test_equivalent_mutants_really_are_equivalent`` proves each claim.
EQUIVALENT = {
    "kappa counts pos(b) == pos(a)": _mutant_kappa_counts_equal,
    "redundancy ignores the w != b guard": _mutant_redundant_includes_self,
}

CASES = 200


# --- the detector: exactly the comparison V-B3 performs --------------------

def _comparison_fails(case: int) -> bool:
    """True when the oracle comparison of V-B3 rejects the (possibly mutated) code."""
    from curriculum.services.graph import snapshot_from

    rng = random.Random(SEED + case)
    tree = _random_forest(rng)
    prereqs, _ = _grow(rng, tree)
    pos = tree.pos()
    digraph = og.digraph(tree, prereqs)
    proto_tree, proto_rels = _to_prototype(tree, prereqs)
    try:
        snap = snapshot_from(0, proto_tree, proto_rels)
    except Exception:
        return True

    oracle_desc = og.desc_star(digraph)
    checks = [
        snap.pos == pos,
        all(snap.leaves_of(n) == tree.leaves(n) for n in tree.parent),
        {e: le.weight for e, le in snap.edges.items()} == og.inherited_edges(tree, prereqs),
        og.order_respects_edges(digraph, snap.order),
        list(snap.order) == og.lexicographic_order(digraph, pos),
        snap.lev == og.lev(digraph),
        all(set(snap.descendants(t)) == oracle_desc[t] for t in snap.order),
        set(snap.redundant) == og.redundant_edges(digraph),
        set(snap.conflicts) == og.kappa_edges(snap.edges, pos),
    ]
    return not all(checks)


def _detects(case: int) -> bool:
    """``_comparison_fails``, counting a mutant caught during generation as caught."""
    try:
        return _comparison_fails(case)
    except AssertionError:
        # _grow itself compares the Algorithm 2.1 decision against the oracle.
        return True


def test_the_detector_passes_on_unmutated_code():
    assert not any(_detects(case) for case in range(CASES))


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_every_mutant_is_killed(name, monkeypatch):
    """Every behaviour-changing mutant must be rejected by one of the random cases."""
    MUTANTS[name](monkeypatch)
    killed_at = next((case for case in range(CASES) if _detects(case)), None)
    assert killed_at is not None, f"mutant survived {CASES} random cases: {name}"


@pytest.mark.parametrize("name", sorted(EQUIVALENT))
def test_equivalent_mutants_survive_as_expected(name, monkeypatch):
    EQUIVALENT[name](monkeypatch)
    assert not any(_detects(case) for case in range(CASES)), (
        f"{name} was expected to be an equivalent mutant but changed behaviour"
    )


def test_equivalent_mutants_really_are_equivalent():
    """
    Why the two mutants above cannot be killed:

    * ``pos`` is a preorder index, hence injective, and ``expand`` never emits a
      self loop, so ``pos[b] == pos[a]`` is impossible for an edge of E_L and
      ``<`` and ``<=`` agree.
    * G_L is acyclic, so b is never in Desc*(b): adding ``w == b`` to the
      redundancy test adds a term that is always false.
    """
    from curriculum.services.graph import snapshot_from

    for case in range(CASES):
        rng = random.Random(SEED + case)
        tree = _random_forest(rng)
        prereqs, _ = _grow(rng, tree)
        snap = snapshot_from(0, *_to_prototype(tree, prereqs))

        assert len(set(snap.pos.values())) == len(snap.pos)          # injective
        assert not [edge for edge in snap.edges if edge[0] == edge[1]]  # no self loop
        for index, topic in enumerate(snap.order):
            assert not snap.desc[topic] >> index & 1                 # b not in Desc*(b)
