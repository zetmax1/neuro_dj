"""
curriculum/tests/test_dag.py — Unit tests for TopicPrerequisite DAG operations.

Tests:
  (a) Cycle rejection on model save/clean
  (b) Topological ordering (Kahn's algorithm) for multi-branch prerequisites
  (c) is_unlocked_dag AND-logic (requiring ALL prerequisites mastered)
  (d) Prerequisite graph API endpoint (GET /api/curriculum/prerequisite-graph/)
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from curriculum.models import Topic, TopicPrerequisite
from curriculum.services.graph import (
    get_all_prerequisites,
    is_unlocked_dag,
    topological_order,
)
from assessments.models import UserKnowledgeState

User = get_user_model()


class DAGTestSetup(TestCase):
    """
    Setup multi-branch tree structure:
        Math (Root 1)
        └── Calculus (Child 1)

        Physics (Root 2)
        └── Classical Mechanics (Child 2)

        Quantum Computing (Root 3 or Child of Math)
        Depends on BOTH Calculus AND Classical Mechanics
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="student1@test.com",
            password="password123",
        )

        # Branch 1: Math
        cls.math = Topic.objects.create(
            name="Mathematics", slug="math", position=0
        )
        cls.calculus = Topic.objects.create(
            name="Calculus", slug="calculus", parent=cls.math, position=0
        )

        # Branch 2: Physics
        cls.physics = Topic.objects.create(
            name="Physics", slug="physics", position=1
        )
        cls.mechanics = Topic.objects.create(
            name="Classical Mechanics", slug="mechanics", parent=cls.physics, position=0
        )

        # Topic with 2 prerequisites from different tree branches
        cls.quantum = Topic.objects.create(
            name="Quantum Computing", slug="quantum-computing", position=2
        )

        Topic.objects.rebuild()


class TestCycleRejection(DAGTestSetup):
    """(a) Test that cycle creation is rejected by TopicPrerequisite.clean()."""

    def test_self_reference_rejected(self):
        """A topic cannot depend on itself."""
        prereq = TopicPrerequisite(topic=self.calculus, prerequisite=self.calculus)
        with self.assertRaises(ValidationError) as cm:
            prereq.clean()
        self.assertIn("cannot be a prerequisite of itself", str(cm.exception))

    def test_direct_cycle_rejected(self):
        """A -> B then B -> A should raise ValidationError."""
        # Calculus requires Math (Calculus -> Math)
        TopicPrerequisite.objects.create(topic=self.calculus, prerequisite=self.math)

        # Try to make Math require Calculus (Math -> Calculus) -> Cycle!
        bad_prereq = TopicPrerequisite(topic=self.math, prerequisite=self.calculus)
        with self.assertRaises(ValidationError) as cm:
            bad_prereq.clean()
        self.assertIn("creates a cycle", str(cm.exception))

    def test_transitive_cycle_rejected(self):
        """A -> B -> C then C -> A should raise ValidationError."""
        # Calculus requires Math
        TopicPrerequisite.objects.create(topic=self.calculus, prerequisite=self.math)
        # Quantum requires Calculus
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.calculus)

        # Try to make Math require Quantum (Math -> Quantum) -> Math -> Quantum -> Calculus -> Math cycle!
        bad_prereq = TopicPrerequisite(topic=self.math, prerequisite=self.quantum)
        with self.assertRaises(ValidationError) as cm:
            bad_prereq.clean()
        self.assertIn("creates a cycle", str(cm.exception))


class TestTopologicalOrder(DAGTestSetup):
    """(b) Test topological_order for a topic having 2+ prerequisites from different tree branches."""

    def test_topological_sort_multi_branch(self):
        # Quantum requires Calculus (Branch 1) AND Classical Mechanics (Branch 2)
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.calculus)
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.mechanics)

        # Calculus requires Math
        TopicPrerequisite.objects.create(topic=self.calculus, prerequisite=self.math)

        topics = [self.math, self.calculus, self.physics, self.mechanics, self.quantum]
        ordered = topological_order(topics)
        ordered_ids = [t.id for t in ordered]

        # Verify prerequisites appear BEFORE dependent topic (Quantum)
        math_idx = ordered_ids.index(self.math.id)
        calc_idx = ordered_ids.index(self.calculus.id)
        mech_idx = ordered_ids.index(self.mechanics.id)
        quantum_idx = ordered_ids.index(self.quantum.id)

        self.assertLess(math_idx, calc_idx, "Math must come before Calculus")
        self.assertLess(calc_idx, quantum_idx, "Calculus must come before Quantum")
        self.assertLess(mech_idx, quantum_idx, "Mechanics must come before Quantum")

    def test_get_all_prerequisites_transitive(self):
        TopicPrerequisite.objects.create(topic=self.calculus, prerequisite=self.math)
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.calculus)
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.mechanics)

        all_prereqs = get_all_prerequisites(self.quantum)
        expected = {self.calculus, self.math, self.mechanics}
        self.assertEqual(all_prereqs, expected)


class TestIsUnlockedDAG(DAGTestSetup):
    """(c) Test that is_unlocked_dag correctly requires ALL prerequisites, not just one."""

    def test_multi_prerequisite_unlocking(self):
        # Quantum requires BOTH Calculus AND Classical Mechanics
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.calculus)
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.mechanics)

        # Initially, neither prerequisite is mastered -> Quantum is LOCKED
        self.assertFalse(is_unlocked_dag(self.user, self.quantum))

        # Master ONLY Calculus (mastery_percentage = 0.85)
        UserKnowledgeState.objects.create(
            user=self.user,
            topic=self.calculus,
            mastery_percentage=0.85,
        )

        # Only 1 of 2 prerequisites mastered -> STILL LOCKED
        self.assertFalse(
            is_unlocked_dag(self.user, self.quantum),
            "Topic should remain locked when only 1 of 2 prerequisites is mastered",
        )

        # Master the 2nd prerequisite: Classical Mechanics
        UserKnowledgeState.objects.create(
            user=self.user,
            topic=self.mechanics,
            mastery_percentage=0.90,
        )

        # BOTH prerequisites mastered -> NOW UNLOCKED!
        self.assertTrue(
            is_unlocked_dag(self.user, self.quantum),
            "Topic should unlock once ALL prerequisites are mastered",
        )


class TestPrerequisiteGraphAPI(DAGTestSetup):
    """(d) Test GET /api/curriculum/prerequisite-graph/ endpoint."""

    def test_graph_endpoint_response_format(self):
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.calculus)
        TopicPrerequisite.objects.create(topic=self.quantum, prerequisite=self.mechanics)

        client = APIClient()
        url = "/api/curriculum/prerequisite-graph/"
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn("nodes", data)
        self.assertIn("edges", data)

        # Nodes should contain topic IDs and labels
        node_ids = [n["id"] for n in data["nodes"]]
        self.assertIn(str(self.quantum.id), node_ids)
        self.assertIn(str(self.calculus.id), node_ids)

        # Edges should connect prerequisite -> topic
        edges = data["edges"]
        self.assertEqual(len(edges), 2)
        edge_targets = {e["target"] for e in edges}
        edge_sources = {e["source"] for e in edges}

        self.assertEqual(edge_targets, {str(self.quantum.id)})
        self.assertEqual(edge_sources, {str(self.calculus.id), str(self.mechanics.id)})
