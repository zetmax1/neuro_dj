"""
V-B4 — attempts to bypass the knowledge-base service.

``bulk_create``, ``QuerySet.update``, ``bulk_update``, ``delete``, plain
``save()`` and the Django admin must not be able to break Y1-Y4, the kind
rules or the KB version. Each attempt is followed by a check that nothing was
written and that the snapshot is still the one the service produced.
"""

from __future__ import annotations

import pytest

from verification.oracle import graph as og

pytestmark = pytest.mark.django_db


def _state():
    """Everything a bypass could corrupt, as comparable plain data."""
    from curriculum.models import KnowledgeBaseVersion, Topic, TopicPrerequisite

    return (
        sorted(Topic.objects.values_list("id", "parent_id", "kind", "position", "is_archived")),
        sorted(TopicPrerequisite.objects.values_list("id", "prerequisite_id", "topic_id", "weight")),
        KnowledgeBaseVersion.current(),
    )


# ---------------------------------------------------------------------------
# QuerySet and model API
# ---------------------------------------------------------------------------

def test_v_b4_topic_bulk_create_is_refused(reference_course):
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import Topic

    before = _state()
    with pytest.raises(KBWriteError):
        Topic.objects.bulk_create([
            Topic(name="smuggled", slug="smuggled", kind="topic", parent_id=reference_course.id_of["t1"]),
        ])
    assert not Topic.objects.filter(slug="smuggled").exists()
    assert _state() == before


@pytest.mark.parametrize(
    "changes",
    [
        {"parent_id": None},
        {"kind": "course"},
        {"position": 99},
        {"is_archived": True},
    ],
    ids=["parent", "kind", "position", "is_archived"],
)
def test_v_b4_topic_queryset_update_is_refused(reference_course, changes):
    """A structural QuerySet.update() must be refused for every such field."""
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import Topic

    before = _state()
    with pytest.raises(KBWriteError):
        Topic.objects.filter(pk=reference_course.id_of["t6"]).update(**changes)
    assert _state() == before


def test_v_b4_topic_bulk_update_is_refused(reference_course):
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import Topic

    before = _state()
    node = Topic.objects.get(pk=reference_course.id_of["t6"])
    node.parent_id = reference_course.id_of["B1"]
    with pytest.raises(KBWriteError):
        Topic.objects.bulk_update([node], ["parent_id"])
    assert _state() == before


def test_v_b4_plain_save_of_a_structural_change_is_refused(reference_course):
    """Moving t6 under B1 with save() would orphan the t4 -> B3 relation."""
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import Topic

    before = _state()
    node = Topic.objects.get(pk=reference_course.id_of["t6"])
    node.parent_id = reference_course.id_of["B1"]
    with pytest.raises(KBWriteError):
        node.save()
    with pytest.raises(KBWriteError):
        node.save(update_fields=["parent"])
    assert _state() == before


def test_v_b4_non_structural_writes_stay_allowed(reference_course):
    """Renaming is not a KB change: it is allowed and does not bump the version."""
    from curriculum.models import KnowledgeBaseVersion, Topic

    version = KnowledgeBaseVersion.current()
    Topic.objects.filter(pk=reference_course.id_of["t1"]).update(name="Massivlar (yangi nom)")
    node = Topic.objects.get(pk=reference_course.id_of["t2"])
    node.description = "tahrir"
    node.save()
    assert KnowledgeBaseVersion.current() == version


def test_v_b4_topic_delete_is_refused(reference_course):
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import Topic

    before = _state()
    with pytest.raises(KBWriteError):
        Topic.objects.filter(pk=reference_course.id_of["t7"]).delete()
    with pytest.raises(KBWriteError):
        Topic.objects.get(pk=reference_course.id_of["t7"]).delete()
    assert _state() == before


def test_v_b4_prerequisite_writes_are_refused(reference_course):
    """A relation that would close a cycle must not be creatable outside the service."""
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import TopicPrerequisite

    course = reference_course
    before = _state()
    cyclic = dict(prerequisite_id=course.id_of["t8"], topic_id=course.id_of["t3"])

    with pytest.raises(KBWriteError):
        TopicPrerequisite.objects.create(**cyclic)
    with pytest.raises(KBWriteError):
        TopicPrerequisite.objects.bulk_create([TopicPrerequisite(**cyclic)])
    with pytest.raises(KBWriteError):
        TopicPrerequisite(**cyclic).save()
    with pytest.raises(KBWriteError):
        TopicPrerequisite.objects.filter(pk__gt=0).update(weight=0.5)
    with pytest.raises(KBWriteError):
        TopicPrerequisite.objects.all().delete()
    with pytest.raises(KBWriteError):
        TopicPrerequisite.objects.first().delete()
    assert _state() == before


def test_v_b4_related_manager_create_and_update_or_create_are_refused(reference_course):
    """The guarded paths of the reverse managers: create() and update_or_create()."""
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import Topic

    course = reference_course
    before = _state()
    t6 = Topic.objects.get(pk=course.id_of["t6"])

    with pytest.raises(KBWriteError):
        t6.prerequisites.create(prerequisite_id=course.id_of["t7"])
    with pytest.raises(KBWriteError):
        Topic.objects.update_or_create(slug="t6", defaults={"parent_id": course.id_of["B1"]})
    with pytest.raises(KBWriteError):
        Topic.objects.get(pk=course.id_of["course"]).children.clear()
    assert _state() == before


def test_v_b4_reverse_manager_add_cannot_move_a_node(reference_course):
    """
    ``parent.children.add(node)`` is a structural change: it must be refused,
    or at the very least validated and versioned like every other move.

    Django's related descriptors write through ``Topic._base_manager``, and
    ``Topic._meta.base_manager_name`` is unset, so that manager is a plain
    ``Manager``/``QuerySet`` without the guards installed on ``TopicQuerySet``.
    """
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import KnowledgeBaseVersion, Topic

    course = reference_course
    version = KnowledgeBaseVersion.current()
    b1 = Topic.objects.get(pk=course.id_of["B1"])
    t6 = Topic.objects.get(pk=course.id_of["t6"])

    with pytest.raises(KBWriteError):
        b1.children.add(t6)

    assert Topic.objects.get(pk=t6.pk).parent_id == course.id_of["B3"], (
        "t6 was moved out of B3 without the KB service"
    )
    assert KnowledgeBaseVersion.current() == version


def test_v_b4_reverse_manager_set_cannot_break_y2_and_the_kind_rules(reference_course):
    """
    ``t6.children.set([t3])`` makes the topic t6 the parent of the topic t3.
    That breaks two invariants at once: a topic is a leaf (3.1 / Y4), and the
    existing relation (t3, t6) now joins a node with its own ancestor (Y2).
    """
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import KnowledgeBaseVersion, Topic
    from curriculum.services.graph import build_snapshot
    from curriculum.services.kb import KBError, _check_nesting

    course = reference_course
    version = KnowledgeBaseVersion.current()
    t6 = Topic.objects.get(pk=course.id_of["t6"])
    t3 = Topic.objects.get(pk=course.id_of["t3"])

    try:
        with pytest.raises(KBWriteError):
            t6.children.set([t3])
    finally:
        moved = Topic.objects.get(pk=t3.pk).parent_id
        if moved == t6.pk:
            # Record exactly what the bypass produced before the assertion above
            # is reported, so the report can quote the resulting state.
            tree = course.oracle_tree()
            assert tree.violates_y2(t3.pk, t6.pk)
            assert t6.kind == "topic" and tree.children(t6.pk) == [t3.pk]
            with pytest.raises(KBError):
                _check_nesting(build_snapshot(version=0))
            assert KnowledgeBaseVersion.current() == version


def test_v_b4_kb_version_cannot_be_rewritten(reference_course):
    """The version counter is what every cached snapshot is keyed by (GR1)."""
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import KnowledgeBaseVersion

    before = _state()
    with pytest.raises(KBWriteError):
        KnowledgeBaseVersion.objects.filter(pk=1).update(version=1)
    with pytest.raises(KBWriteError):
        KnowledgeBaseVersion.objects.get(pk=1).save()
    assert _state() == before


def test_v_b4_kb_version_row_cannot_be_removed_or_replaced(reference_course):
    """
    Resetting the counter is as damaging as rewriting it, but
    ``KnowledgeBaseVersionQuerySet`` overrides only ``update``, so ``delete``
    and ``bulk_create`` are unguarded.
    """
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import KnowledgeBaseVersion

    before = _state()
    with pytest.raises(KBWriteError):
        KnowledgeBaseVersion.objects.filter(pk=1).delete()
    assert _state() == before, "the KB version row was removed outside the service"


def test_v_b4_removing_the_version_row_makes_get_snapshot_serve_a_stale_kb(reference_course):
    """
    The consequence of the hole above (GR1). ``current()`` falls back to 1 when
    the row is gone and ``_bump_version`` recreates it at 1, so after the next
    real KB change the cache key ``kb:snapshot:v1`` still holds the *previous*
    knowledge base and ``get_snapshot`` serves it.
    """
    from curriculum.models import KnowledgeBaseVersion
    from curriculum.services import kb
    from curriculum.services.graph import clear_local_cache, get_snapshot

    course = reference_course
    KnowledgeBaseVersion.objects.filter(pk=1).delete()   # the unguarded write
    assert KnowledgeBaseVersion.current() == 1

    clear_local_cache()
    stale = get_snapshot()                                # caches kb:snapshot:v1
    assert len(stale.edges) == 10

    kb.remove_prerequisite(
        __import__("curriculum.models", fromlist=["x"]).TopicPrerequisite.objects.get(
            prerequisite_id=course.id_of["t6"], topic_id=course.id_of["t7"]
        ).pk
    )
    clear_local_cache()
    served = get_snapshot()
    assert len(served.edges) == 9, (
        "get_snapshot served a cached snapshot of the previous knowledge base "
        f"(version {served.version}, {len(served.edges)} edges)"
    )


def test_v_b4_integrity_after_every_attempt(reference_course, snapshot_now):
    """After the bypass attempts the KB is still exactly the reference course."""
    from curriculum.kb_guard import KBWriteError
    from curriculum.models import Topic, TopicPrerequisite

    course = reference_course
    attempts = [
        lambda: Topic.objects.filter(pk=course.id_of["t4"]).update(parent_id=course.id_of["B3"]),
        lambda: TopicPrerequisite.objects.create(
            prerequisite_id=course.id_of["t8"], topic_id=course.id_of["t1"]
        ),
        lambda: Topic.objects.filter(pk=course.id_of["B3"]).delete(),
    ]
    for attempt in attempts:
        with pytest.raises(KBWriteError):
            attempt()

    snap = snapshot_now()
    tree, prereqs = course.oracle_tree(), course.oracle_prereqs()
    assert course.slug_edges(snap.edges) == __import__(
        "verification.oracle.reference", fromlist=["x"]
    ).EXPECTED_EL
    assert list(snap.order) == og.lexicographic_order(og.digraph(tree, prereqs), tree.pos())


# ---------------------------------------------------------------------------
# Django admin
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_client_su(db, client):
    from accounts.models import CustomUser

    user = CustomUser.objects.create_superuser(email="verifier@example.com", password="verify-pass-123")
    client.force_login(user)
    return client


def test_v_b4_admin_cannot_add_a_cycle(reference_course, admin_client_su):
    """The prerequisite admin must refuse (t8, t3) and write nothing."""
    from curriculum.models import TopicPrerequisite

    course = reference_course
    before = _state()
    response = admin_client_su.post(
        "/admin/curriculum/topicprerequisite/add/",
        {"prerequisite": course.id_of["t8"], "topic": course.id_of["t3"], "weight": "1.0"},
        follow=True,
    )
    assert response.status_code == 200
    assert not TopicPrerequisite.objects.filter(
        prerequisite_id=course.id_of["t8"], topic_id=course.id_of["t3"]
    ).exists()
    assert _state() == before
    messages = [m.message for m in response.context["messages"]]
    assert any("cycle" in m for m in messages), messages


def test_v_b4_admin_cannot_move_a_node_into_its_own_subtree(reference_course, admin_client_su):
    """Y1 through the admin change form."""
    from curriculum.models import Topic

    course = reference_course
    before = _state()
    b3 = Topic.objects.get(pk=course.id_of["B3"])
    response = admin_client_su.post(
        f"/admin/curriculum/topic/{b3.pk}/change/",
        {
            "name": b3.name,
            "slug": b3.slug,
            "description": "",
            "parent": course.id_of["t6"],
            "kind": "section",
            "position": b3.position,
            "pass_mark_percentage": "60.0",
            "test_question_count": "10",
            "is_unlocked": "on",
            "resources-TOTAL_FORMS": "0",
            "resources-INITIAL_FORMS": "0",
            "prerequisites-TOTAL_FORMS": "0",
            "prerequisites-INITIAL_FORMS": "0",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert Topic.objects.get(pk=b3.pk).parent_id == course.id_of["course"]
    assert _state() == before


def test_v_b4_admin_delete_archives_instead_of_breaking_references(reference_course, admin_client_su):
    """The admin delete goes through the service, so it bumps the version once."""
    from curriculum.models import KnowledgeBaseVersion, Topic

    course = reference_course
    version = KnowledgeBaseVersion.current()
    response = admin_client_su.post(
        f"/admin/curriculum/topic/{course.id_of['t7']}/delete/", {"post": "yes"}, follow=True
    )
    assert response.status_code == 200
    assert not Topic.objects.filter(pk=course.id_of["t7"]).exists()
    assert KnowledgeBaseVersion.current() == version + 1
