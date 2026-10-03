"""
curriculum/services/kb.py — the only writer of the knowledge base (BB5–BB9).

Every operation runs in one transaction that
1. takes ``pg_advisory_xact_lock(KB_LOCK_KEY)``, so KB changes are serialised;
2. re-reads the KB from the database (never from the cache);
3. validates the result: Y1 (tree), Y2 (no relation between a node and its
   ancestor), Y3 (G_L acyclic; Algorithm 2.1 for a new relation, Algorithm 2.2
   after tree changes), plus the kind rules of 3.1;
4. bumps ``KnowledgeBaseVersion.version`` by exactly one.
Any violation raises ``KBError`` and rolls everything back, version included.

API views, the admin, imports and seed commands call these functions; the
model guards (curriculum.kb_guard) refuse structural writes from anywhere else.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from django.db import IntegrityError, connection, transaction
from django.db.models import F, Max, ProtectedError, RestrictedError
from django.utils import timezone

from curriculum.kb_guard import KBError, kb_write
from curriculum.models import (
    STRUCTURAL_FIELDS,
    KnowledgeBaseVersion,
    Topic,
    TopicKind,
    TopicPrerequisite,
)
from curriculum.services.graph import KBSnapshot, build_snapshot
from neuro_model import graph as g

# Single-key advisory lock space; the answer ledger uses the two-key space.
KB_LOCK_KEY: int = 0x4E4C5F4B42  # "NL_KB"

# Topic attributes the instructor may edit (structure is handled separately).
EDITABLE_FIELDS = frozenset({
    "name", "slug", "description", "instructor", "pass_mark_percentage",
    "test_question_count", "is_unlocked",
})


# ``KBError`` is defined in curriculum.kb_guard (curriculum.models raises it as
# well) and re-exported here: ``kb.KBError`` stays the name callers import.
__all__ = [
    "KBError",
    "add_prerequisite",
    "archive_node",
    "create_node",
    "delete_node",
    "ensure_node",
    "ensure_prerequisite",
    "move_node",
    "remove_prerequisite",
    "update_node",
    "update_weight",
]


# ---------------------------------------------------------------------------
# Transaction, lock, version
# ---------------------------------------------------------------------------

def _lock() -> None:
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [KB_LOCK_KEY])


def _bump_version() -> int:
    # The row is an invariant (D31): it is never recreated here, because a
    # counter that restarts at 1 would make a cached snapshot of the previous
    # knowledge base look current. ``updated_at`` is set explicitly —
    # ``auto_now`` does not fire on ``QuerySet.update()`` (V-B6a).
    rows = KnowledgeBaseVersion.objects.filter(pk=1).update(
        version=F("version") + 1,
        updated_at=timezone.now(),
    )
    if rows != 1:
        raise KBError("version_missing", KnowledgeBaseVersion._MISSING)
    return KnowledgeBaseVersion.current()


@contextmanager
def _kb_change() -> Iterator[None]:
    """One serialised, validated, versioned KB change."""
    with transaction.atomic(), kb_write():
        _lock()
        yield
        _bump_version()


def _fresh() -> KBSnapshot:
    """The KB as it stands inside the current transaction; raises KBError on a cycle."""
    try:
        return build_snapshot(version=0)
    except g.CycleError as exc:
        raise KBError(
            "cycle",
            "The change would make the prerequisite graph cyclic (Y3).",
            chain=exc.remaining,
        ) from exc


def _check_nesting(snapshot: KBSnapshot) -> None:
    """Y2 for every active relation (needed after tree changes)."""
    for rel in snapshot.prerequisites:
        if g.is_nested(snapshot.tree, rel.source, rel.target):
            raise KBError(
                "nested",
                "A prerequisite may not join a node and its ancestor or descendant (Y2).",
                edge=(rel.source, rel.target),
            )


def _active(pk: int, *, lock: bool = False) -> Topic:
    qs = Topic.objects.select_for_update() if lock else Topic.objects
    try:
        return qs.get(pk=pk, is_archived=False)
    except Topic.DoesNotExist:
        raise KBError("archived", f"Node {pk} does not exist or is archived.") from None


def _has_questions(node: Topic) -> bool:
    return node.questions.exists()


def _validate_tree_rules(node: Topic) -> None:
    """Kinds of 3.1: course = root; topics are leaves; sections and courses hold no questions."""
    if (node.kind == TopicKind.COURSE) != (node.parent_id is None):
        raise KBError("kind", "Courses are exactly the roots of the tree.")
    if node.parent_id is not None:
        parent = _active(node.parent_id)
        if parent.kind == TopicKind.TOPIC:
            raise KBError(
                "parent_is_topic",
                f"'{parent.name}' is a topic; topics are leaves. Change it to a section first.",
            )
    if node.kind == TopicKind.TOPIC and node.pk and node.children.filter(is_archived=False).exists():
        raise KBError("has_children", "A topic cannot have children; use a section.")
    if node.kind != TopicKind.TOPIC and node.pk and _has_questions(node):
        raise KBError("has_questions", "Only topics hold questions (Y4); move the questions first.")


def _check_slug_free(slug: str, *, exclude_pk: int | None = None) -> None:
    """``slug`` is unique in the database; report the clash as a KBError (D32)."""
    clash = Topic.objects.filter(slug=slug)
    if exclude_pk is not None:
        clash = clash.exclude(pk=exclude_pk)
    if clash.exists():
        raise KBError("duplicate_slug", f"A node with the slug {slug!r} already exists.")


def _next_position(parent_id: int | None) -> int:
    top = Topic.objects.filter(parent_id=parent_id).aggregate(p=Max("position"))["p"]
    return 0 if top is None else top + 1


# ---------------------------------------------------------------------------
# Tree operations
# ---------------------------------------------------------------------------

def create_node(
    *,
    name: str,
    slug: str,
    parent: Topic | int | None = None,
    kind: str | None = None,
    position: int | None = None,
    **attrs: Any,
) -> Topic:
    """Add a node. Default kind: course for a root, topic otherwise."""
    unknown = set(attrs) - EDITABLE_FIELDS
    if unknown:
        raise TypeError(f"Unknown topic fields: {sorted(unknown)}")
    parent_id = getattr(parent, "pk", parent)
    kind = kind or (TopicKind.COURSE if parent_id is None else TopicKind.TOPIC)
    if kind not in TopicKind.values:
        raise KBError("kind", f"Unknown kind {kind!r}.")
    with _kb_change():
        # Serialised by the KB lock, so the check cannot be raced; the
        # IntegrityError below still covers backends without advisory locks.
        _check_slug_free(slug)
        if parent_id is not None:
            _active(parent_id, lock=True)
        node = Topic(
            name=name,
            slug=slug,
            parent_id=parent_id,
            kind=kind,
            position=_next_position(parent_id) if position is None else position,
            **attrs,
        )
        _validate_tree_rules(node)
        try:
            with transaction.atomic():
                node.save()
        except IntegrityError as exc:
            raise KBError("duplicate_slug", f"A node with the slug {slug!r} already exists.") from exc
        _fresh()  # a new topic inherits its ancestors' relations: Algorithm 2.2
    return node


def update_node(node: Topic | int, **changes: Any) -> Topic:
    """
    Edit a node. Structural changes (``parent``, ``kind``, ``position``) are
    validated (Y1–Y3, kinds) and bump the KB version; other fields do not.
    """
    pk = getattr(node, "pk", node)
    if "parent" in changes:
        parent = changes.pop("parent")
        changes["parent_id"] = getattr(parent, "pk", parent)
    allowed = EDITABLE_FIELDS | {"parent_id", "kind", "position"}
    unknown = set(changes) - allowed
    if unknown:
        raise TypeError(f"Unknown topic fields: {sorted(unknown)}")

    with transaction.atomic(), kb_write():
        _lock()
        current = _active(pk, lock=True)
        if "slug" in changes and changes["slug"] != current.slug:
            _check_slug_free(changes["slug"], exclude_pk=pk)
        structural = {
            k: v for k, v in changes.items()
            if k in STRUCTURAL_FIELDS and getattr(current, k) != v
        }
        for field, value in changes.items():
            setattr(current, field, value)
        if structural:
            if "parent_id" in structural and current.parent_id is not None:
                new_parent = _active(current.parent_id, lock=True)
                # Y1: the new parent is neither the node nor one of its descendants.
                if Topic.objects.ancestors(new_parent.pk, include_self=True).filter(pk=current.pk).exists():
                    raise KBError("move_into_subtree", "A node cannot be moved into its own subtree (Y1).")
            _validate_tree_rules(current)
        current.save()
        if structural:
            snapshot = _fresh()  # Algorithm 2.2 on the changed tree
            _check_nesting(snapshot)
            _bump_version()
    return current


def move_node(node: Topic | int, new_parent: Topic | int, position: int | None = None) -> Topic:
    """Move a node under another parent (Y1, then Y2/Y3 on the result)."""
    parent_id = getattr(new_parent, "pk", new_parent)
    changes: dict[str, Any] = {"parent_id": parent_id}
    changes["position"] = _next_position(parent_id) if position is None else position
    return update_node(node, **changes)


def archive_node(node: Topic | int) -> int:
    """Archive a node with its whole subtree; returns the number of archived nodes."""
    pk = getattr(node, "pk", node)
    with _kb_change():
        _active(pk, lock=True)
        subtree = list(Topic.objects.descendants(pk, include_self=True).values_list("pk", flat=True))
        count = Topic.objects.filter(pk__in=subtree, is_archived=False).update(is_archived=True)
        _fresh()
    return count


def delete_node(node: Topic | int) -> tuple[str, int]:
    """
    Delete a node and its subtree. If answers or test results reference the
    subtree (PROTECT, D11), archive it instead. Returns ("deleted" | "archived", n).
    """
    pk = getattr(node, "pk", node)
    with transaction.atomic(), kb_write():
        _lock()
        current = _active(pk, lock=True)
        # Already-archived descendants are not part of the knowledge base, so
        # they are not counted (D32).
        size = Topic.objects.descendants(pk, include_self=True).filter(is_archived=False).count()
        try:
            with transaction.atomic():
                current.delete()
        except (ProtectedError, RestrictedError):
            return "archived", archive_node(pk)
        _fresh()
        _bump_version()
    return "deleted", size


# ---------------------------------------------------------------------------
# Prerequisite operations
# ---------------------------------------------------------------------------

def _check_weight(weight: float) -> float:
    try:
        weight = float(weight)
    except (TypeError, ValueError):
        raise KBError("weight", "The weight ω must be a number in (0, 1].") from None
    if not 0.0 < weight <= 1.0:
        raise KBError("weight", "The weight ω must be in (0, 1].")
    return weight


def add_prerequisite(*, prerequisite: Topic | int, topic: Topic | int, weight: float = 1.0) -> TopicPrerequisite:
    """
    Algorithm 2.1: add (x, y) — x must be mastered before y.

    1. Y2: x ≠ y, x ∉ Anc(y), y ∉ Anc(x)  → reason "self" / "nested".
    2. BFS from Leaves(y); reaching Leaves(x) means a cycle → reason "cycle"
       with the chain (e.g. [t3, t6, t8] for the new edge t8 → t3).
    """
    x = getattr(prerequisite, "pk", prerequisite)
    y = getattr(topic, "pk", topic)
    weight = _check_weight(weight)
    if x == y:
        raise KBError("self", "A node cannot be its own prerequisite.", edge=(x, y))
    with _kb_change():
        _active(x, lock=True)
        _active(y, lock=True)
        if TopicPrerequisite.objects.filter(prerequisite_id=x, topic_id=y).exists():
            raise KBError("duplicate", "This prerequisite already exists.", edge=(x, y))
        snapshot = _fresh()
        if g.is_nested(snapshot.tree, x, y):
            raise KBError(
                "nested",
                "A prerequisite may not join a node and its ancestor or descendant (Y2).",
                edge=(x, y),
            )
        chain = g.find_cycle_chain(snapshot.tree, snapshot.prerequisites, snapshot.leaf_sets, x, y)
        if chain is not None:
            raise KBError(
                "cycle",
                "The prerequisite would close a cycle in the topic graph (Y3).",
                chain=chain,
                edge=(x, y),
            )
        relation = TopicPrerequisite.objects.create(prerequisite_id=x, topic_id=y, weight=weight)
        _fresh()  # defence in depth: Algorithm 2.2 must agree with Algorithm 2.1
    return relation


def update_weight(relation: TopicPrerequisite | int, weight: float) -> TopicPrerequisite:
    pk = getattr(relation, "pk", relation)
    weight = _check_weight(weight)
    with _kb_change():
        try:
            current = TopicPrerequisite.objects.select_for_update().get(pk=pk)
        except TopicPrerequisite.DoesNotExist:
            raise KBError("not_found", f"Prerequisite {pk} does not exist.") from None
        current.weight = weight
        current.save(update_fields=["weight"])
    return current


def remove_prerequisite(relation: TopicPrerequisite | int) -> None:
    pk = getattr(relation, "pk", relation)
    with _kb_change():
        deleted, _ = TopicPrerequisite.objects.filter(pk=pk).delete()
        if not deleted:
            raise KBError("not_found", f"Prerequisite {pk} does not exist.")


# ---------------------------------------------------------------------------
# Helpers for seed commands
# ---------------------------------------------------------------------------

def ensure_node(*, slug: str, name: str, parent: Topic | None = None, kind: str | None = None, **attrs: Any) -> Topic:
    """Idempotent create for seeds: return the node with this slug or create it."""
    existing = Topic.objects.filter(slug=slug).first()
    if existing is not None:
        return existing
    return create_node(name=name, slug=slug, parent=parent, kind=kind, **attrs)


def ensure_prerequisite(*, prerequisite: Topic, topic: Topic, weight: float = 1.0) -> TopicPrerequisite:
    existing = TopicPrerequisite.objects.filter(prerequisite=prerequisite, topic=topic).first()
    return existing or add_prerequisite(prerequisite=prerequisite, topic=topic, weight=weight)
