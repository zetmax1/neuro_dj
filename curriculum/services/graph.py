"""
curriculum/services/graph.py — the knowledge base as an immutable snapshot.

A ``KBSnapshot`` holds everything chapter II derives from the tree and E_P:
pos (D4), Leaves, G_L with weights, the Algorithm 2.2 order and lev, Pre/Succ,
Desc* bitsets, redundant edges and κ. It is computed by ``neuro_model.graph``
and cached under the KB version (GR1): a KB change bumps the version, so stale
entries are never read and nothing has to be invalidated. When Redis is down
the LocMem fallback or a rebuild is used (DJANGO_REDIS_IGNORE_EXCEPTIONS).

Only active (non-archived) nodes are part of the knowledge base. Names are not
cached: renaming a node does not change the KB, so views read names from the DB.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from django.apps import apps
from django.conf import settings
from django.core.cache import cache

from curriculum.models import KnowledgeBaseVersion, Topic, TopicKind, TopicPrerequisite
from neuro_model import graph as g

logger = logging.getLogger(__name__)

Edge = tuple[int, int]
CACHE_TIMEOUT_SECONDS = 24 * 3600


@dataclass(frozen=True)
class KBSnapshot:
    version: int
    tree: g.Tree
    pos: dict[int, int]
    depth: dict[int, int]
    leaf_sets: dict[int, frozenset[int]]
    prerequisites: tuple[g.Prerequisite, ...]
    edges: dict[Edge, g.LeafEdge]
    order: tuple[int, ...]
    lev: dict[int, int]
    pre: dict[int, tuple[int, ...]]
    succ: dict[int, tuple[int, ...]]
    desc: dict[int, int]
    redundant: tuple[Edge, ...]
    conflicts: tuple[Edge, ...]

    # --- tree -------------------------------------------------------------
    def __contains__(self, node: int) -> bool:
        return node in self.tree.parent

    def kind(self, node: int) -> str:
        return self.tree.kind[node]

    def root_of(self, node: int) -> int:
        chain = g.ancestors(self.tree, node)
        return chain[-1] if chain else node

    def leaves_of(self, node: int) -> frozenset[int]:
        """Leaves(n); empty for unknown or archived nodes."""
        return self.leaf_sets.get(node, frozenset())

    def topics_in_programme_order(self, nodes: Iterable[int] | None = None) -> list[int]:
        chosen = self.tree.parent.keys() if nodes is None else nodes
        return sorted((n for n in chosen if n in self.pos), key=lambda n: (self.pos[n], n))

    # --- G_L --------------------------------------------------------------
    @property
    def topics(self) -> tuple[int, ...]:
        return self.order

    @property
    def kappa(self) -> int:
        return len(self.conflicts)

    def descendants(self, topic: int) -> list[int]:
        """Desc*(v) in topological order."""
        return g.bitset_members(self.desc.get(topic, 0), list(self.order))


def build_snapshot(version: int | None = None) -> KBSnapshot:
    """Compute the snapshot from the database (no cache). Raises g.CycleError."""
    if version is None:
        version = KnowledgeBaseVersion.current()
    rows = list(
        Topic.objects.filter(is_archived=False)
        .values_list("id", "parent_id", "kind", "position")
    )
    # Archiving covers whole subtrees; drop any node whose ancestor is archived
    # anyway, so the forest is always rooted.
    parent_of = {pk: parent for pk, parent, _, _ in rows}
    active = set(parent_of)
    changed = True
    while changed:
        orphans = {pk for pk in active if parent_of[pk] is not None and parent_of[pk] not in active}
        active -= orphans
        changed = bool(orphans)
    rows = [row for row in rows if row[0] in active]
    tree = g.Tree(
        parent={pk: parent for pk, parent, _, _ in rows},
        kind={pk: kind for pk, _, kind, _ in rows},
        position={pk: position for pk, _, _, position in rows},
    )
    prerequisites = tuple(
        g.Prerequisite(id=pk, source=x, target=y, weight=w)
        for pk, x, y, w in TopicPrerequisite.objects.order_by("id").values_list(
            "id", "prerequisite_id", "topic_id", "weight",
        )
        if x in active and y in active
    )
    return snapshot_from(version, tree, prerequisites)


def snapshot_from(version: int, tree: g.Tree, prerequisites: tuple[g.Prerequisite, ...]) -> KBSnapshot:
    pos = g.preorder_positions(tree)
    leaf_sets = g.leaves(tree)
    edges = g.expand(prerequisites, leaf_sets)
    topics = [n for n, k in tree.kind.items() if k == TopicKind.TOPIC]
    order, lev = g.topological_order(topics, edges, pos)
    succ_lists = g.successors(order, edges)
    pre_lists: dict[int, list[int]] = {t: [] for t in order}
    for a, b in edges:
        pre_lists[b].append(a)
    rank = {t: i for i, t in enumerate(order)}
    succ = {t: tuple(sorted(ws, key=rank.get)) for t, ws in succ_lists.items()}
    pre = {t: tuple(sorted(us, key=rank.get)) for t, us in pre_lists.items()}
    desc = g.descendant_bitsets(order, succ)
    return KBSnapshot(
        version=version,
        tree=tree,
        pos=pos,
        depth=g.depths(tree),
        leaf_sets=leaf_sets,
        prerequisites=prerequisites,
        edges=edges,
        order=tuple(order),
        lev=lev,
        pre=pre,
        succ=succ,
        desc=desc,
        redundant=tuple(g.redundant_edges(order, succ, desc)),
        conflicts=tuple(g.order_conflicts(edges, pos)),
    )


# ---------------------------------------------------------------------------
# Version-keyed cache
# ---------------------------------------------------------------------------

_local = threading.local()


def _cache_key(version: int) -> str:
    return f"kb:snapshot:v{version}"


def clear_local_cache() -> None:
    """Forget the per-thread copy (tests reset the database between cases)."""
    _local.snapshot = None


def get_snapshot() -> KBSnapshot:
    """
    The snapshot of the current committed KB version.

    Never call this inside a KB write transaction: such a snapshot would see
    uncommitted rows. The KB service uses ``build_snapshot`` instead.
    """
    version = KnowledgeBaseVersion.current()
    local = getattr(_local, "snapshot", None)
    if local is not None and local.version == version:
        return local

    snapshot = cache.get(_cache_key(version))
    if not isinstance(snapshot, KBSnapshot) or snapshot.version != version:
        snapshot = _build_committed(version)
    _local.snapshot = snapshot
    return snapshot


def _build_committed(version: int) -> KBSnapshot:
    # The version is read before and after the rows: every KB change bumps it
    # in the same transaction, so equal values mean the rows belong to it.
    for _ in range(3):
        snapshot = build_snapshot(version)
        after = KnowledgeBaseVersion.current()
        if after == version:
            cache.set(_cache_key(version), snapshot, CACHE_TIMEOUT_SECONDS)
            return snapshot
        version = after
    return build_snapshot(version)


# ---------------------------------------------------------------------------
# Legacy unlock rule (D9) — replaced by the readiness service in stage 4.
# ---------------------------------------------------------------------------

def is_unlocked_dag(user: Any, topic: Topic) -> bool:
    """
    Legacy node-level unlock check kept until stage 4 (TY1–TY6).

    If the node has direct prerequisite rows, all of them need the legacy
    mastery threshold; otherwise roots are open and other nodes follow their
    parent. Not a chapter II rule (no G_L, no hysteresis).
    """
    raw_threshold = getattr(settings, "MASTERY_THRESHOLD", 0.70)
    threshold = raw_threshold / 100.0 if raw_threshold > 1.0 else float(raw_threshold)

    prereq_qs = TopicPrerequisite.objects.filter(topic=topic, prerequisite__is_archived=False)
    prereq_count = prereq_qs.count()

    if prereq_count > 0:
        if user is None or not getattr(user, "is_authenticated", False):
            return False

        UserKnowledgeState = apps.get_model("assessments", "UserKnowledgeState")
        prereq_ids = list(prereq_qs.values_list("prerequisite_id", flat=True))

        mastered_count = UserKnowledgeState.objects.filter(
            user=user,
            topic_id__in=prereq_ids,
            mastery_percentage__gte=threshold,
        ).count()

        return mastered_count == prereq_count

    if topic.parent_id is None:
        return True

    if user is None or not getattr(user, "is_authenticated", False):
        return True

    UserKnowledgeState = apps.get_model("assessments", "UserKnowledgeState")
    parent_state = UserKnowledgeState.objects.filter(
        user=user,
        topic_id=topic.parent_id,
    ).first()

    if parent_state:
        return parent_state.mastery_percentage >= threshold
    return True
