"""
assessments/tests/test_test_session.py — Unit tests for topic test sessions and weighted scoring.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from curriculum.models import Topic
from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    DifficultyLevel,
    Question,
    TestSessionResult,
    UserKnowledgeState,
)
from assessments.services import get_stratified_test_questions

User = get_user_model()


class TestStratifiedTestSession(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student_session@test.com",
            password=None,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.topic = Topic.objects.create(
            name="Algorithms",
            slug="algorithms",
            pass_mark_percentage=60.0,
            test_question_count=10,
        )

        # Create 6 Easy, 5 Medium, 4 Hard questions for topic (Total 15 questions)
        for i in range(6):
            q = Question.objects.create(
                topic=self.topic,
                text=f"Easy Q{i+1}",
                difficulty=DifficultyLevel.EASY,
            )
            Choice.objects.create(question=q, text="Wrong", is_correct=False)
            Choice.objects.create(question=q, text="Correct", is_correct=True)

        for i in range(5):
            q = Question.objects.create(
                topic=self.topic,
                text=f"Med Q{i+1}",
                difficulty=DifficultyLevel.MEDIUM,
            )
            Choice.objects.create(question=q, text="Wrong", is_correct=False)
            Choice.objects.create(question=q, text="Correct", is_correct=True)

        for i in range(4):
            q = Question.objects.create(
                topic=self.topic,
                text=f"Hard Q{i+1}",
                difficulty=DifficultyLevel.HARD,
            )
            Choice.objects.create(question=q, text="Wrong", is_correct=False)
            Choice.objects.create(question=q, text="Correct", is_correct=True)

    def test_stratified_question_selection_distribution(self):
        questions = get_stratified_test_questions(topic_id=self.topic.id)
        self.assertEqual(len(questions), 10)

        easy_count = sum(1 for q in questions if q.difficulty == DifficultyLevel.EASY)
        med_count = sum(1 for q in questions if q.difficulty == DifficultyLevel.MEDIUM)
        hard_count = sum(1 for q in questions if q.difficulty == DifficultyLevel.HARD)

        self.assertEqual(easy_count, 4)
        self.assertEqual(med_count, 3)
        self.assertEqual(hard_count, 3)

    def test_get_test_session_endpoint(self):
        response = self.client.get(f"/api/assessments/test_session/?topic_id={self.topic.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["topic_id"], self.topic.id)
        self.assertEqual(data["pass_mark_percentage"], 60.0)
        self.assertEqual(data["test_question_count"], 10)
        self.assertEqual(len(data["questions"]), 10)

    def test_submit_test_session_weighted_grading(self):
        # Fetch question session paper
        questions = get_stratified_test_questions(topic_id=self.topic.id)
        answers = []

        # Answer 4 Easy correct (4x1 = 4 pts)
        # Answer 3 Medium correct (3x2 = 6 pts)
        # Answer 3 Hard incorrect (0 pts out of 3x3=9 pts)
        # Total earned: 10 / 19 pts = 52.6% (Below 60% pass mark -> Failed)
        for q in questions:
            correct_choice = q.choices.filter(is_correct=True).first()
            wrong_choice = q.choices.filter(is_correct=False).first()

            if q.difficulty in (DifficultyLevel.EASY, DifficultyLevel.MEDIUM):
                answers.append({"question_id": q.id, "choice_id": correct_choice.id})
            else:
                answers.append({"question_id": q.id, "choice_id": wrong_choice.id})

        response = self.client.post(
            "/api/assessments/submit_test_session/",
            {
                "topic_id": self.topic.id,
                "answers": answers,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["total_points"], 19)
        self.assertEqual(data["earned_points"], 10)
        self.assertAlmostEqual(data["grade_percentage"], 52.6, places=1)
        self.assertFalse(data["is_passed"])

        # Now test passing score: answer 2 Hard correct (2x3 = 6 pts) -> Earned: 16/19 pts = 84.2% -> Passed!
        answers = []
        for q in questions:
            correct_choice = q.choices.filter(is_correct=True).first()
            answers.append({"question_id": q.id, "choice_id": correct_choice.id})

        response = self.client.post(
            "/api/assessments/submit_test_session/",
            {
                "topic_id": self.topic.id,
                "answers": answers,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["is_passed"])
        self.assertAlmostEqual(data["grade_percentage"], 100.0, places=1)

        # D7: the grade is stored as a test result, never as the mastery
        # probability (stage 5 runs the answers through the model instead).
        state = UserKnowledgeState.objects.get(user=self.user, topic=self.topic)
        self.assertEqual(state.mastery_percentage, 0.0)

        first, second = TestSessionResult.objects.filter(user=self.user).order_by("submitted_at", "id")
        self.assertEqual(data["session_id"], second.pk)
        self.assertAlmostEqual(first.score_percentage, 52.6, places=1)
        self.assertFalse(first.passed)
        self.assertAlmostEqual(second.score_percentage, 100.0, places=1)
        self.assertTrue(second.passed)

        # Every answer is in the ledger and linked to its session. The second
        # paper repeats the first within the review window, so D25 marks it.
        self.assertEqual(
            set(first.attempts.values_list("source", flat=True)), {AttemptSource.TEST_SESSION},
        )
        self.assertEqual(
            set(second.attempts.values_list("source", flat=True)), {AttemptSource.REVIEW_REPEAT},
        )
        self.assertEqual(AssessmentAttempt.objects.filter(user=self.user).count(), 20)
        self.assertEqual(
            sorted(AssessmentAttempt.objects.filter(user=self.user).values_list("attempt_no", flat=True)),
            list(range(1, 21)),
        )
