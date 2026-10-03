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

User = get_user_model()


class TestTopicDiagnosticsEndpoint(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="diag_user@test.com",
            password=None,
        )
        self.topic = Topic.objects.create(name="Linear Algebra", slug="linear-algebra")
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

        # Verify current theta
        self.assertIn("current_theta", data)

        # Verify recent items
        self.assertGreaterEqual(len(data["recent_items"]), 1)
        self.assertEqual(data["recent_items"][0]["question_id"], self.q1.id)
        self.assertEqual(data["recent_items"][0]["irt_difficulty"], -0.5)
