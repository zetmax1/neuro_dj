"""
analytics/tests/test_diagnostics.py — Unit tests for the TopicDiagnosticsView endpoint.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from curriculum.models import Topic
from assessments.models import (
    DifficultyLevel,
    Question,
    Choice,
    UserAbility,
    UserKnowledgeHistory,
)
from assessments.services.orchestrator import process_submission
from curriculum.testing import make_topic

User = get_user_model()


class TestTopicDiagnosticsEndpoint(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="diag_user@test.com",
            password=None,
        )
        self.topic = make_topic("Linear Algebra", slug="linear-algebra")
        self.q1 = Question.objects.create(
            topic=self.topic,
            text="Vector addition?",
            difficulty=DifficultyLevel.EASY,
            irt_difficulty=-0.5,
            irt_discrimination=1.0,
        )
        self.c1 = Choice.objects.create(question=self.q1, text="Correct", is_correct=True)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_diagnostics_unauthenticated_returns_401(self):
        anonymous_client = APIClient()
        response = anonymous_client.get(f"/api/analytics/topic/{self.topic.id}/diagnostics/")
        self.assertEqual(response.status_code, 401)

    def test_diagnostics_returns_200_and_expected_shape(self):
        # Process a submission to populate UserKnowledgeHistory, AssessmentAttempt, UserAbility
        process_submission(user=self.user, question_id=self.q1.id, choice_id=self.c1.id)

        response = self.client.get(f"/api/analytics/topic/{self.topic.id}/diagnostics/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["topic_id"], self.topic.id)
        self.assertEqual(data["topic_name"], "Linear Algebra")

        # Verify mastery trend contains multi-point history entry
        self.assertGreaterEqual(len(data["mastery_trend"]), 1)
        self.assertEqual(data["mastery_trend"][0]["attempt_number"], 1)
        self.assertIn("mastery_probability", data["mastery_trend"][0])

        # Verify current theta: a correct answer raises it above the start.
        self.assertIn("current_theta", data)
        self.assertGreater(data["current_theta"], 0.0)

        # Verify recent items. Elo moves b_q after every answer (3.3), so the
        # reported difficulty is the item's new value: a correct answer makes
        # the question look easier than the -0.5 it was seeded with.
        self.assertGreaterEqual(len(data["recent_items"]), 1)
        item = data["recent_items"][0]
        self.assertEqual(item["question_id"], self.q1.id)
        self.assertLess(item["irt_difficulty"], -0.5)
        self.assertEqual(
            item["irt_difficulty"],
            round(Question.objects.get(pk=self.q1.pk).irt_difficulty, 3),
        )
        # θ is recorded per answer, so it is the value this answer was scored
        # against rather than whatever θ happens to be now.
        self.assertEqual(item["theta_at_time"], data["current_theta"])
