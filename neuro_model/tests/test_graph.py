"""
Reference values of NEUROLEARN_REMEDIATION.md, section 4 (graph part),
checked on the pure functions without a database.
"""

from __future__ import annotations

import pytest

from neuro_model import graph as g

# Course C; sections B1, B2, B3; topics t1..t8 (ids chosen so that id order
# differs from programme order, to make sure ties use pos, not id).
C, B1, B2, B3 = 100, 30, 20, 10
T = {i: 90 - i for i in range(1, 9)}  # t1=89, ..., t8=82
NAMES = {C: "C", B1: "B1", B2: "B2", B3: "B3", **{v: f"t{k}" for k, v in T.items()}}


def reference_tree() -> g.Tree:
    parent = {C: None, B1: C, B2: C, B3: C}
    kind = {C: g.COURSE, B1: g.SECTION, B2: g.SECTION, B3: g.SECTION}
    position = {C: 0, B1: 1, B2: 2, B3: 3}
    layout = {B1: (1, 2, 3), B2: (4, 5), B3: (6, 7, 8)}
    for section, numbers in layout.items():
        for slot, n in enumerate(numbers):
            parent[T[n]] = section
            kind[T[n]] = g.TOPIC
            position[T[n]] = slot
    return g.Tree(parent=parent, kind=kind, position=position)


def reference_prerequisites() -> list[g.Prerequisite]:
    pairs = [(T[1], T[3]), (T[1], T[5]), (T[2], T[4]), (T[3], T[6]),
             (T[5], T[6]), (T[6], T[7]), (T[6], T[8]), (T[4], B3)]
    return [g.Prerequisite(id=i, source=a, target=b) for i, (a, b) in enumerate(pairs, 1)]


def names(ids):
    return [NAMES[i] for i in ids]


@pytest.fixture
def kb():
    tree = reference_tree()
    leaf_sets = g.leaves(tree)
    rels = reference_prerequisites()
    edges = g.expand(rels, leaf_sets)
    pos = g.preorder_positions(tree)
    topics = [n for n, k in tree.kind.items() if k == g.TOPIC]
    return tree, leaf_sets, rels, edges, pos, topics


def test_inherited_graph_has_ten_edges(kb):
    _, _, _, edges, _, _ = kb
    assert len(edges) == 10
    inherited = {(NAMES[a], NAMES[b]) for (a, b), e in edges.items() if not e.direct}
    assert inherited == {("t4", "t6"), ("t4", "t7"), ("t4", "t8")}
    assert edges[(T[4], T[7])].via == (8,)


def test_preorder_positions(kb):
    _, _, _, _, pos, _ = kb
    by_pos = sorted(pos, key=pos.get)
    assert names(by_pos) == ["C", "B1", "t1", "t2", "t3", "B2", "t4", "t5", "B3", "t6", "t7", "t8"]


def test_priority_order_and_levels(kb):
    _, _, _, edges, pos, topics = kb
    order, lev = g.topological_order(topics, edges, pos)
    assert names(order) == ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]
    assert [lev[T[i]] for i in range(1, 9)] == [0, 0, 1, 1, 1, 2, 3, 3]


def test_fifo_queue_gives_a_different_order(kb):
    _, _, _, edges, pos, topics = kb
    order, _ = g.topological_order(topics, edges, pos, queue="fifo")
    assert names(order) == ["t1", "t2", "t3", "t5", "t4", "t6", "t7", "t8"]


def test_descendants_redundant_edges_and_kappa(kb):
    _, _, _, edges, pos, topics = kb
    order, _ = g.topological_order(topics, edges, pos)
    succ = g.successors(topics, edges)
    desc = g.descendant_bitsets(order, succ)
    sizes = [bin(desc[T[i]]).count("1") for i in range(1, 9)]
    assert sizes == [5, 4, 3, 3, 3, 2, 0, 0]
    assert names(g.bitset_members(desc[T[2]], order)) == ["t4", "t6", "t7", "t8"]
    redundant = {(NAMES[a], NAMES[b]) for a, b in g.redundant_edges(order, succ, desc)}
    assert redundant == {("t4", "t7"), ("t4", "t8")}
    assert g.order_conflicts(edges, pos) == []


def test_kappa_counts_backward_edges(kb):
    _, _, _, _, pos, _ = kb
    assert g.order_conflicts([(T[5], T[4]), (T[1], T[2])], pos) == [(T[5], T[4])]


def test_adding_t8_to_t3_closes_a_cycle(kb):
    tree, leaf_sets, rels, _, _, _ = kb
    chain = g.find_cycle_chain(tree, rels, leaf_sets, x=T[8], y=T[3])
    assert names(chain) == ["t3", "t6", "t8"]


def test_acyclic_additions_have_no_chain(kb):
    tree, leaf_sets, rels, _, _, _ = kb
    assert g.find_cycle_chain(tree, rels, leaf_sets, x=T[2], y=T[5]) is None
    assert g.find_cycle_chain(tree, rels, leaf_sets, x=B1, y=T[7]) is None


def test_cycle_through_inheritance_is_found(kb):
    """t4 → B3 makes t4 a prerequisite of t8; t8 → t2 then closes t2 → t4 → t8 → t2."""
    tree, leaf_sets, rels, _, _, _ = kb
    assert names(g.find_cycle_chain(tree, rels, leaf_sets, x=T[8], y=T[2])) == ["t2", "t4", "t8"]


def test_nesting_rule(kb):
    tree, *_ = kb
    assert g.is_nested(tree, B3, T[6])          # (B3, t6) is rejected by Y2
    assert g.is_nested(tree, T[6], B3)
    assert g.is_nested(tree, C, T[1])
    assert g.is_nested(tree, T[1], T[1])
    assert not g.is_nested(tree, B1, T[6])


def test_moving_t4_into_b3_violates_y2(kb):
    tree, *_ = kb
    moved = g.Tree(parent={**tree.parent, T[4]: B3}, kind=tree.kind, position=tree.position)
    assert g.is_nested(moved, T[4], B3)


def test_audit_probe_parent_level_cycle():
    """Audit probe 1: `B requires A` and `a1 requires b1` form a cycle in G_L."""
    A, B, a1, b1, root = 1, 2, 3, 4, 5
    tree = g.Tree(
        parent={root: None, A: root, B: root, a1: A, b1: B},
        kind={root: g.COURSE, A: g.SECTION, B: g.SECTION, a1: g.TOPIC, b1: g.TOPIC},
        position={root: 0, A: 0, B: 1, a1: 0, b1: 0},
    )
    rels = [g.Prerequisite(1, A, B)]
    leaf_sets = g.leaves(tree)
    assert g.find_cycle_chain(tree, rels, leaf_sets, x=b1, y=a1) == [a1, b1]


def test_cycle_error_lists_unordered_topics():
    pos = {1: 0, 2: 1, 3: 2}
    with pytest.raises(g.CycleError) as exc:
        g.topological_order([1, 2, 3], [(1, 2), (2, 3), (3, 2)], pos)
    assert exc.value.remaining == [2, 3]


def test_weights_take_the_maximum():
    tree = g.Tree(
        parent={1: None, 2: 1, 3: 1, 4: 3},
        kind={1: g.COURSE, 2: g.TOPIC, 3: g.SECTION, 4: g.TOPIC},
        position={1: 0, 2: 0, 3: 1, 4: 0},
    )
    rels = [g.Prerequisite(7, 2, 3, 0.4), g.Prerequisite(8, 2, 4, 0.9)]
    edges = g.expand(rels, g.leaves(tree))
    assert edges == {(2, 4): g.LeafEdge(weight=0.9, via=(7, 8), direct=True)}


def test_archived_endpoints_are_ignored():
    tree = g.Tree(parent={1: None, 2: 1}, kind={1: g.COURSE, 2: g.TOPIC}, position={1: 0, 2: 0})
    assert g.expand([g.Prerequisite(1, 2, 99)], g.leaves(tree)) == {}


def test_parent_loops_are_detected():
    tree = g.Tree(parent={1: 2, 2: 1}, kind={1: g.SECTION, 2: g.SECTION}, position={1: 0, 2: 0})
    with pytest.raises(ValueError):
        g.ancestors(tree, 1)
    with pytest.raises(ValueError):
        g.preorder_positions(tree)
