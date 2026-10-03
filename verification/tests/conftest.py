"""
Fixtures of the verification suite.

The reference course is built through the only documented writer of the
knowledge base (``curriculum.services.kb``): if that service refused a legal
build, the refusal itself would be a finding. Everything that is *checked*
afterwards is compared against ``verification.oracle``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from django.conf import settings

from verification.oracle import reference
from verification.oracle.graph import Rel
from verification.oracle.tree import OracleTree

SEED: int = settings.VERIFICATION_SEED


@dataclass
class Course:
    """The reference course in the database, with slug <-> id translation."""

    id_of: dict[str, int]
    slug_of: dict[int, str]

    def ids(self, slugs) -> list[int]:
        return [self.id_of[s] for s in slugs]

    def slugs(self, ids) -> list[str]:
        return [self.slug_of[i] for i in ids]

    def slug_edges(self, edges) -> set[tuple[str, str]]:
        return {(self.slug_of[a], self.slug_of[b]) for a, b in edges}

    def oracle_tree(self) -> OracleTree:
        from curriculum.models import Topic

        rows = list(
            Topic.objects.filter(is_archived=False).values_list("id", "parent_id", "kind", "position")
        )
        return OracleTree(
            parent={pk: parent for pk, parent, _, _ in rows},
            kind={pk: kind for pk, _, kind, _ in rows},
            position={pk: position for pk, _, _, position in rows},
        )

    def oracle_prereqs(self) -> list[Rel]:
        from curriculum.models import TopicPrerequisite

        return [
            (pk, x, y, w)
            for pk, x, y, w in TopicPrerequisite.objects.order_by("id").values_list(
                "id", "prerequisite_id", "topic_id", "weight"
            )
        ]


@pytest.fixture
def reference_course(db) -> Course:
    """The section-4 course, built node by node through the KB service."""
    from curriculum.services import kb

    id_of: dict[str, int] = {}
    for slug in reference.ORDER:
        kind, name, parent_slug = reference.NODES[slug]
        node = kb.create_node(
            name=name,
            slug=slug,
            parent=id_of[parent_slug] if parent_slug else None,
            kind=kind,
        )
        id_of[slug] = node.pk
    for x, y in reference.PREREQUISITES:
        kb.add_prerequisite(prerequisite=id_of[x], topic=id_of[y])
    return Course(id_of=id_of, slug_of={v: k for k, v in id_of.items()})


@pytest.fixture
def snapshot_now():
    """A freshly built, uncached KB snapshot of the committed database state."""
    from curriculum.services.graph import build_snapshot, clear_local_cache

    def _get():
        clear_local_cache()
        return build_snapshot()

    return _get
