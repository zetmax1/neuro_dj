"""
V-B6 — the knowledge-base version counter.

Every successful change must raise it by exactly one; a rejected change must
leave it where it was. The counter is what the snapshot cache is keyed by (GR1),
so the last check follows a change through ``get_snapshot``.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _version() -> int:
    from curriculum.models import KnowledgeBaseVersion

    return KnowledgeBaseVersion.current()


def test_v_b6_every_successful_operation_bumps_by_exactly_one(reference_course):
    """create, move, position change, weight change, remove, archive, delete."""
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    course = reference_course
    relation = TopicPrerequisite.objects.get(
        prerequisite_id=course.id_of["t6"], topic_id=course.id_of["t7"]
    )
    steps = [
        ("create_node", lambda: kb.create_node(
            name="t9", slug="t9", parent=course.id_of["B2"], kind="topic")),
        ("add_prerequisite", lambda: kb.add_prerequisite(
            prerequisite=course.id_of["t3"], topic=course.id_of["t7"])),
        ("update_weight", lambda: kb.update_weight(relation.pk, 0.4)),
        ("remove_prerequisite", lambda: kb.remove_prerequisite(relation.pk)),
        ("move_node", lambda: kb.move_node(course.id_of["t2"], course.id_of["B2"])),
        ("update_node position", lambda: kb.update_node(course.id_of["t2"], position=7)),
        ("archive_node", lambda: kb.archive_node(course.id_of["t8"])),
        ("delete_node", lambda: kb.delete_node(course.id_of["t7"])),
    ]
    for label, step in steps:
        before = _version()
        step()
        assert _version() == before + 1, f"{label} did not bump the version by exactly one"


def test_v_b6_rejected_operations_leave_the_version_alone(reference_course):
    from curriculum.services import kb

    course = reference_course
    rejects = [
        ("cycle", lambda: kb.add_prerequisite(
            prerequisite=course.id_of["t8"], topic=course.id_of["t3"])),
        ("nested", lambda: kb.add_prerequisite(
            prerequisite=course.id_of["B3"], topic=course.id_of["t6"])),
        ("self", lambda: kb.add_prerequisite(
            prerequisite=course.id_of["t1"], topic=course.id_of["t1"])),
        ("duplicate", lambda: kb.add_prerequisite(
            prerequisite=course.id_of["t1"], topic=course.id_of["t3"])),
        ("move into own subtree", lambda: kb.move_node(
            course.id_of["B3"], course.id_of["t6"])),
        ("move t4 under B3", lambda: kb.move_node(
            course.id_of["t4"], course.id_of["B3"])),
        ("parent is a topic", lambda: kb.create_node(
            name="bad", slug="bad", parent=course.id_of["t1"], kind="topic")),
        ("weight out of range", lambda: kb.update_weight(
            __import__("curriculum.models", fromlist=["x"]).TopicPrerequisite.objects.first().pk, 1.5)),
    ]
    for label, step in rejects:
        before = _version()
        with pytest.raises(kb.KBError):
            step()
        assert _version() == before, f"a rejected change ({label}) changed the version"


def test_v_b6_archive_then_delete_counts_once_each(reference_course):
    """
    ``delete_node`` on a branch a test result points at archives instead (D11);
    that must still be exactly one bump, not one for the failed delete plus one
    for the archive.
    """
    from accounts.models import CustomUser
    from assessments.models import TestSessionResult
    from curriculum.models import Topic
    from curriculum.services import kb

    course = reference_course
    user = CustomUser.objects.create_user(email="learner@example.com", password="x-pass-12345")
    TestSessionResult.objects.create(
        user=user, topic_id=course.id_of["t6"], total_questions=1, earned_points=1,
        total_points=1, score_percentage=100.0, pass_mark_percentage=60.0, passed=True,
    )

    before = _version()
    outcome, count = kb.delete_node(course.id_of["B3"])
    assert outcome == "archived"
    assert count == 4  # B3, t6, t7, t8
    assert _version() == before + 1
    assert Topic.objects.filter(pk=course.id_of["t6"], is_archived=True).exists()


def test_v_b6_renaming_is_not_a_kb_change(reference_course):
    """
    Documented behaviour, not a defect: names are not part of the snapshot
    (3.2 cache note), so a rename must not bump the version.
    """
    from curriculum.services import kb

    before = _version()
    kb.update_node(reference_course.id_of["t1"], name="Massivlar va ro'yxatlar")
    assert _version() == before


def test_v_b6_the_cache_follows_the_version(reference_course):
    """GR1: after a change ``get_snapshot`` serves the new KB, not a stale entry."""
    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb
    from curriculum.services.graph import clear_local_cache, get_snapshot

    course = reference_course
    clear_local_cache()
    first = get_snapshot()
    assert len(first.edges) == 10

    version = first.version
    relation = TopicPrerequisite.objects.get(
        prerequisite_id=course.id_of["t4"], topic_id=course.id_of["B3"]
    )
    kb.remove_prerequisite(relation.pk)

    clear_local_cache()
    second = get_snapshot()
    assert second.version == version + 1
    assert len(second.edges) == 7, "the inherited t4 -> t6/t7/t8 edges should be gone"
    assert course.slug_edges(second.redundant) == set()

    # And the old entry is still addressable, i.e. nothing had to be invalidated.
    from django.core.cache import cache

    assert cache.get(f"kb:snapshot:v{version}") is not None


def test_v_b6_archiving_removes_a_node_from_the_knowledge_base(reference_course):
    """An archived subtree leaves G_L, and the relations through it stop inheriting."""
    from curriculum.services import kb
    from curriculum.services.graph import clear_local_cache, get_snapshot

    course = reference_course
    kb.archive_node(course.id_of["t6"])
    clear_local_cache()
    snap = get_snapshot()

    assert course.id_of["t6"] not in snap.order
    assert course.slug_edges(snap.edges) == {
        ("t1", "t3"), ("t1", "t5"), ("t2", "t4"), ("t4", "t7"), ("t4", "t8"),
    }
    assert snap.leaves_of(course.id_of["B3"]) == frozenset(course.ids(["t7", "t8"]))


def test_v_b6_a_snapshot_is_not_cached_when_the_version_moved_while_reading(reference_course):
    """
    GR1: the version is read before and after the rows, and a snapshot whose two
    reads disagree must not be written to the cache under either key.
    """
    from django.core.cache import cache

    from curriculum.models import KnowledgeBaseVersion
    from curriculum.services import graph as graph_service

    base = KnowledgeBaseVersion.current()
    seen: list[int] = []

    def moving_version() -> int:
        seen.append(base + len(seen) + 1)  # every read reports a newer version
        return seen[-1]

    cache.clear()
    original = KnowledgeBaseVersion.current
    try:
        KnowledgeBaseVersion.current = staticmethod(moving_version)
        snapshot = graph_service._build_committed(base)
    finally:
        KnowledgeBaseVersion.current = original

    assert snapshot is not None
    for version in set(seen) | {base}:
        assert cache.get(f"kb:snapshot:v{version}") is None, (
            f"a snapshot was cached under v{version} although the version moved while reading"
        )


def test_v_b6_update_weight_on_a_missing_relation_is_not_a_kb_error(reference_course):
    """
    Observation for stage 6, not a V-B failure: ``update_weight`` and
    ``create_node`` raise raw database/ORM errors instead of ``KBError`` for a
    missing relation and a duplicate slug, so those paths cannot become a 400
    without extra handling in the view layer.
    """
    from django.db import IntegrityError, transaction

    from curriculum.models import TopicPrerequisite
    from curriculum.services import kb

    with pytest.raises(TopicPrerequisite.DoesNotExist):
        kb.update_weight(10**9, 0.5)

    with pytest.raises(IntegrityError), transaction.atomic():
        kb.create_node(name="duplicate slug", slug="t1", parent=reference_course.id_of["B1"], kind="topic")


def test_v_b6_updated_at_tracks_the_last_kb_change(reference_course):
    """
    ``KnowledgeBaseVersion.updated_at`` is declared ``auto_now=True``, but
    ``_bump_version`` writes through ``QuerySet.update()``, which does not run
    ``auto_now``. The timestamp therefore stays at the row's creation time and
    never names the last KB change.
    """
    from curriculum.models import KnowledgeBaseVersion
    from curriculum.services import kb

    before = KnowledgeBaseVersion.objects.get(pk=1).updated_at
    kb.create_node(name="t9", slug="t9", parent=reference_course.id_of["B2"], kind="topic")
    after = KnowledgeBaseVersion.objects.get(pk=1)

    assert after.version == KnowledgeBaseVersion.current()
    assert after.updated_at > before, (
        f"updated_at did not move with the version bump (still {after.updated_at})"
    )
