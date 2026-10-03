"""
curriculum/tests/test_tree.py — the topic tree on django-tree-queries (D3, D4, BB1, BB2, BB5).

Replaces the 25 MPTT tests: descendants/ancestors/children now come from
recursive CTEs, depth and the global order ``pos`` from the KB snapshot, and
every structural write goes through curriculum.services.kb.

    Computer Science            (course)
    ├── Data Structures         (section)
    │   ├── Arrays              (topic)
    │   └── Linked Lists        (topic)
    └── Algorithms              (section)
        ├── Sorting             (topic)
        └── Searching           (topic)
"""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.test import TestCase

from curriculum.kb_guard import kb_write
from curriculum.models import KnowledgeBaseVersion, Topic, TopicKind
from curriculum.services import kb
from curriculum.services.graph import get_snapshot
from curriculum.testing import make_course, make_section, make_topic


class TopicTreeSetup(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.root = make_course("Computer Science", slug="cs-test", position=0)
        cls.ds = make_section("Data Structures", cls.root, slug="ds-test", position=0)
        cls.algos = make_section("Algorithms", cls.root, slug="algos-test", position=1)
        cls.arrays = make_topic("Arrays", cls.ds, slug="arrays-test", position=0)
        cls.linked_lists = make_topic("Linked Lists", cls.ds, slug="linked-lists-test", position=1)
        cls.sorting = make_topic("Sorting", cls.algos, slug="sorting-test", position=0)
        cls.searching = make_topic("Searching", cls.algos, slug="searching-test", position=1)

    def ids(self, queryset) -> set[int]:
        return set(queryset.values_list("id", flat=True))


class TestDescendants(TopicTreeSetup):
    def test_root_descendants_include_all_children(self):
        self.assertEqual(
            self.ids(Topic.objects.descendants(self.root)),
            {self.ds.id, self.algos.id, self.arrays.id, self.linked_lists.id, self.sorting.id, self.searching.id},
        )

    def test_root_descendants_count(self):
        self.assertEqual(Topic.objects.descendants(self.root).count(), 6)

    def test_mid_level_descendants(self):
        self.assertEqual(self.ids(self.ds.descendants()), {self.arrays.id, self.linked_lists.id})

    def test_leaf_has_no_descendants(self):
        self.assertEqual(list(self.arrays.descendants()), [])

    def test_descendants_include_self_on_request(self):
        self.assertEqual(
            self.ids(self.algos.descendants(include_self=True)),
            {self.algos.id, self.sorting.id, self.searching.id},
        )


class TestAncestors(TopicTreeSetup):
    def test_root_has_no_ancestors(self):
        self.assertEqual(list(self.root.ancestors()), [])

    def test_child_ancestors(self):
        self.assertEqual(list(self.ds.ancestors().values_list("id", flat=True)), [self.root.id])

    def test_grandchild_ancestor_chain_is_ordered_from_the_root(self):
        self.assertEqual(
            list(self.searching.ancestors().values_list("name", flat=True)),
            ["Computer Science", "Algorithms"],
        )


class TestChildren(TopicTreeSetup):
    def test_root_children_in_sibling_order(self):
        self.assertEqual(list(self.root.children.values_list("id", flat=True)), [self.ds.id, self.algos.id])

    def test_leaf_has_no_children(self):
        self.assertFalse(self.sorting.children.exists())

    def test_children_exclude_grandchildren(self):
        self.assertNotIn(self.arrays.id, self.ids(self.root.children.all()))

    def test_siblings_tie_on_position_by_id(self):
        first = make_topic("Tie 1", self.algos, position=5)
        second = make_topic("Tie 2", self.algos, position=5)
        order = list(self.algos.children.values_list("id", flat=True))
        self.assertLess(order.index(first.id), order.index(second.id))


class TestSnapshotTreeData(TopicTreeSetup):
    def test_depths(self):
        depth = get_snapshot().depth
        self.assertEqual((depth[self.root.id], depth[self.ds.id], depth[self.arrays.id]), (0, 1, 2))

    def test_pos_is_the_preorder_index(self):
        pos = get_snapshot().pos
        expected = [self.root, self.ds, self.arrays, self.linked_lists, self.algos, self.sorting, self.searching]
        self.assertEqual([pos[n.id] for n in expected], list(range(7)))

    def test_root_of_and_leaves(self):
        snapshot = get_snapshot()
        self.assertEqual(snapshot.root_of(self.searching.id), self.root.id)
        self.assertEqual(snapshot.leaves_of(self.ds.id), {self.arrays.id, self.linked_lists.id})
        self.assertEqual(snapshot.leaves_of(self.sorting.id), {self.sorting.id})

    def test_leaves_for_every_kind(self):
        """Leaves(n): the course yields every topic, a section its own, a topic itself."""
        snapshot = get_snapshot()
        self.assertEqual(
            snapshot.leaves_of(self.root.id),
            {self.arrays.id, self.linked_lists.id, self.sorting.id, self.searching.id},
        )
        self.assertEqual(snapshot.leaves_of(self.algos.id), {self.sorting.id, self.searching.id})
        self.assertEqual(snapshot.leaves_of(self.searching.id), {self.searching.id})

    def test_position_change_reorders_pos_and_bumps_the_version(self):
        version = KnowledgeBaseVersion.current()
        kb.update_node(self.algos, position=0)
        kb.update_node(self.ds, position=1)
        self.assertEqual(KnowledgeBaseVersion.current(), version + 2)
        pos = get_snapshot().pos
        self.assertLess(pos[self.sorting.id], pos[self.arrays.id])

    def test_rename_does_not_change_the_knowledge_base(self):
        version = KnowledgeBaseVersion.current()
        kb.update_node(self.arrays, name="Arrays and slices")
        self.assertEqual(KnowledgeBaseVersion.current(), version)
        self.assertEqual(Topic.objects.get(pk=self.arrays.pk).name, "Arrays and slices")


class TestKinds(TopicTreeSetup):
    def test_kinds_and_defaults(self):
        self.assertEqual(
            [self.root.kind, self.ds.kind, self.arrays.kind],
            [TopicKind.COURSE, TopicKind.SECTION, TopicKind.TOPIC],
        )
        self.assertEqual(make_topic("Default", self.ds).kind, TopicKind.TOPIC)
        self.assertEqual(kb.create_node(name="Root", slug="root-default").kind, TopicKind.COURSE)

    def test_course_is_exactly_a_root(self):
        with self.assertRaises(kb.KBError) as rejected:
            kb.create_node(name="Nested course", slug="nested-course", parent=self.ds, kind=TopicKind.COURSE)
        self.assertEqual(rejected.exception.reason, "kind")
        with self.assertRaises(kb.KBError):
            kb.create_node(name="Root section", slug="root-section", kind=TopicKind.SECTION)

    def test_course_rule_is_also_a_database_constraint(self):
        with kb_write(), self.assertRaises(IntegrityError), transaction.atomic():
            Topic.objects.filter(pk=self.ds.pk).update(parent=None)

    def test_topics_are_leaves(self):
        with self.assertRaises(kb.KBError) as rejected:
            make_topic("Under a topic", self.arrays)
        self.assertEqual(rejected.exception.reason, "parent_is_topic")

    def test_section_becomes_topic_only_without_children(self):
        with self.assertRaises(kb.KBError) as rejected:
            kb.update_node(self.ds, kind=TopicKind.TOPIC)
        self.assertEqual(rejected.exception.reason, "has_children")
        empty = make_section("Empty", self.algos)
        self.assertEqual(kb.update_node(empty, kind=TopicKind.TOPIC).kind, TopicKind.TOPIC)


class TestMoves(TopicTreeSetup):
    def test_move_to_another_section(self):
        kb.move_node(self.arrays, self.algos)
        self.assertEqual(self.ids(self.algos.descendants()), {self.sorting.id, self.searching.id, self.arrays.id})

    def test_y1_node_cannot_move_into_its_subtree(self):
        for node, target in ((self.ds, self.ds), (self.ds, self.arrays), (self.root, self.ds)):
            with self.subTest(node=node.name, target=target.name):
                with self.assertRaises(kb.KBError) as rejected:
                    kb.move_node(node, target)
                self.assertEqual(rejected.exception.reason, "move_into_subtree")

    def test_rejected_move_changes_nothing(self):
        version = KnowledgeBaseVersion.current()
        with self.assertRaises(kb.KBError):
            kb.move_node(self.algos, self.sorting)  # a topic cannot receive children
        self.assertEqual(Topic.objects.get(pk=self.algos.pk).parent_id, self.root.id)
        self.assertEqual(KnowledgeBaseVersion.current(), version)


class TestArchivedNodesLeaveReads(TopicTreeSetup):
    """D11: archiving keeps the rows for the answer ledger but drops them from the KB."""

    def test_archived_subtree_leaves_the_snapshot(self):
        kb.archive_node(self.ds)
        snapshot = get_snapshot()
        for gone in (self.ds, self.arrays, self.linked_lists):
            with self.subTest(node=gone.name):
                self.assertNotIn(gone.id, snapshot.order)
                self.assertNotIn(gone.id, snapshot.pos)
                self.assertNotIn(gone.id, snapshot.depth)

    def test_archiving_reduces_the_leaves_of_the_ancestors(self):
        kb.archive_node(self.ds)
        snapshot = get_snapshot()
        self.assertEqual(snapshot.leaves_of(self.root.id), {self.sorting.id, self.searching.id})

    def test_archiving_a_single_topic_leaves_its_siblings(self):
        kb.archive_node(self.arrays)
        snapshot = get_snapshot()
        self.assertNotIn(self.arrays.id, snapshot.order)
        self.assertEqual(snapshot.leaves_of(self.ds.id), {self.linked_lists.id})

    def test_pos_closes_the_gap_left_by_an_archived_subtree(self):
        kb.archive_node(self.ds)
        pos = get_snapshot().pos
        expected = [self.root, self.algos, self.sorting, self.searching]
        self.assertEqual([pos[n.id] for n in expected], list(range(4)))

    def test_archiving_bumps_the_version(self):
        version = KnowledgeBaseVersion.current()
        self.assertEqual(kb.archive_node(self.ds), 3)
        self.assertEqual(KnowledgeBaseVersion.current(), version + 1)


class TestAncestorsAndDescendantsAfterAMove(TopicTreeSetup):
    """A move must leave both ends of the tree consistent (D37)."""

    def setUp(self) -> None:
        super().setUp()
        kb.move_node(self.arrays, self.algos)

    def test_the_node_has_the_new_ancestor_chain(self):
        self.assertEqual(
            list(self.arrays.ancestors().values_list("id", flat=True)),
            [self.root.id, self.algos.id],
        )

    def test_the_new_parent_gained_the_subtree(self):
        self.assertEqual(
            self.ids(self.algos.descendants()),
            {self.sorting.id, self.searching.id, self.arrays.id},
        )

    def test_the_old_parent_lost_the_subtree(self):
        self.assertEqual(self.ids(self.ds.descendants()), {self.linked_lists.id})

    def test_the_root_still_sees_every_node(self):
        self.assertEqual(Topic.objects.descendants(self.root).count(), 6)

    def test_depth_and_leaves_follow_the_move(self):
        snapshot = get_snapshot()
        self.assertEqual(snapshot.depth[self.arrays.id], 2)
        self.assertEqual(snapshot.leaves_of(self.ds.id), {self.linked_lists.id})
        self.assertEqual(
            snapshot.leaves_of(self.algos.id),
            {self.sorting.id, self.searching.id, self.arrays.id},
        )

    def test_moving_a_whole_section(self):
        empty = make_section("Electives", self.root)
        kb.move_node(self.ds, empty)
        self.assertEqual(
            list(self.linked_lists.ancestors().values_list("id", flat=True)),
            [self.root.id, empty.id, self.ds.id],
        )
        self.assertEqual(get_snapshot().depth[self.linked_lists.id], 3)


class TestDeepTree(TestCase):
    """The same reads on a chain deeper than five levels (D37)."""

    DEPTH = 7  # course + 5 sections + leaf topic

    @classmethod
    def setUpTestData(cls) -> None:
        cls.chain = [make_course("Deep", slug="deep-root")]
        for level in range(1, cls.DEPTH - 1):
            cls.chain.append(make_section(f"Level {level}", cls.chain[-1], slug=f"deep-s{level}"))
        cls.chain.append(make_topic("Deep leaf", cls.chain[-1], slug="deep-leaf"))
        cls.root, cls.leaf = cls.chain[0], cls.chain[-1]

    def test_ancestors_are_ordered_from_the_root(self):
        self.assertEqual(
            list(self.leaf.ancestors().values_list("id", flat=True)),
            [node.id for node in self.chain[:-1]],
        )

    def test_descendants_cover_the_whole_chain(self):
        self.assertEqual(
            set(self.root.descendants().values_list("id", flat=True)),
            {node.id for node in self.chain[1:]},
        )

    def test_depth_matches_the_level(self):
        depth = get_snapshot().depth
        self.assertEqual([depth[node.id] for node in self.chain], list(range(self.DEPTH)))

    def test_pos_is_the_preorder_index_of_the_chain(self):
        pos = get_snapshot().pos
        self.assertEqual([pos[node.id] for node in self.chain], list(range(self.DEPTH)))

    def test_every_level_has_the_same_single_leaf(self):
        snapshot = get_snapshot()
        for node in self.chain:
            with self.subTest(node=node.name):
                self.assertEqual(snapshot.leaves_of(node.id), {self.leaf.id})
                self.assertEqual(snapshot.root_of(node.id), self.root.id)

    def test_a_move_near_the_bottom_keeps_the_chain_consistent(self):
        kb.move_node(self.leaf, self.chain[1])
        self.assertEqual(
            list(self.leaf.ancestors().values_list("id", flat=True)),
            [self.root.id, self.chain[1].id],
        )
        self.assertEqual(get_snapshot().depth[self.leaf.id], 2)
