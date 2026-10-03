"""
Stage 2: the knowledge base end to end (BB1–BB10, GR1–GR3, Y1–Y4).

The reference course of NEUROLEARN_REMEDIATION.md section 4 is built through
the instructor API, then checked against the expected values; rejected changes
must answer 400 with a reason (and a chain for cycles) and leave the KB
version unchanged. The model guards must refuse every bypass.
"""

from __future__ import annotations

import io

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from assessments.models import Choice, Question
from curriculum.kb_guard import KBWriteError
from curriculum.models import KnowledgeBaseVersion, Topic, TopicKind, TopicPrerequisite
from curriculum.services import kb
from curriculum.services.graph import get_snapshot
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()


@pytest.fixture
def teacher():
    user = User.objects.create_user(email="kb.teacher@example.org", password=None)
    user.groups.add(Group.objects.get_or_create(name="Instructor")[0])
    return user


@pytest.fixture
def api(teacher):
    client = APIClient()
    client.force_authenticate(teacher)
    return client


def version() -> int:
    return KnowledgeBaseVersion.current()


class Reference:
    """Course “Ma’lumotlar tuzilmalari” built through the API."""

    def __init__(self, api):
        self.api = api
        self.ids: dict[str, int] = {}
        self.node("C", None, "course")
        for b, (section, topics) in enumerate({"B1": (1, 2, 3), "B2": (4, 5), "B3": (6, 7, 8)}.items()):
            self.node(section, "C", "section", position=b)
            for slot, n in enumerate(topics):
                self.node(f"t{n}", section, "topic", position=slot)
        self.names = {v: k for k, v in self.ids.items()}
        for x, y in [("t1", "t3"), ("t1", "t5"), ("t2", "t4"), ("t3", "t6"),
                     ("t5", "t6"), ("t6", "t7"), ("t6", "t8"), ("t4", "B3")]:
            response = self.add(x, y)
            assert response.status_code == 201, response.json()

    def node(self, name, parent, kind, position=0):
        body = {"name": name, "slug": f"ref-{name.lower()}", "kind": kind, "position": position}
        if parent:
            body["parent"] = self.ids[parent]
        response = self.api.post("/api/curriculum/instructor/topics/", body, format="json")
        assert response.status_code == 201, response.json()
        self.ids[name] = response.json()["id"]

    def add(self, x, y, **extra):
        return self.api.post(
            "/api/curriculum/instructor/prerequisites/",
            {"prerequisite": self.ids[x], "topic": self.ids[y], **extra},
            format="json",
        )

    def named(self, ids):
        return [self.names[i] for i in ids]


@pytest.fixture
def ref(api):
    return Reference(api)


# ---------------------------------------------------------------------------
# Section 4 reference values
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_reference_graph_values(ref, api):
    leaf = api.get("/api/curriculum/instructor/prerequisites/?expand=leaf").json()
    assert len(leaf) == 10
    assert {(ref.names[e["source"]], ref.names[e["target"]]) for e in leaf if e["inherited"]} == {
        ("t4", "t6"), ("t4", "t7"), ("t4", "t8"),
    }
    t4_t7 = next(e for e in leaf if (ref.names[e["source"]], ref.names[e["target"]]) == ("t4", "t7"))
    relation_t4_b3 = TopicPrerequisite.objects.get(prerequisite_id=ref.ids["t4"], topic_id=ref.ids["B3"])
    assert t4_t7["via"] == [relation_t4_b3.pk]

    snapshot = get_snapshot()
    assert ref.named(snapshot.order) == ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]
    assert [snapshot.lev[ref.ids[f"t{i}"]] for i in range(1, 9)] == [0, 0, 1, 1, 1, 2, 3, 3]
    assert [len(snapshot.descendants(ref.ids[f"t{i}"])) for i in range(1, 9)] == [5, 4, 3, 3, 3, 2, 0, 0]

    warnings = api.get("/api/curriculum/instructor/kb/warnings/").json()
    assert {(ref.names[w["source"]], ref.names[w["target"]]) for w in warnings["redundant_edges"]} == {
        ("t4", "t7"), ("t4", "t8"),
    }
    assert warnings["kappa"] == 0 and warnings["order_conflicts"] == []
    assert warnings["kb_version"] == version()

    graph = api.get("/api/curriculum/prerequisite-graph/").json()
    lev = {ref.names[int(n["id"])]: n["data"]["lev"] for n in graph["nodes"]}
    assert lev["t6"] == 2 and lev["B3"] is None
    assert "warnings" in graph  # shown to instructors


@pytest.mark.django_db
def test_cycle_t8_to_t3_is_rejected_with_its_chain(ref):
    before = version()
    response = ref.add("t8", "t3")
    assert response.status_code == 400
    body = response.json()
    assert body["reason"] == "cycle"
    assert ref.named(body["chain"]) == ["t3", "t6", "t8"]
    assert body["chain_names"] == ["t3", "t6", "t8"]
    assert body["edge"] == [ref.ids["t8"], ref.ids["t3"]]
    assert version() == before


@pytest.mark.django_db
def test_b3_to_t6_violates_y2(ref):
    before = version()
    response = ref.add("B3", "t6")
    assert (response.status_code, response.json()["reason"]) == (400, "nested")
    assert version() == before


@pytest.mark.django_db
def test_moving_t4_into_b3_violates_y2(ref, api):
    before = version()
    response = api.patch(
        f"/api/curriculum/instructor/topics/{ref.ids['t4']}/", {"parent": ref.ids["B3"]}, format="json",
    )
    assert (response.status_code, response.json()["reason"]) == (400, "nested")
    assert Topic.objects.get(pk=ref.ids["t4"]).parent_id == ref.ids["B2"]
    assert version() == before


@pytest.mark.django_db
def test_backward_edge_counts_in_kappa(ref, api):
    assert ref.add("t5", "t4").status_code == 201  # pos(t4) < pos(t5)
    warnings = api.get("/api/curriculum/instructor/kb/warnings/").json()
    assert warnings["kappa"] == 1
    assert [(ref.names[w["source"]], ref.names[w["target"]]) for w in warnings["order_conflicts"]] == [("t5", "t4")]


@pytest.mark.django_db
def test_adding_a_topic_under_a_section_with_relations_is_checked(ref, api):
    """A new topic inherits its ancestors' relations; Algorithm 2.2 runs on create."""
    response = api.post(
        "/api/curriculum/instructor/topics/",
        {"name": "t9", "slug": "ref-t9", "parent": ref.ids["B3"]},
        format="json",
    )
    assert response.status_code == 201
    t9 = response.json()["id"]
    assert ref.ids["t4"] in get_snapshot().pre[t9]


# ---------------------------------------------------------------------------
# Audit probes and versions
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_audit_probes(api):
    course = make_course("Probe")
    a = make_section("A", course)
    b = make_section("B", course)
    a1 = make_topic("a1", a)
    b1 = make_topic("b1", b)
    url = "/api/curriculum/instructor/prerequisites/"

    # (1) `B requires A` and `a1 requires b1` → cycle.
    assert api.post(url, {"prerequisite": a.pk, "topic": b.pk}, format="json").status_code == 201
    response = api.post(url, {"prerequisite": b1.pk, "topic": a1.pk}, format="json")
    assert (response.status_code, response.json()["reason"]) == (400, "cycle")
    assert response.json()["chain"] == [a1.pk, b1.pk]

    # (2) an ancestor → descendant prerequisite is rejected.
    response = api.post(url, {"prerequisite": a.pk, "topic": a1.pk}, format="json")
    assert (response.status_code, response.json()["reason"]) == (400, "nested")


@pytest.mark.django_db
def test_every_successful_change_bumps_the_version_by_one(api):
    course = make_course("V")
    t1 = make_topic("v1", course)
    t2 = make_topic("v2", course)
    url = "/api/curriculum/instructor/prerequisites/"

    before = version()
    created = api.post(url, {"prerequisite": t1.pk, "topic": t2.pk, "weight": 0.6}, format="json")
    assert created.status_code == 201 and version() == before + 1
    rel = created.json()["id"]

    for bad in (0, 1.5, "x"):
        response = api.patch(f"{url}{rel}/", {"weight": bad}, format="json")
        assert response.status_code == 400, bad
    assert version() == before + 1
    assert api.post(url, {"prerequisite": t1.pk, "topic": t2.pk}, format="json").json()["reason"] == "duplicate"
    assert api.post(url, {"prerequisite": t1.pk, "topic": t1.pk}, format="json").json()["reason"] == "self"
    assert version() == before + 1

    assert api.patch(f"{url}{rel}/", {"weight": 0.25}, format="json").json()["weight"] == 0.25
    assert version() == before + 2
    assert get_snapshot().edges[(t1.pk, t2.pk)].weight == 0.25
    assert api.delete(f"{url}{rel}/").status_code == 204
    assert version() == before + 3
    assert (t1.pk, t2.pk) not in get_snapshot().edges


@pytest.mark.django_db
def test_archived_nodes_leave_the_knowledge_base(api):
    course = make_course("Arch")
    sec = make_section("S", course)
    gone = make_topic("gone", sec)
    kept = make_topic("kept", course)
    kb.add_prerequisite(prerequisite=gone, topic=kept)
    assert (gone.pk, kept.pk) in get_snapshot().edges
    kb.archive_node(sec)
    snapshot = get_snapshot()
    assert gone.pk not in snapshot and sec.pk not in snapshot
    assert snapshot.edges == {}
    response = api.post(
        "/api/curriculum/instructor/prerequisites/", {"prerequisite": gone.pk, "topic": kept.pk}, format="json",
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Guards (V-B4)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_structural_writes_outside_the_service_are_refused():
    course = make_course("G")
    sec = make_section("S", course)
    a = make_topic("a", sec)
    b = make_topic("b", course)
    rel = kb.add_prerequisite(prerequisite=a, topic=b)
    before = version()

    attempts = [
        lambda: Topic.objects.create(name="x", slug="x", parent=course, kind=TopicKind.TOPIC),
        lambda: Topic.objects.bulk_create([Topic(name="y", slug="y", parent=course, kind=TopicKind.TOPIC)]),
        lambda: Topic.objects.filter(pk=a.pk).update(parent=course),
        lambda: Topic.objects.filter(pk=a.pk).update(kind=TopicKind.SECTION),
        lambda: Topic.objects.filter(pk=a.pk).update(position=9),
        lambda: Topic.objects.filter(pk=sec.pk).update(is_archived=True),
        lambda: Topic.objects.bulk_update([a], ["parent"]),
        lambda: Topic.objects.filter(pk=b.pk).delete(),
        lambda: Topic.objects.get(pk=b.pk).delete(),
        lambda: TopicPrerequisite.objects.create(prerequisite=b, topic=a),
        lambda: TopicPrerequisite.objects.bulk_create([TopicPrerequisite(prerequisite=b, topic=a)]),
        lambda: TopicPrerequisite.objects.filter(pk=rel.pk).update(weight=0.5),
        lambda: TopicPrerequisite.objects.filter(pk=rel.pk).delete(),
        lambda: TopicPrerequisite.objects.get(pk=rel.pk).delete(),
        lambda: KnowledgeBaseVersion.objects.filter(pk=1).update(version=0),
        # D30: the reverse manager and _base_manager used to slip past the guard.
        lambda: course.children.add(a),
        lambda: course.children.set([a]),
        lambda: course.children.remove(sec),
        lambda: course.children.clear(),
        lambda: Topic._base_manager.filter(pk=a.pk).update(parent_id=course.pk),
        lambda: Topic._base_manager.bulk_create([Topic(name="z", slug="z", parent=course, kind=TopicKind.TOPIC)]),
        lambda: TopicPrerequisite._base_manager.all().delete(),
        # D31: the version row may not be removed either.
        lambda: KnowledgeBaseVersion.objects.filter(pk=1).delete(),
    ]
    for attempt in attempts:
        with pytest.raises(KBWriteError):
            attempt()

    moved = Topic.objects.get(pk=a.pk)
    moved.parent = course
    with pytest.raises(KBWriteError):
        moved.save()

    assert version() == before
    assert Topic.objects.get(pk=a.pk).parent_id == sec.pk
    assert TopicPrerequisite.objects.get(pk=rel.pk).weight == 1.0

    # Non-structural edits stay possible (e.g. renaming, the pass mark).
    Topic.objects.filter(pk=a.pk).update(name="renamed", pass_mark_percentage=55.0)
    renamed = Topic.objects.get(pk=a.pk)
    renamed.description = "notes"
    renamed.save()
    assert version() == before


@pytest.mark.django_db
def test_admin_writes_go_through_the_service():
    admin_user = User.objects.create_superuser(email="kb.admin@example.org", password="x-unused-x")
    client = APIClient()
    client.force_login(admin_user)
    course = make_course("Adm")
    a = make_topic("a", course)
    b = make_topic("b", course)
    kb.add_prerequisite(prerequisite=a, topic=b)
    before = version()

    response = client.post(
        "/admin/curriculum/topicprerequisite/add/",
        {"prerequisite": b.pk, "topic": a.pk, "weight": 1},
        follow=True,
    )
    assert response.status_code == 200
    assert "Rejected (cycle)" in response.content.decode()
    assert not TopicPrerequisite.objects.filter(prerequisite=b, topic=a).exists()
    assert version() == before

    response = client.post(
        "/admin/curriculum/topicprerequisite/add/",
        {"prerequisite": course.pk, "topic": a.pk, "weight": 1},
        follow=True,
    )
    assert "Rejected (nested)" in response.content.decode()
    assert version() == before


# ---------------------------------------------------------------------------
# Y4 and choices
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_questions_only_on_topics():
    course = make_course("Y4")
    sec = make_section("S", course)
    topic = make_topic("t", sec)
    q = Question.objects.create(topic=topic, text="ok")

    for target in (course, sec):
        with pytest.raises(ValidationError):
            Question.objects.create(topic=target, text="bad")
        with pytest.raises(ValidationError):
            Question.objects.bulk_create([Question(topic=target, text="bad")])
        with pytest.raises(ValidationError):
            Question.objects.filter(pk=q.pk).update(topic=target)
        moved = Question.objects.get(pk=q.pk)
        moved.topic = target
        with pytest.raises(ValidationError):
            moved.save()
    assert Question.objects.get(pk=q.pk).topic_id == topic.pk

    with pytest.raises(kb.KBError) as rejected:
        kb.update_node(topic, kind=TopicKind.SECTION)
    assert rejected.value.reason == "has_questions"


@pytest.mark.django_db
def test_at_most_four_choices_on_bulk_paths():
    q = Question.objects.create(topic=make_topic("c"), text="Q")
    Choice.objects.bulk_create([Choice(question=q, text=str(i)) for i in range(4)])
    with pytest.raises(ValidationError):
        Choice.objects.bulk_create([Choice(question=q, text="5th")])
    with pytest.raises(ValidationError):
        Choice.objects.create(question=q, text="5th")
    assert q.choices.count() == 4


def _upload(api, topic_id, text):
    file = io.BytesIO(text.encode())
    file.name = "questions.txt"
    return api.post(
        "/api/assessments/instructor/questions_import/", {"topic_id": topic_id, "file": file}, format="multipart",
    )


@pytest.mark.django_db
def test_import_checks_y4_and_choice_limits(api):
    course = make_course("Imp")
    topic = make_topic("imp", course)
    good = "Question 1: Two plus two?\nA) 4\nB) 5\n"
    too_many = "Question 1: Pick one\nA) a\nB) b\nC) c\nD) d\n- e\nQuestion 2: Fine?\nA) yes\nB) no\n"

    response = _upload(api, course.pk, good)
    assert (response.status_code, response.json()["reason"]) == (400, "y4")

    response = _upload(api, topic.pk, too_many)
    assert response.status_code == 400
    assert response.json()["errors"] == [{"question": 1, "message": "A question needs 2 to 4 options; found 5."}]
    assert not Question.objects.filter(topic=topic).exists()

    response = _upload(api, topic.pk, good)
    assert response.status_code == 201
    assert Question.objects.get(topic=topic).choices.count() == 2


# ---------------------------------------------------------------------------
# D31 — the version row is an invariant, and the cache is scoped to it
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_a_missing_version_row_is_an_error_not_version_one():
    """Without the row the KB has no version; a silent 1 would serve a stale cache."""
    from curriculum.kb_guard import kb_write

    course = make_course("Invariant", slug="inv-course")
    with kb_write():  # only the service may remove it; here we simulate the damage
        KnowledgeBaseVersion.objects.filter(pk=1).delete()

    with pytest.raises(kb.KBError) as missing:
        KnowledgeBaseVersion.current()
    assert missing.value.reason == "version_missing"

    with pytest.raises(kb.KBError) as refused:
        make_topic("orphan", course, slug="inv-orphan")
    assert refused.value.reason == "version_missing"
    assert not Topic.objects.filter(slug="inv-orphan").exists()


@pytest.mark.django_db
def test_updated_at_moves_with_every_version_bump():
    """auto_now does not fire on QuerySet.update(), so the service sets it (V-B6a)."""
    course = make_course("Stamp", slug="stamp-course")
    before = KnowledgeBaseVersion.objects.get(pk=1).updated_at

    make_topic("t", course, slug="stamp-t")

    row = KnowledgeBaseVersion.objects.get(pk=1)
    assert row.version == version()
    assert row.updated_at > before


@pytest.mark.django_db
def test_cache_entries_are_scoped_to_the_version_row():
    """
    The key carries the row's instance_token, so an entry written before the
    counter was reset can never be served. Entries are still never invalidated:
    a new version simply writes a new key.
    """
    from django.core.cache import cache

    from curriculum.services.graph import _cache_key, clear_local_cache, get_snapshot

    course = make_course("Cache", slug="cache-course")
    a = make_topic("a", course, slug="cache-a")
    b = make_topic("b", course, slug="cache-b")
    relation = kb.add_prerequisite(prerequisite=a, topic=b)

    clear_local_cache()
    first = get_snapshot()
    token = KnowledgeBaseVersion.token()
    old_key = _cache_key(first.version)
    assert old_key == f"kb:snapshot:{token}:v{first.version}"
    assert cache.get(old_key) is not None

    kb.remove_prerequisite(relation.pk)
    clear_local_cache()
    second = get_snapshot()

    assert second.version == first.version + 1
    assert len(second.edges) == len(first.edges) - 1
    assert cache.get(old_key) is not None, "the previous entry stays addressable"
    assert cache.get(_cache_key(second.version)) is not None
    assert cache.get(f"kb:snapshot:v{first.version}") is None, "no unscoped key is written"


# ---------------------------------------------------------------------------
# D32 — only KBError leaves the service
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_missing_relation_and_duplicate_slug_are_kb_errors():
    course = make_course("Wrap", slug="wrap-course")
    a = make_topic("a", course, slug="wrap-a")
    b = make_topic("b", course, slug="wrap-b")
    relation = kb.add_prerequisite(prerequisite=a, topic=b)
    before = version()

    with pytest.raises(kb.KBError) as missing:
        kb.update_weight(10**9, 0.5)
    assert missing.value.reason == "not_found"

    with pytest.raises(kb.KBError) as duplicate:
        kb.create_node(name="Again", slug="wrap-a", parent=course, kind=TopicKind.TOPIC)
    assert duplicate.value.reason == "duplicate_slug"

    with pytest.raises(kb.KBError) as renamed:
        kb.update_node(b, slug="wrap-a")
    assert renamed.value.reason == "duplicate_slug"

    assert version() == before
    assert TopicPrerequisite.objects.get(pk=relation.pk).weight == 1.0
    assert Topic.objects.filter(slug="wrap-a").count() == 1


@pytest.mark.django_db
def test_duplicate_slug_answers_400_through_the_api(api):
    """
    On the API the serializer's unique check answers first, with a field-shaped
    400; the service's ``duplicate_slug`` covers the other callers (seeds,
    imports, the admin). Either way nothing reaches the client as a 500.
    """
    course = make_course("Api", slug="api-course")
    make_topic("taken", course, slug="api-taken")

    response = api.post(
        "/api/curriculum/instructor/topics/",
        {"name": "Clash", "slug": "api-taken", "parent": course.pk, "kind": "topic"},
        format="json",
    )
    assert response.status_code == 400
    assert "slug" in response.json()
    assert Topic.objects.filter(slug="api-taken").count() == 1


@pytest.mark.django_db
def test_delete_node_counts_only_the_nodes_it_removes():
    """Already-archived descendants are not part of the KB, so they are not counted."""
    course = make_course("Count", slug="count-course")
    section = make_section("S", course, slug="count-s")
    make_topic("keep", section, slug="count-keep")
    archived = make_topic("gone", section, slug="count-gone")
    kb.archive_node(archived)

    assert kb.delete_node(section) == ("deleted", 2)
    assert not Topic.objects.filter(slug="count-gone").exists()
