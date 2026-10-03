"""
curriculum/tests/test_seed_thesis_demo.py — Unit tests for seed_thesis_demo management command.
"""

from io import StringIO
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from curriculum.models import Topic, TopicPrerequisite
from assessments.models import UserKnowledgeHistory, UserAbility

User = get_user_model()


class TestSeedThesisDemoCommand(TestCase):
    def test_seed_thesis_demo_creates_hierarchy_dag_and_history(self):
        out = StringIO()
        call_command("seed_thesis_demo", stdout=out)

        output = out.getvalue()
        self.assertIn("Thesis Demo Database Seeding Completed Successfully", output)

        # 1. Verify MPTT Tree Hierarchy
        cs = Topic.objects.get(slug="computer-science")
        ds = Topic.objects.get(slug="data-structures")
        algo = Topic.objects.get(slug="algorithms")

        self.assertEqual(ds.parent, cs)
        self.assertEqual(algo.parent, cs)

        # 2. Verify Multi-Branch DAG Prerequisite Convergence
        demo_topic = Topic.objects.get(slug="demo-topic")
        prereqs = list(TopicPrerequisite.objects.filter(topic=demo_topic).values_list("prerequisite__slug", flat=True))
        self.assertIn("binary-trees", prereqs)
        self.assertIn("graph-traversals", prereqs)

        # 3. Verify Algorithmic History Ledger & Ability Theta
        student = User.objects.get(email="hybrid_demo@test.com")
        history_count = UserKnowledgeHistory.objects.filter(user=student).count()
        self.assertGreaterEqual(history_count, 15)

        # Ability is one row per course the learner answered in (D33), and the
        # demo seeds a single course, so one row that has actually moved.
        abilities = list(UserAbility.objects.filter(user=student))
        self.assertEqual(len(abilities), 1)
        self.assertEqual(abilities[0].course, cs)
        self.assertGreaterEqual(abilities[0].n_answers, 15)
        self.assertNotEqual(abilities[0].theta, 0.0)

        # 4. Readiness of demo_topic is decided by the one service (3.4), and
        # the seeder only answers what the learner may answer, so every topic
        # it did answer was open at the time.
        from assessments.models import StudentTopicState
        from assessments.services import readiness

        answered = StudentTopicState.objects.filter(user=student, attempts__gt=0)
        self.assertTrue(answered.exists())
        for state in answered:
            self.assertNotEqual(state.status, "closed")
        # demo_topic sits behind binary-trees and graph-traversals; whether it
        # opened depends on whether those reached M = 1, so the assertion is
        # that the service and the stored status agree.
        blocked = readiness.check_open(user=student, topic_id=demo_topic.pk)
        stored = StudentTopicState.objects.get(user=student, topic=demo_topic)
        self.assertEqual(blocked is None, stored.status != "closed")

        self.assertTrue(User.objects.filter(email="yuta@gmail.com").exists())
        self.assertTrue(User.objects.filter(email="alex@neuro.learn").exists())

    def test_seed_thesis_demo_is_idempotent(self):
        out1 = StringIO()
        call_command("seed_thesis_demo", stdout=out1)

        history_count1 = UserKnowledgeHistory.objects.filter(user__email="hybrid_demo@test.com").count()

        out2 = StringIO()
        call_command("seed_thesis_demo", stdout=out2)

        history_count2 = UserKnowledgeHistory.objects.filter(user__email="hybrid_demo@test.com").count()

        # History count is identical after re-running (no duplicate accumulation)
        self.assertEqual(history_count1, history_count2)
