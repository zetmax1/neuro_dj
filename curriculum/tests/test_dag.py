"""
curriculum/tests/test_dag.py — prerequisite relations through the KB service.

  (a) cycle and self-loop rejection (Algorithm 2.1), with the chain
  (b) topological order of G_L (Algorithm 2.2) across branches
  (c) readiness through G_L: every u ∈ Pre(w) must be mastered (3.4)
  (d) GET /api/curriculum/prerequisite-graph/ format

    Mathematics (course) ── Calculus (topic)
    Physics     (course) ── Classical Mechanics (topic)
    Quantum     (course) ── Quantum Computing (topic)
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from assessments.services import readiness
from curriculum.services import kb
from curriculum.services.graph import get_snapshot
from curriculum.testing import make_course, make_topic

User = get_user_model()


class DAGTestSetup(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(email="student1@test.com", password=None)
        cls.math = make_course("Mathematics", slug="math", position=0)
        cls.calculus = make_topic("Calculus", cls.math, slug="calculus")
        cls.physics = make_course("Physics", slug="physics", position=1)
        cls.mechanics = make_topic("Classical Mechanics", cls.physics, slug="mechanics")
        quantum_course = make_course("Quantum", slug="quantum", position=2)
        cls.quantum = make_topic("Quantum Computing", quantum_course, slug="quantum-computing")


class TestCycleRejection(DAGTestSetup):
    def test_self_reference_rejected(self):
        with self.assertRaises(kb.KBError) as cm:
            kb.add_prerequisite(prerequisite=self.calculus, topic=self.calculus)
        self.assertEqual(cm.exception.reason, "self")

    def test_direct_cycle_rejected_with_chain(self):
        kb.add_prerequisite(prerequisite=self.calculus, topic=self.quantum)
        with self.assertRaises(kb.KBError) as cm:
            kb.add_prerequisite(prerequisite=self.quantum, topic=self.calculus)
        self.assertEqual(cm.exception.reason, "cycle")
        self.assertEqual(cm.exception.chain, [self.calculus.id, self.quantum.id])

    def test_transitive_cycle_rejected_with_chain(self):
        kb.add_prerequisite(prerequisite=self.calculus, topic=self.mechanics)
        kb.add_prerequisite(prerequisite=self.mechanics, topic=self.quantum)
        with self.assertRaises(kb.KBError) as cm:
            kb.add_prerequisite(prerequisite=self.quantum, topic=self.calculus)
        self.assertEqual(cm.exception.chain, [self.calculus.id, self.mechanics.id, self.quantum.id])

    def test_cross_course_cycle_through_course_relations(self):
        # Course-level relation: every topic of Physics needs every topic of Mathematics.
        kb.add_prerequisite(prerequisite=self.math, topic=self.physics)
        with self.assertRaises(kb.KBError) as cm:
            kb.add_prerequisite(prerequisite=self.mechanics, topic=self.calculus)
        self.assertEqual(cm.exception.reason, "cycle")


class TestTopologicalOrder(DAGTestSetup):
    def test_topological_sort_multi_branch(self):
        kb.add_prerequisite(prerequisite=self.calculus, topic=self.quantum)
        kb.add_prerequisite(prerequisite=self.mechanics, topic=self.quantum)
        snapshot = get_snapshot()
        order = list(snapshot.order)
        self.assertEqual(order, [self.calculus.id, self.mechanics.id, self.quantum.id])
        self.assertEqual(snapshot.lev[self.quantum.id], 1)
        self.assertEqual(snapshot.pre[self.quantum.id], (self.calculus.id, self.mechanics.id))

    def test_descendants_are_transitive(self):
        kb.add_prerequisite(prerequisite=self.calculus, topic=self.mechanics)
        kb.add_prerequisite(prerequisite=self.mechanics, topic=self.quantum)
        self.assertEqual(get_snapshot().descendants(self.calculus.id), [self.mechanics.id, self.quantum.id])


class TestReadinessThroughTheGraph(DAGTestSetup):
    """(c) R_s(w) = 1 only when every immediate predecessor has M = 1 (3.4)."""

    def _master(self, topic) -> None:
        """Set M directly: the arithmetic that gets there is tested elsewhere."""
        from assessments.models import StudentTopicState

        readiness.states_for(user=self.user)
        StudentTopicState.objects.filter(user=self.user, topic=topic).update(
            p_mastery=0.99, mastered_flag=True,
        )
        readiness.resync(user=self.user, snapshot=get_snapshot())

    def test_a_topic_needs_all_of_its_prerequisites(self):
        kb.add_prerequisite(prerequisite=self.calculus, topic=self.quantum)
        kb.add_prerequisite(prerequisite=self.mechanics, topic=self.quantum)

        blocked = readiness.check_open(user=self.user, topic_id=self.quantum.pk)
        assert blocked is not None
        self.assertEqual(
            {item["topic_id"] for item in blocked.missing},
            {self.calculus.pk, self.mechanics.pk},
        )

        self._master(self.calculus)
        blocked = readiness.check_open(user=self.user, topic_id=self.quantum.pk)
        assert blocked is not None
        self.assertEqual(
            [item["topic_id"] for item in blocked.missing], [self.mechanics.pk],
        )

        self._master(self.mechanics)
        self.assertIsNone(readiness.check_open(user=self.user, topic_id=self.quantum.pk))

    def test_a_topic_without_prerequisites_is_open(self):
        self.assertIsNone(readiness.check_open(user=self.user, topic_id=self.calculus.pk))


class TestPrerequisiteGraphAPI(DAGTestSetup):
    """(d) GET /api/curriculum/prerequisite-graph/ (addendum A4-2 – A4-5)."""

    def test_graph_endpoint_response_format(self):
        kb.add_prerequisite(prerequisite=self.calculus, topic=self.quantum)
        kb.add_prerequisite(prerequisite=self.mechanics, topic=self.quantum, weight=0.5)

        client = APIClient()
        url = "/api/curriculum/prerequisite-graph/"
        self.assertEqual(client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

        client.force_authenticate(user=self.user)
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["kb_version"], get_snapshot().version)
        self.assertNotIn("warnings", data)  # instructors only
        nodes = {n["id"]: n["data"] for n in data["nodes"]}
        self.assertEqual(nodes[str(self.quantum.id)]["kind"], "topic")
        self.assertEqual(nodes[str(self.quantum.id)]["lev"], 1)
        self.assertEqual(nodes[str(self.math.id)]["kind"], "course")
        self.assertIsNone(nodes[str(self.math.id)]["lev"])
        self.assertEqual([n["data"]["pos"] for n in data["nodes"]], sorted(n["data"]["pos"] for n in data["nodes"]))

        edges = data["edges"]
        self.assertEqual({e["target"] for e in edges}, {str(self.quantum.id)})
        self.assertEqual({e["source"] for e in edges}, {str(self.calculus.id), str(self.mechanics.id)})
        self.assertEqual(sorted(e["weight"] for e in edges), [0.5, 1.0])
        self.assertEqual(
            {(e["source"], e["target"], e["inherited"]) for e in data["leaf_edges"]},
            {(str(self.calculus.id), str(self.quantum.id), False), (str(self.mechanics.id), str(self.quantum.id), False)},
        )
