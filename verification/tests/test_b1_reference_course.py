"""
V-B1 — the section-4 reference course: E_L, the Algorithm 2.2 order, lev,
|Desc*|, redundant edges, kappa, and the differing FIFO order.

Every number is checked twice: against the literal table of section 4 and
against the independent ``networkx`` oracle built from the same database rows.
"""

from __future__ import annotations

import pytest

from verification.oracle import graph as og
from verification.oracle import reference as ref

pytestmark = pytest.mark.django_db


def test_v_b1_el_has_the_ten_inherited_edges(reference_course, snapshot_now):
    """E_L: 10 edges; t4->B3 produces t4->t6, t4->t7, t4->t8."""
    course, snap = reference_course, snapshot_now()
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()

    actual = course.slug_edges(snap.edges)
    expected_oracle = course.slug_edges(og.inherited_edges(tree, prereqs))

    assert actual == ref.EXPECTED_EL
    assert actual == expected_oracle
    assert len(snap.edges) == 10
    assert {("t4", "t6"), ("t4", "t7"), ("t4", "t8")} <= actual


def test_v_b1_inherited_edge_weights_and_provenance(reference_course, snapshot_now):
    """The weight of an inherited edge is the max of the producing relations."""
    course, snap = reference_course, snapshot_now()
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()

    oracle_w = og.inherited_edges(tree, prereqs)
    oracle_via = og.inherited_via(tree, prereqs)
    for edge, leaf_edge in snap.edges.items():
        assert leaf_edge.weight == pytest.approx(oracle_w[edge], abs=1e-12)
        assert leaf_edge.via == oracle_via[edge]


def test_v_b1_topological_order_and_lev(reference_course, snapshot_now):
    """Algorithm 2.2: order t1..t8 and lev 0,0,1,1,1,2,3,3."""
    course, snap = reference_course, snapshot_now()
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()
    digraph = og.digraph(tree, prereqs)
    pos = tree.pos()

    assert tuple(course.slugs(snap.order)) == ref.EXPECTED_ORDER
    assert course.slugs(snap.order) == course.slugs(og.lexicographic_order(digraph, pos))
    assert og.order_respects_edges(digraph, snap.order)

    oracle_lev = og.lev(digraph)
    assert {course.slug_of[t]: v for t, v in snap.lev.items()} == ref.EXPECTED_LEV
    assert all(snap.lev[t] == oracle_lev[t] for t in digraph.nodes)


def test_v_b1_fifo_queue_gives_a_different_order(reference_course, snapshot_now):
    """The comparison order of section 4: plain Kahn yields t1,t2,t3,t5,t4,..."""
    from neuro_model import graph as g

    course, snap = reference_course, snapshot_now()
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()
    digraph = og.digraph(tree, prereqs)

    fifo, _ = g.topological_order(snap.order, snap.edges, snap.pos, queue="fifo")
    assert tuple(course.slugs(fifo)) == ref.EXPECTED_FIFO_ORDER
    assert course.slugs(fifo) == course.slugs(og.fifo_order(digraph, tree.pos()))
    assert tuple(course.slugs(fifo)) != ref.EXPECTED_ORDER


def test_v_b1_descendant_sets(reference_course, snapshot_now):
    """|Desc*| = 5, 4, 3, 3, 3, 2, 0, 0, and the sets themselves match networkx."""
    course, snap = reference_course, snapshot_now()
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()
    oracle = og.desc_star(og.digraph(tree, prereqs))

    sizes = {course.slug_of[t]: len(snap.descendants(t)) for t in snap.order}
    assert sizes == ref.EXPECTED_DESC_SIZES
    for topic in snap.order:
        assert set(snap.descendants(topic)) == oracle[topic]


def test_v_b1_redundant_edges_and_kappa(reference_course, snapshot_now):
    """Redundant edges t4->t7 and t4->t8 (never removed); kappa = 0."""
    course, snap = reference_course, snapshot_now()
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()
    digraph = og.digraph(tree, prereqs)

    assert course.slug_edges(snap.redundant) == ref.EXPECTED_REDUNDANT
    assert course.slug_edges(snap.redundant) == course.slug_edges(og.redundant_edges(digraph))
    assert snap.kappa == ref.EXPECTED_KAPPA
    assert course.slug_edges(snap.conflicts) == course.slug_edges(
        og.kappa_edges(snap.edges, tree.pos())
    )
    # A reported redundancy must not silently disappear from E_L.
    assert set(snap.redundant) <= set(snap.edges)


def test_v_b1_programme_order_pos_and_depth(reference_course, snapshot_now):
    """pos is the preorder index of the forest (D4); depth matches the tree."""
    course, snap = reference_course, snapshot_now()
    tree = course.oracle_tree()

    assert snap.pos == tree.pos()
    assert snap.depth == {n: tree.depth(n) for n in tree.parent}
    assert course.slugs(snap.topics_in_programme_order(snap.order)) == list(ref.EXPECTED_ORDER)
    assert {course.slug_of[n]: snap.pos[n] for n in course.ids(["course", "B1", "t1"])} == {
        "course": 0, "B1": 1, "t1": 2,
    }


def test_v_b1_leaves_of_every_node(reference_course, snapshot_now):
    """Leaves(n): the topics in n's subtree, {n} for a topic."""
    course, snap = reference_course, snapshot_now()
    tree = course.oracle_tree()

    for node in tree.parent:
        assert snap.leaves_of(node) == tree.leaves(node)
    assert course.slugs(sorted(snap.leaves_of(course.id_of["B3"]))) == ["t6", "t7", "t8"]
    assert snap.leaves_of(course.id_of["t4"]) == frozenset({course.id_of["t4"]})


def test_v_b1_two_relations_on_one_edge_take_the_maximum_weight(reference_course, snapshot_now):
    """
    3.1: "Meros orqali hosil bo'lgan qirraning vazni — uni hosil qilgan
    munosabatlar vaznlarining eng kattasi." t4 -> t6 is produced by (t4, B3);
    adding (t4, t6) directly gives the same E_L edge a second producer.
    """
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    course = reference_course
    inherited = TopicPrerequisite.objects.get(
        prerequisite_id=course.id_of["t4"], topic_id=course.id_of["B3"]
    )
    kb.update_weight(inherited.pk, 0.8)
    direct = kb.add_prerequisite(
        prerequisite=course.id_of["t4"], topic=course.id_of["t6"], weight=0.3
    )

    edge = (course.id_of["t4"], course.id_of["t6"])
    snap = snapshot_now()
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()
    assert snap.edges[edge].weight == pytest.approx(0.8)
    assert snap.edges[edge].via == tuple(sorted((inherited.pk, direct.pk)))
    assert snap.edges[edge].weight == pytest.approx(
        og.inherited_edges(tree, prereqs)[edge]
    )

    kb.update_weight(direct.pk, 1.0)
    snap = snapshot_now()
    assert snap.edges[edge].weight == pytest.approx(1.0)
    assert snap.edges[edge].weight == pytest.approx(
        og.inherited_edges(course.oracle_tree(), course.oracle_prereqs())[edge]
    )


@pytest.mark.parametrize("weight", [1.0, 0.5, 1e-6])
def test_v_b1_weight_inside_the_allowed_interval(reference_course, weight):
    """omega in (0, 1]."""
    from curriculum.services import kb

    course = reference_course
    relation = kb.add_prerequisite(
        prerequisite=course.id_of["t1"], topic=course.id_of["t4"], weight=weight
    )
    assert relation.weight == pytest.approx(weight)
    kb.remove_prerequisite(relation.pk)


@pytest.mark.parametrize("weight", [0.0, -0.1, 1.000001, 2.0, "abc", None])
def test_v_b1_weight_outside_the_interval_is_refused(reference_course, weight):
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    course = reference_course
    before = TopicPrerequisite.objects.count()
    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(
            prerequisite=course.id_of["t1"], topic=course.id_of["t4"], weight=weight
        )
    assert exc.value.reason == "weight"
    assert TopicPrerequisite.objects.count() == before
