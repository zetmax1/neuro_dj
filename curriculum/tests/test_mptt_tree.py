"""
curriculum/tests/test_mptt_tree.py — Regression tests for the MPTT migration.

Confirms that django-mptt's get_descendants() and get_ancestors() return
identical results to what django-tree-queries would have produced, and
that the is_unlocked gating logic continues to work correctly.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from curriculum.models import Topic

User = get_user_model()


class TopicTreeSetup(TestCase):
    """
    Shared test fixtures for tree-related tests.

    Creates a three-level topic hierarchy:
        Root (Computer Science)
        ├── Data Structures (level 1)
        │   ├── Arrays (level 2)
        │   └── Linked Lists (level 2)
        └── Algorithms (level 1)
            ├── Sorting (level 2)
            └── Searching (level 2)
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.root = Topic.objects.create(
            name="Computer Science",
            slug="cs-test",
            position=0,
        )
        cls.ds = Topic.objects.create(
            name="Data Structures",
            slug="ds-test",
            parent=cls.root,
            position=0,
        )
        cls.algos = Topic.objects.create(
            name="Algorithms",
            slug="algos-test",
            parent=cls.root,
            position=1,
        )
        cls.arrays = Topic.objects.create(
            name="Arrays",
            slug="arrays-test",
            parent=cls.ds,
            position=0,
        )
        cls.linked_lists = Topic.objects.create(
            name="Linked Lists",
            slug="linked-lists-test",
            parent=cls.ds,
            position=1,
        )
        cls.sorting = Topic.objects.create(
            name="Sorting",
            slug="sorting-test",
            parent=cls.algos,
            position=0,
        )
        cls.searching = Topic.objects.create(
            name="Searching",
            slug="searching-test",
            parent=cls.algos,
            position=1,
        )
        # Rebuild tree to ensure MPTT columns are correct
        Topic.objects.rebuild()


class TestGetDescendants(TopicTreeSetup):
    """Test that get_descendants() returns the correct set at each level."""

    def test_root_descendants_include_all_children(self):
        """Root should have 6 descendants (2 children + 4 grandchildren)."""
        descendants = set(self.root.get_descendants().values_list("id", flat=True))
        expected = {
            self.ds.id, self.algos.id,
            self.arrays.id, self.linked_lists.id,
            self.sorting.id, self.searching.id,
        }
        self.assertEqual(descendants, expected)

    def test_root_descendants_count(self):
        self.assertEqual(self.root.get_descendant_count(), 6)

    def test_mid_level_descendants(self):
        """Data Structures should have 2 descendants: Arrays, Linked Lists."""
        descendants = set(self.ds.get_descendants().values_list("id", flat=True))
        self.assertEqual(descendants, {self.arrays.id, self.linked_lists.id})

    def test_leaf_has_no_descendants(self):
        """Leaf nodes should have zero descendants."""
        self.assertEqual(self.arrays.get_descendant_count(), 0)
        self.assertEqual(list(self.arrays.get_descendants()), [])

    def test_algorithms_descendants(self):
        """Algorithms should have Sorting and Searching."""
        descendants = set(self.algos.get_descendants().values_list("id", flat=True))
        self.assertEqual(descendants, {self.sorting.id, self.searching.id})


class TestGetAncestors(TopicTreeSetup):
    """Test that get_ancestors() returns correct ancestor chain."""

    def test_root_has_no_ancestors(self):
        """Root node should have no ancestors."""
        self.assertEqual(list(self.root.get_ancestors()), [])

    def test_child_ancestors(self):
        """Data Structures should have [Computer Science] as ancestor."""
        ancestors = list(self.ds.get_ancestors().values_list("id", flat=True))
        self.assertEqual(ancestors, [self.root.id])

    def test_grandchild_ancestors(self):
        """Arrays should have [Computer Science, Data Structures] as ancestors."""
        ancestors = list(self.arrays.get_ancestors().values_list("id", flat=True))
        self.assertEqual(ancestors, [self.root.id, self.ds.id])

    def test_ancestor_chain_ordering(self):
        """Ancestors should be returned in root-to-leaf order."""
        ancestors = list(self.searching.get_ancestors().values_list("name", flat=True))
        self.assertEqual(ancestors, ["Computer Science", "Algorithms"])


class TestGetChildren(TopicTreeSetup):
    """Test that get_children() returns only direct children."""

    def test_root_children(self):
        """Root should have exactly 2 children: DS and Algorithms."""
        children = set(self.root.get_children().values_list("id", flat=True))
        self.assertEqual(children, {self.ds.id, self.algos.id})

    def test_leaf_has_no_children(self):
        """Leaf nodes should have no children."""
        self.assertEqual(list(self.sorting.get_children()), [])

    def test_children_excludes_grandchildren(self):
        """get_children() should NOT include grandchildren."""
        child_ids = set(self.root.get_children().values_list("id", flat=True))
        # Arrays/Linked Lists/Sorting/Searching should NOT be in children
        self.assertNotIn(self.arrays.id, child_ids)
        self.assertNotIn(self.sorting.id, child_ids)


class TestMPTTColumns(TopicTreeSetup):
    """Test that MPTT lft/rght/level columns are correctly computed."""

    def test_root_level_is_zero(self):
        self.root.refresh_from_db()
        self.assertEqual(self.root.level, 0)

    def test_child_level_is_one(self):
        self.ds.refresh_from_db()
        self.assertEqual(self.ds.level, 1)

    def test_grandchild_level_is_two(self):
        self.arrays.refresh_from_db()
        self.assertEqual(self.arrays.level, 2)

    def test_lft_rght_range_contains_descendants(self):
        """Root's lft/rght range should encompass all descendant ranges."""
        self.root.refresh_from_db()
        for desc in self.root.get_descendants():
            self.assertGreater(desc.lft, self.root.lft)
            self.assertLess(desc.rght, self.root.rght)

    def test_leaf_lft_rght_adjacent(self):
        """Leaf nodes should have rght = lft + 1."""
        self.arrays.refresh_from_db()
        self.assertEqual(self.arrays.rght, self.arrays.lft + 1)


class TestIsUnlockedGating(TopicTreeSetup):
    """Test that the is_unlocked gating logic works with MPTT."""

    def test_root_is_always_unlocked(self):
        """Root nodes should always be unlocked (parent_id is None)."""
        self.assertTrue(self.root.is_unlocked)

    def test_default_unlock_state(self):
        """New topics default to is_unlocked=True."""
        new_topic = Topic.objects.create(
            name="Test",
            slug="test-unlock",
            parent=self.root,
            position=99,
        )
        self.assertTrue(new_topic.is_unlocked)

    def test_locked_topic_can_be_unlocked(self):
        """Locked topics can be bulk-unlocked (simulating mastery threshold)."""
        locked = Topic.objects.create(
            name="Locked Topic",
            slug="locked-topic",
            parent=self.root,
            position=99,
            is_unlocked=False,
        )
        self.assertFalse(locked.is_unlocked)

        # Simulate unlocking via the orchestrator pattern
        Topic.objects.filter(pk=locked.pk).update(is_unlocked=True)
        locked.refresh_from_db()
        self.assertTrue(locked.is_unlocked)


class TestTreeIntegrity(TopicTreeSetup):
    """Test overall tree structural integrity after MPTT migration."""

    def test_tree_id_consistency(self):
        """All nodes in the same tree should share the same tree_id."""
        tree_ids = set(
            Topic.objects.filter(
                id__in=[
                    self.root.id, self.ds.id, self.algos.id,
                    self.arrays.id, self.linked_lists.id,
                    self.sorting.id, self.searching.id,
                ]
            ).values_list("tree_id", flat=True)
        )
        self.assertEqual(len(tree_ids), 1, "All nodes should share one tree_id")

    def test_rebuild_preserves_parent_relationships(self):
        """After rebuild(), parent_id relationships should be unchanged."""
        Topic.objects.rebuild()
        self.arrays.refresh_from_db()
        self.assertEqual(self.arrays.parent_id, self.ds.id)
        self.ds.refresh_from_db()
        self.assertEqual(self.ds.parent_id, self.root.id)

    def test_get_siblings_returns_self_and_siblings(self):
        """get_siblings(include_self=True) should return the topic and all its siblings."""
        sibling_ids = set(self.ds.get_siblings(include_self=True).values_list("id", flat=True))
        # DS and Algorithms are siblings
        self.assertIn(self.ds.id, sibling_ids)
        self.assertIn(self.algos.id, sibling_ids)

    def test_get_family_returns_entire_family(self):
        """get_family() should return ancestors, self, and descendants."""
        family_ids = set(self.ds.get_family().values_list("id", flat=True))
        self.assertEqual(family_ids, {self.root.id, self.ds.id, self.arrays.id, self.linked_lists.id})

    def test_is_leaf_node(self):
        """Leaf nodes should be correctly identified."""
        self.assertTrue(self.arrays.is_leaf_node())
        self.assertFalse(self.root.is_leaf_node())
        self.assertFalse(self.ds.is_leaf_node())

    def test_is_root_node(self):
        """Root node should be correctly identified."""
        self.assertTrue(self.root.is_root_node())
        self.assertFalse(self.ds.is_root_node())
        self.assertFalse(self.arrays.is_root_node())
