"""
V-B3 (service level) — random tree mutations through ``curriculum.services.kb``.

For every attempt the decision of the service is compared with the oracle, which
rebuilds G_L and asks ``networkx`` whether it is still acyclic. A rejected
attempt must leave the tree, the relations and the version untouched; an
accepted one must bump the version by exactly one and match the oracle's KB.

Seed: SEED + 20_000 + case.
"""

from __future__ import annotations

import random

import pytest
from django.conf import settings

from verification.oracle import graph as og
from verification.oracle.tree import OracleTree

CASES = 40
SEED = settings.VERIFICATION_SEED

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


def _build_random_kb(rng: random.Random, tag: str) -> dict[str, int]:
    """A small random course: sections, topics and whatever relations are legal."""
    from curriculum.services import kb

    course = kb.create_node(name=f"c{tag}", slug=f"c{tag}", kind="course")
    nodes = [course.pk]
    sections = [course.pk]
    for i in range(rng.randint(2, 4)):
        parent = rng.choice(sections)
        section = kb.create_node(name=f"s{tag}-{i}", slug=f"s{tag}-{i}", parent=parent, kind="section")
        sections.append(section.pk)
        nodes.append(section.pk)
    topics = []
    for i in range(rng.randint(3, 7)):
        parent = rng.choice(sections)
        topic = kb.create_node(name=f"t{tag}-{i}", slug=f"t{tag}-{i}", parent=parent, kind="topic")
        topics.append(topic.pk)
        nodes.append(topic.pk)

    for _ in range(rng.randint(2, 6)):
        x, y = rng.choice(nodes), rng.choice(nodes)
        tree, prereqs, _ = _read()
        if (x, y) in {(r[1], r[2]) for r in prereqs}:
            continue
        if og.rejection_reason(tree, prereqs, x, y) is None:
            kb.add_prerequisite(prerequisite=x, topic=y, weight=round(rng.uniform(0.1, 1.0), 3))
    return {"course": course.pk, "sections": sections, "topics": topics, "nodes": nodes}


@pytest.mark.parametrize("case", range(CASES))
def test_v_b3_random_tree_mutations(case):
    from curriculum.services import kb

    rng = random.Random(SEED + 20_000 + case)
    plan = _build_random_kb(rng, f"{case}")
    movable = [n for n in plan["nodes"] if n != plan["course"]]
    attempts = 0

    for step in range(8):
        tree, prereqs, version = _read()
        if rng.random() < 0.65:
            node, parent = rng.choice(movable), rng.choice(plan["nodes"])
            expected = og.move_rejections(tree, prereqs, node, parent)
            action = lambda: kb.move_node(node, parent)  # noqa: E731
            label = f"move {node} -> {parent}"
        else:
            parent = rng.choice(plan["nodes"])
            new_id = -(step + 1)
            expected = og.add_topic_rejections(tree, prereqs, parent, new_id)
            action = lambda: kb.create_node(  # noqa: E731
                name=f"n{case}-{step}", slug=f"n{case}-{step}", parent=parent, kind="topic"
            )
            label = f"create topic under {parent}"
        attempts += 1

        if expected:
            with pytest.raises(kb.KBError) as exc:
                action()
            assert exc.value.reason in expected, f"{label}: reason {exc.value.reason!r} not in {expected}"
            assert _read() == (tree, prereqs, version), f"{label}: a rejected change left traces"
        else:
            action()
            after_tree, after_prereqs, after_version = _read()
            assert after_version == version + 1, f"{label}: version moved by more than one"
            assert after_prereqs == prereqs
            import networkx as nx

            assert nx.is_directed_acyclic_graph(og.digraph(after_tree, after_prereqs))
            assert not any(after_tree.violates_y2(x, y) for _r, x, y, _w in after_prereqs)

    assert attempts == 8
