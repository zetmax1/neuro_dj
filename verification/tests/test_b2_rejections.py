"""
V-B2 — changes that must be rejected, and the reason reported with them.

Section 4 / NEUROLEARN_AUDIT probes:
  (t8, t3)            -> cycle, chain t3 -> t6 -> t8
  (B3, t6)            -> nested (Y2)
  move t4 under B3    -> rejected (t4 -> B3 would point into its own ancestor)
  probe 1             -> "B requires A" then "a1 requires b1" -> cycle
  probe 2             -> ancestor -> descendant prerequisite -> nested
Probe 3 ("A not mastered -> b1 closed") belongs to per-learner readiness and is
recorded as N/A in ``test_na.py`` (stage 4 is not implemented).
"""

from __future__ import annotations

import pytest

from verification.oracle import graph as og
from verification.oracle import reference as ref

pytestmark = pytest.mark.django_db


def _version() -> int:
    from curriculum.models import KnowledgeBaseVersion

    return KnowledgeBaseVersion.current()


def test_v_b2_cycle_is_rejected_with_the_chain(reference_course, snapshot_now):
    """(t8, t3): rejected by Y3; the reported chain is t3 -> t6 -> t8."""
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    course = reference_course
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()
    x, y = course.id_of["t8"], course.id_of["t3"]

    assert og.rejection_reason(tree, prereqs, x, y) == "cycle"

    before_version, before_rows = _version(), TopicPrerequisite.objects.count()
    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(prerequisite=x, topic=y)

    error = exc.value
    assert error.reason == "cycle"
    assert tuple(course.slugs(error.chain)) == ref.EXPECTED_CYCLE_CHAIN
    assert og.cycle_chain_is_valid(tree, prereqs, x, y, error.chain)
    payload = error.payload()
    assert payload["chain_names"] == [
        ref.NODES[s][1] for s in ref.EXPECTED_CYCLE_CHAIN
    ]
    assert payload["edge"] == [x, y]
    assert TopicPrerequisite.objects.count() == before_rows
    assert _version() == before_version


def test_v_b2_nested_prerequisite_is_rejected(reference_course):
    """(B3, t6): t6 is inside B3, so Y2 refuses the relation."""
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    course = reference_course
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()
    x, y = course.id_of["B3"], course.id_of["t6"]

    assert og.rejection_reason(tree, prereqs, x, y) == "nested"

    before_version, before_rows = _version(), TopicPrerequisite.objects.count()
    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(prerequisite=x, topic=y)
    assert exc.value.reason == "nested"
    assert exc.value.payload()["edge"] == [x, y]
    assert TopicPrerequisite.objects.count() == before_rows
    assert _version() == before_version


def test_v_b2_moving_t4_under_b3_is_rejected(reference_course, snapshot_now):
    """
    t4 -> B3 is an existing relation; moving t4 into B3 would make it point at
    its own ancestor (Y2), so the move must be refused and rolled back.
    """
    from curriculum.models import Topic
    from curriculum.services import kb

    course = reference_course
    tree = course.oracle_tree()
    t4, b3 = course.id_of["t4"], course.id_of["B3"]

    # The oracle: after the move the relation (t4, B3) violates Y2.
    moved = course.oracle_tree()
    moved.parent[t4] = b3
    moved.__post_init__()
    assert moved.violates_y2(t4, b3)
    assert not tree.violates_y1(t4, b3)  # the refusal is Y2, not Y1

    before_version = _version()
    with pytest.raises(kb.KBError) as exc:
        kb.move_node(t4, b3)
    assert exc.value.reason == "nested"
    assert Topic.objects.get(pk=t4).parent_id == course.id_of["B2"]
    assert _version() == before_version
    assert snapshot_now().tree.parent[t4] == course.id_of["B2"]


def test_v_b2_self_prerequisite_is_rejected(reference_course):
    from curriculum.services import kb

    t1 = reference_course.id_of["t1"]
    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(prerequisite=t1, topic=t1)
    assert exc.value.reason == "self"


def test_v_b2_duplicate_prerequisite_is_rejected(reference_course):
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    course = reference_course
    before = TopicPrerequisite.objects.count()
    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(prerequisite=course.id_of["t1"], topic=course.id_of["t3"])
    assert exc.value.reason == "duplicate"
    assert TopicPrerequisite.objects.count() == before


@pytest.fixture
def two_sections(db):
    """Audit probes 1 and 2: sections A and B holding one topic each."""
    from curriculum.services import kb

    course = kb.create_node(name="Probe course", slug="probe", kind="course")
    section_a = kb.create_node(name="A", slug="A", parent=course, kind="section")
    section_b = kb.create_node(name="B", slug="B", parent=course, kind="section")
    a1 = kb.create_node(name="a1", slug="a1", parent=section_a, kind="topic")
    b1 = kb.create_node(name="b1", slug="b1", parent=section_b, kind="topic")
    return {"course": course.pk, "A": section_a.pk, "B": section_b.pk, "a1": a1.pk, "b1": b1.pk}


def test_v_b2_audit_probe_1_section_cycle(two_sections):
    """'B requires A' then 'a1 requires b1' closes a cycle a1 -> b1 -> a1."""
    from curriculum.models import Topic, TopicPrerequisite
    from curriculum.services import kb
    from verification.oracle.tree import OracleTree

    ids = two_sections
    kb.add_prerequisite(prerequisite=ids["A"], topic=ids["B"])

    rows = list(Topic.objects.filter(is_archived=False).values_list("id", "parent_id", "kind", "position"))
    tree = OracleTree(
        parent={p: q for p, q, _, _ in rows},
        kind={p: k for p, _, k, _ in rows},
        position={p: s for p, _, _, s in rows},
    )
    prereqs = list(
        TopicPrerequisite.objects.order_by("id").values_list("id", "prerequisite_id", "topic_id", "weight")
    )
    assert og.rejection_reason(tree, prereqs, ids["b1"], ids["a1"]) == "cycle"

    with pytest.raises(kb.KBError) as exc:
        kb.add_prerequisite(prerequisite=ids["b1"], topic=ids["a1"])
    assert exc.value.reason == "cycle"
    assert exc.value.chain == [ids["a1"], ids["b1"]]
    assert og.cycle_chain_is_valid(tree, prereqs, ids["b1"], ids["a1"], exc.value.chain)


def test_v_b2_audit_probe_2_ancestor_to_descendant(two_sections):
    """A prerequisite between a node and its own descendant is refused (Y2)."""
    from curriculum.services import kb

    ids = two_sections
    for x, y in ((ids["A"], ids["a1"]), (ids["a1"], ids["A"]), (ids["course"], ids["b1"])):
        with pytest.raises(kb.KBError) as exc:
            kb.add_prerequisite(prerequisite=x, topic=y)
        assert exc.value.reason == "nested", (x, y)


def test_v_b2_kind_rules(two_sections):
    """3.1 kind rules: a topic is a leaf, a course is exactly a root."""
    from curriculum.services import kb

    ids = two_sections
    with pytest.raises(kb.KBError) as exc:
        kb.create_node(name="under a topic", slug="under-a1", parent=ids["a1"], kind="topic")
    assert exc.value.reason == "parent_is_topic"

    with pytest.raises(kb.KBError) as exc:
        kb.create_node(name="rooted course", slug="c2", parent=ids["A"], kind="course")
    assert exc.value.reason == "kind"

    with pytest.raises(kb.KBError) as exc:
        kb.move_node(ids["A"], ids["A"])
    assert exc.value.reason in {"move_into_subtree", "kind"}


# ---------------------------------------------------------------------------
# Tree changes: "rebuild G_L and check it with Algorithm 2.2" (3.1)
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_sections(db):
    """
    Three sections with a prerequisite ring between them. While the sections hold
    no topics the ring produces no E_L edge at all, so each relation is legal on
    its own -- the cycle only appears once the sections gain topics.
    """
    from curriculum.services import kb

    course = kb.create_node(name="Ring", slug="ring", kind="course")
    ids = {"course": course.pk}
    for name in ("A", "B", "C"):
        ids[name] = kb.create_node(name=name, slug=f"ring-{name}", parent=course, kind="section").pk
    for x, y in (("A", "B"), ("B", "C"), ("C", "A")):
        kb.add_prerequisite(prerequisite=ids[x], topic=ids[y])
    return ids


def test_v_b2_adding_a_topic_that_closes_a_cycle_is_rejected(empty_sections, snapshot_now):
    """The third topic turns the section ring into a cycle of G_L; it must be refused."""
    from curriculum.models import Topic
    from curriculum.services import kb

    ids = empty_sections
    assert snapshot_now().edges == {}, "empty sections inherit nothing"

    kb.create_node(name="a1", slug="ring-a1", parent=ids["A"], kind="topic")
    kb.create_node(name="b1", slug="ring-b1", parent=ids["B"], kind="topic")

    before_version, before_count = _version(), Topic.objects.count()
    with pytest.raises(kb.KBError) as exc:
        kb.create_node(name="c1", slug="ring-c1", parent=ids["C"], kind="topic")
    assert exc.value.reason == "cycle"
    assert not Topic.objects.filter(slug="ring-c1").exists()
    assert Topic.objects.count() == before_count
    assert _version() == before_version


def test_v_b2_a_move_that_closes_a_cycle_is_rejected(db, snapshot_now):
    """
    (A, B) with a1 in A and b1 in B gives a1 -> b1; the relation (b1, c1) gives
    b1 -> c1. Moving c1 into A would add c1 -> b1 and close the cycle.
    """
    from curriculum.models import Topic
    from curriculum.services import kb

    course = kb.create_node(name="Move", slug="mv", kind="course")
    a = kb.create_node(name="A", slug="mv-A", parent=course, kind="section")
    b = kb.create_node(name="B", slug="mv-B", parent=course, kind="section")
    c = kb.create_node(name="C", slug="mv-C", parent=course, kind="section")
    a1 = kb.create_node(name="a1", slug="mv-a1", parent=a, kind="topic")
    b1 = kb.create_node(name="b1", slug="mv-b1", parent=b, kind="topic")
    c1 = kb.create_node(name="c1", slug="mv-c1", parent=c, kind="topic")
    kb.add_prerequisite(prerequisite=a.pk, topic=b.pk)
    kb.add_prerequisite(prerequisite=b1.pk, topic=c1.pk)
    assert {(a1.pk, b1.pk), (b1.pk, c1.pk)} == set(snapshot_now().edges)

    before_version = _version()
    with pytest.raises(kb.KBError) as exc:
        kb.move_node(c1.pk, a.pk)
    assert exc.value.reason == "cycle"
    assert Topic.objects.get(pk=c1.pk).parent_id == c.pk
    assert _version() == before_version
    assert {(a1.pk, b1.pk), (b1.pk, c1.pk)} == set(snapshot_now().edges)


def test_v_b2_y4_a_node_with_questions_cannot_become_a_section(db):
    """Y4: questions belong to exactly one node of kind ``topic``."""
    from assessments.models import Question
    from curriculum.models import Topic
    from curriculum.services import kb

    course = kb.create_node(name="Y4", slug="y4", kind="course")
    topic = kb.create_node(name="t", slug="y4-t", parent=course, kind="topic")
    Question.objects.create(topic=topic, text="2 + 2 = ?", difficulty=1)

    before_version = _version()
    with pytest.raises(kb.KBError) as exc:
        kb.update_node(topic.pk, kind="section")
    assert exc.value.reason == "has_questions"
    assert Topic.objects.get(pk=topic.pk).kind == "topic"
    assert _version() == before_version

    with pytest.raises(kb.KBError) as exc:
        kb.create_node(name="child", slug="y4-child", parent=topic.pk, kind="topic")
    assert exc.value.reason == "parent_is_topic"


def test_v_b2_y4_questions_cannot_be_attached_to_a_section(db):
    """The other half of Y4, from the question side."""
    from django.core.exceptions import ValidationError

    from assessments.models import Question
    from curriculum.services import kb

    course = kb.create_node(name="Y4b", slug="y4b", kind="course")
    section = kb.create_node(name="s", slug="y4b-s", parent=course, kind="section")

    with pytest.raises(ValidationError):
        Question.objects.create(topic=section, text="?", difficulty=1)
    with pytest.raises(ValidationError):
        Question.objects.create(topic=course, text="?", difficulty=1)
    assert not Question.objects.exists()
