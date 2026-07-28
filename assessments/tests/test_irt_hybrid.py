"""
assessments/tests/test_irt_hybrid.py — Unit tests for IRT and Hybrid BKT-IRT Engines.

Tests:
  (a) probability_correct matches known 2PL reference values for (θ, a, b) triples.
  (b) update_ability updates θ in the correct direction after correct/incorrect response.
  (c) Hybrid BKT-IRT engine produces measurably different P(S)/P(G) and mastery
      than plain BKT when theta differs from item difficulty.
  (d) Adaptive question selection selects question closest to theta under IRT/Hybrid engines.
"""

from __future__ import annotations

import math
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from curriculum.models import Topic
from assessments.models import (
    DifficultyLevel,
    Question,
    UserAbility,
    UserKnowledgeState,
)
from assessments.services.engines.bayesian import BayesianKnowledgeTracingEngine
from assessments.services.engines.irt import IRTEngine, probability_correct
from assessments.services.engines.hybrid_bkt_irt import HybridBKTIRTEngine
from assessments.services.question_selection import get_next_question

User = get_user_model()


class Test2PLIRTMath(TestCase):
    """(a) Test 2PL IRT probability_correct against known analytical values."""

    def test_probability_correct_known_triples(self):
        # Case 1: theta == b (a=1, b=0, theta=0) -> P = 0.5
        p1 = probability_correct(theta=0.0, a=1.0, b=0.0)
        self.assertAlmostEqual(p1, 0.5, places=5)

        # Case 2: theta=1, a=1, b=0 -> P = 1 / (1 + exp(-1)) = 0.7310585786
        p2 = probability_correct(theta=1.0, a=1.0, b=0.0)
        expected_p2 = 1.0 / (1.0 + math.exp(-1.0))
        self.assertAlmostEqual(p2, expected_p2, places=5)
        self.assertAlmostEqual(p2, 0.7310585786, places=5)

        # Case 3: theta=0, a=2, b=1 -> P = 1 / (1 + exp(2)) = 0.1192029220
        p3 = probability_correct(theta=0.0, a=2.0, b=1.0)
        expected_p3 = 1.0 / (1.0 + math.exp(2.0))
        self.assertAlmostEqual(p3, expected_p3, places=5)
        self.assertAlmostEqual(p3, 0.1192029220, places=5)


class TestIRTEngineAbilityUpdate(TestCase):
    """(b) Test online ability update (update_ability) directionality and persistence."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="irt_test@test.com",
            password="password123",
        )
        self.topic = Topic.objects.create(name="Algebra", slug="algebra")
        self.question = Question.objects.create(
            topic=self.topic,
            text="Solve x + 2 = 5",
            difficulty=DifficultyLevel.MEDIUM,
            irt_discrimination=1.0,
            irt_difficulty=0.0,
        )
        self.engine = IRTEngine(k_factor=0.3)

    def test_update_ability_correct_answer_increases_theta(self):
        initial_theta = 0.0
        new_theta = self.engine.update_ability(self.user, self.question, is_correct=True)

        self.assertGreater(new_theta, initial_theta)
        # Check DB persistence
        ability = UserAbility.objects.get(user=self.user, topic=self.topic)
        self.assertAlmostEqual(ability.theta, new_theta)

    def test_update_ability_incorrect_answer_decreases_theta(self):
        initial_theta = 0.0
        new_theta = self.engine.update_ability(self.user, self.question, is_correct=False)

        self.assertLess(new_theta, initial_theta)
        # Check DB persistence
        ability = UserAbility.objects.get(user=self.user, topic=self.topic)
        self.assertAlmostEqual(ability.theta, new_theta)


class TestHybridBKTIRTVSPlainBKT(TestCase):
    """(c) Test that hybrid engine produces different mastery/parameters than plain BKT."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="hybrid_test@test.com",
            password="password123",
        )
        self.topic = Topic.objects.create(name="Calculus", slug="calculus")
        self.question = Question.objects.create(
            topic=self.topic,
            text="Derive x^2",
            difficulty=DifficultyLevel.EASY,  # discrete difficulty = 1
            irt_discrimination=1.5,
            irt_difficulty=2.0,             # high IRT difficulty = 2.0
        )
        self.state = UserKnowledgeState.objects.create(
            user=self.user,
            topic=self.topic,
            mastery_percentage=0.15,
        )
        # User has a low theta = -1.0
        UserAbility.objects.create(
            user=self.user,
            topic=self.topic,
            theta=-1.0,
        )

        self.plain_bkt = BayesianKnowledgeTracingEngine()
        self.hybrid_bkt = HybridBKTIRTEngine()

    def test_hybrid_engine_differs_from_plain_bkt(self):
        plain_mastery = self.plain_bkt.calculate_new_mastery(
            user=self.user,
            topic=self.topic,
            current_state=self.state,
            question=self.question,
            is_correct=True,
        )

        hybrid_mastery = self.hybrid_bkt.calculate_new_mastery(
            user=self.user,
            topic=self.topic,
            current_state=self.state,
            question=self.question,
            is_correct=True,
        )

        # Because question.irt_difficulty (2.0) - theta (-1.0) = 3.0,
        # hybrid BKT increases P(S) and decreases P(G) far more than plain EASY BKT (modifier=0).
        # Therefore, hybrid_mastery and plain_mastery MUST be measurably different.
        self.assertNotAlmostEqual(plain_mastery, hybrid_mastery, places=3)


class TestAdaptiveQuestionSelectionIRT(TestCase):
    """(d) Test question selection under IRT / Hybrid engines (closest-theta selection)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="select_test@test.com",
            password="password123",
        )
        self.topic = Topic.objects.create(name="Geometry", slug="geometry")

        self.q_easy = Question.objects.create(
            topic=self.topic,
            text="Q Easy",
            difficulty=DifficultyLevel.EASY,
            irt_difficulty=-2.0,
        )
        self.q_target = Question.objects.create(
            topic=self.topic,
            text="Q Target",
            difficulty=DifficultyLevel.MEDIUM,
            irt_difficulty=0.5,
        )
        self.q_hard = Question.objects.create(
            topic=self.topic,
            text="Q Hard",
            difficulty=DifficultyLevel.HARD,
            irt_difficulty=3.0,
        )

        # Set user theta close to 0.5
        UserAbility.objects.create(
            user=self.user,
            topic=self.topic,
            theta=0.6,
        )

    @override_settings(STUDENT_MODEL_ENGINE="hybrid_bkt_irt")
    def test_selection_picks_closest_theta_question(self):
        next_q = get_next_question(user=self.user, topic_id=self.topic.id)
        self.assertIsNotNone(next_q)
        self.assertEqual(next_q.id, self.q_target.id)
