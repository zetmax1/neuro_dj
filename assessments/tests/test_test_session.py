"""
assessments/tests/test_test_session.py — Unit tests for topic test sessions and weighted scoring.
"""

from __future__ import annotations

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from django.db import connection
from django.test.utils import CaptureQueriesContext

from curriculum.models import Topic
from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    DifficultyLevel,
    Question,
    TestSessionResult,
    StudentTopicState,
    TopicModelParams,
    UserAbility,
)
from assessments.services import get_stratified_test_questions, test_session
from curriculum.services import kb
from curriculum.services.graph import clear_local_cache, get_snapshot
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()


class TestStratifiedTestSession(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student_session@test.com",
            password=None,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.topic = make_topic(
            "Algorithms",
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

        # D7: the grade is an exam percentage; p_mastery is a probability the
        # answers produced through the model. They are different numbers on
        # different scales, and the old test hard-coded the confusion by
        # asserting mastery == 100.0 (audit 7.1).
        state = StudentTopicState.objects.get(user=self.user, topic=self.topic)
        self.assertGreaterEqual(state.p_mastery, 0.0)
        self.assertLessEqual(state.p_mastery, 1.0)
        self.assertNotAlmostEqual(state.p_mastery, data["grade_percentage"], places=3)

        # And it is exactly what replaying the ledger produces (D35): the test
        # answers went through the same Algorithm 2.4 as any other.
        before = state.p_mastery
        call_command("rebuild_student_states", stdout=StringIO())
        state.refresh_from_db()
        self.assertAlmostEqual(state.p_mastery, before, places=12)

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


# ---------------------------------------------------------------------------
# Stage 5: the paper goes through the model, the grade stays separate (D7)
# ---------------------------------------------------------------------------

class TestSessionGrading(TestCase):
    """``grade_paper`` is pure, so the exam arithmetic is checked on its own."""

    __test__ = True

    def _answer(self, difficulty: int, *, correct: bool | None):
        topic = make_topic("Grading", slug=f"grading-{difficulty}-{correct}")
        question = Question.objects.create(topic=topic, text="Q", difficulty=difficulty)
        choice = None
        if correct is not None:
            choice = Choice.objects.create(question=question, text="C", is_correct=correct)
        return test_session.PaperAnswer(question=question, choice=choice)

    def test_weights_are_one_two_three(self):
        self.assertEqual(
            [
                test_session.DIFFICULTY_WEIGHTS[DifficultyLevel.EASY],
                test_session.DIFFICULTY_WEIGHTS[DifficultyLevel.MEDIUM],
                test_session.DIFFICULTY_WEIGHTS[DifficultyLevel.HARD],
            ],
            [1, 2, 3],
        )

    def test_an_unanswered_line_counts_against_the_score(self):
        paper = [
            self._answer(DifficultyLevel.EASY, correct=True),
            self._answer(DifficultyLevel.HARD, correct=None),
        ]
        grade = test_session.grade_paper(paper, pass_mark=60.0)

        self.assertEqual((grade.total_points, grade.earned_points), (4, 1))
        self.assertAlmostEqual(grade.percentage, 25.0, places=1)
        self.assertFalse(grade.passed)
        self.assertEqual(grade.total_questions, 2)

    def test_an_empty_paper_scores_zero_without_dividing_by_zero(self):
        grade = test_session.grade_paper([], pass_mark=60.0)
        self.assertEqual((grade.total_points, grade.earned_points), (0, 0))
        self.assertEqual(grade.percentage, 0.0)
        self.assertFalse(grade.passed)

    def test_the_pass_mark_is_inclusive(self):
        paper = [
            self._answer(DifficultyLevel.EASY, correct=True),
            self._answer(DifficultyLevel.MEDIUM, correct=False),
        ]
        grade = test_session.grade_paper(paper, pass_mark=33.3)
        self.assertAlmostEqual(grade.percentage, 33.3, places=1)
        self.assertTrue(grade.passed)

    def test_the_breakdown_counts_every_tier(self):
        paper = [
            self._answer(DifficultyLevel.EASY, correct=True),
            self._answer(DifficultyLevel.MEDIUM, correct=True),
            self._answer(DifficultyLevel.HARD, correct=False),
        ]
        grade = test_session.grade_paper(paper, pass_mark=60.0)

        self.assertEqual(grade.breakdown["easy"], {"correct": 1, "total": 1, "points": 1})
        self.assertEqual(grade.breakdown["medium"], {"correct": 1, "total": 1, "points": 2})
        self.assertEqual(grade.breakdown["hard"], {"correct": 0, "total": 1, "points": 0})


class TestSessionGoesThroughTheModel(TestCase):
    """Every test answer is a model observation, in submission order (D7)."""

    __test__ = True

    def setUp(self):
        self.user = User.objects.create_user(email="session.model@test.com", password=None)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.topic = make_topic("Model topic", slug="session-model", pass_mark_percentage=60.0)
        self.course_id = get_snapshot().root_of(self.topic.pk)
        TopicModelParams.objects.create(topic=self.topic, p0=0.3, pt=0.1, g0=0.2, s0=0.05)
        self.questions = []
        for index in range(4):
            question = Question.objects.create(
                topic=self.topic, text=f"Q{index}", difficulty=DifficultyLevel.MEDIUM,
            )
            right = Choice.objects.create(question=question, text="right", is_correct=True)
            wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
            self.questions.append((question, right, wrong))

    def _submit(self, answers):
        return self.client.post(
            "/api/assessments/submit_test_session/",
            {"topic_id": self.topic.id, "answers": answers},
            format="json",
        )

    def _all_correct(self):
        return [{"question_id": q.id, "choice_id": r.id} for q, r, _ in self.questions]

    def test_the_answers_move_p_mastery_theta_and_b(self):
        before_b = [q.irt_difficulty for q, _, _ in self.questions]

        response = self._submit(self._all_correct())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        state = StudentTopicState.objects.get(user=self.user, topic=self.topic)
        self.assertGreater(state.p_mastery, 0.3)
        self.assertEqual(state.attempts, 4)
        self.assertEqual(state.correct, 4)

        ability = UserAbility.objects.get(user=self.user, course_id=self.course_id)
        self.assertGreater(ability.theta, 0.0)
        self.assertEqual(ability.n_answers, 4)

        after_b = [
            Question.objects.get(pk=q.pk).irt_difficulty for q, _, _ in self.questions
        ]
        self.assertNotEqual(before_b, after_b)

    def test_the_rows_are_a_chain_in_submission_order(self):
        self._submit(self._all_correct())

        rows = list(
            AssessmentAttempt.objects
            .filter(user=self.user).order_by("attempt_no")
        )
        self.assertEqual([row.source for row in rows], [AttemptSource.TEST_SESSION] * 4)
        for earlier, later in zip(rows, rows[1:]):
            self.assertAlmostEqual(later.p_before, earlier.p_after, places=12)
            self.assertAlmostEqual(later.theta_before, earlier.theta_after, places=12)
        self.assertTrue(all(row.engine_version == "thesis_hybrid/1" for row in rows))
        self.assertTrue(all(row.session_id is not None for row in rows))

    def test_the_response_reports_the_state_and_the_grade_separately(self):
        body = self._submit(self._all_correct()).json()
        state = StudentTopicState.objects.get(user=self.user, topic=self.topic)

        self.assertAlmostEqual(body["p_mastery"], state.p_mastery, places=12)
        self.assertEqual(body["status"], state.status)
        self.assertAlmostEqual(body["accuracy"], state.accuracy, places=12)
        self.assertEqual(body["grade_percentage"], 100.0)
        self.assertTrue(body["is_passed"])

    def test_readiness_is_recorded_for_every_answer(self):
        self._submit(self._all_correct())
        rows = AssessmentAttempt.objects.filter(user=self.user)
        self.assertTrue(all(row.readiness_score == 1.0 for row in rows))
        self.assertTrue(all(row.was_ready is True for row in rows))

    def test_a_repeat_within_the_window_does_not_move_the_model(self):
        self._submit(self._all_correct())
        first = StudentTopicState.objects.get(user=self.user, topic=self.topic)
        ability_before = UserAbility.objects.get(user=self.user, course_id=self.course_id)

        body = self._submit(self._all_correct()).json()

        after = StudentTopicState.objects.get(user=self.user, topic=self.topic)
        ability_after = UserAbility.objects.get(user=self.user, course_id=self.course_id)
        self.assertAlmostEqual(after.p_mastery, first.p_mastery, places=12)
        self.assertEqual(after.attempts, first.attempts)
        self.assertEqual(ability_after.n_answers, ability_before.n_answers)
        # The grade is still computed and stored — it is an exam, not an update.
        self.assertEqual(body["grade_percentage"], 100.0)
        self.assertEqual(
            {row["source"] for row in body["answers_summary"]},
            {AttemptSource.REVIEW_REPEAT},
        )

    def test_an_unanswered_line_writes_no_ledger_row(self):
        answers = self._all_correct()
        answers[-1] = {"question_id": self.questions[-1][0].id, "choice_id": None}

        body = self._submit(answers).json()

        self.assertEqual(AssessmentAttempt.objects.filter(user=self.user).count(), 3)
        self.assertEqual(body["total_questions"], 4)
        self.assertIsNone(body["answers_summary"][-1]["source"])
        self.assertFalse(body["answers_summary"][-1]["is_correct"])

    def test_a_choice_from_another_question_is_not_accepted(self):
        other_question, other_right, _ = self.questions[1]
        answers = [{"question_id": self.questions[0][0].id, "choice_id": other_right.id}]

        body = self._submit(answers).json()

        self.assertEqual(AssessmentAttempt.objects.filter(user=self.user).count(), 0)
        self.assertFalse(body["answers_summary"][0]["is_correct"])

    def test_the_whole_submission_is_atomic(self):
        """A failure part-way through leaves neither the session nor any row."""
        from unittest import mock

        with mock.patch(
            "assessments.services.test_session.apply_one_answer",
            side_effect=[mock.DEFAULT, RuntimeError("boom")],
        ) as patched:
            patched.return_value = mock.MagicMock(source=AttemptSource.TEST_SESSION, opened=())
            with self.assertRaises(RuntimeError):
                self._submit(self._all_correct())

        self.assertFalse(TestSessionResult.objects.filter(user=self.user).exists())
        self.assertFalse(AssessmentAttempt.objects.filter(user=self.user).exists())

    def test_loading_the_paper_is_two_queries_whatever_its_length(self):
        """
        Audit 7.4: the view issued three queries per answer. ``resolve_paper``
        loads every question and every choice in two, so the paper fetch no
        longer scales with the paper. The per-answer model work that follows is
        linear by nature — that is Algorithm 2.4 running once per answer.
        """
        one = [{"question_id": self.questions[0][0].id, "choice_id": self.questions[0][1].id}]
        with self.assertNumQueries(2):
            self.assertEqual(len(test_session.resolve_paper(one)), 1)

        every = [{"question_id": q.id, "choice_id": r.id} for q, r, _ in self.questions]
        with self.assertNumQueries(2):
            self.assertEqual(len(test_session.resolve_paper(every)), 4)

    def test_loading_a_paper_of_unknown_lines_is_still_two_queries(self):
        lines = [{"question_id": 10 ** 9 + n, "choice_id": 10 ** 9 + n} for n in range(20)]
        with self.assertNumQueries(2):
            self.assertEqual(test_session.resolve_paper(lines), [])


class TestsListQueryBudget(TestCase):
    """Audit 7.4: the tests list used ~4 queries per topic."""

    __test__ = True

    def setUp(self):
        self.user = User.objects.create_user(email="tests.list@test.com", password=None)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _build(self, topics: int) -> None:
        course = make_course(f"Budget {topics}", slug=f"budget-{topics}")
        section = make_section("S", course, slug=f"budget-{topics}-s")
        for index in range(topics):
            topic = make_topic(f"t{index}", section, slug=f"budget-{topics}-t{index}")
            question = Question.objects.create(topic=topic, text="Q")
            Choice.objects.create(question=question, text="right", is_correct=True)
        clear_local_cache()

    def test_the_cost_does_not_grow_with_the_number_of_topics(self):
        self._build(2)
        with CaptureQueriesContext(connection) as small:
            self.assertEqual(self.client.get("/api/assessments/tests/").status_code, 200)

        self._build(8)
        with CaptureQueriesContext(connection) as large:
            self.assertEqual(self.client.get("/api/assessments/tests/").status_code, 200)

        # Eight more topics may cost a bounded amount (the readiness rows are
        # materialised once), but nothing per topic.
        per_topic = (len(large) - len(small)) / 8
        self.assertLess(
            per_topic, 1.0,
            f"{per_topic:.2f} queries per extra topic: the list is still N+1",
        )


class TestSessionRespectsReadiness(TestCase):
    """A closed topic is not examinable either (TY1-TY4)."""

    __test__ = True

    def setUp(self):
        self.user = User.objects.create_user(email="session.closed@test.com", password=None)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        course = make_course("Gated", slug="session-gated")
        section = make_section("S", course, slug="session-gated-s")
        self.gate = make_topic("gate", section, slug="session-gate")
        self.locked = make_topic("locked", section, slug="session-locked")
        kb.add_prerequisite(prerequisite=self.gate, topic=self.locked)
        clear_local_cache()

        question = Question.objects.create(topic=self.locked, text="Q")
        self.right = Choice.objects.create(question=question, text="right", is_correct=True)
        self.question = question

    def test_submitting_a_closed_paper_answers_403(self):
        response = self.client.post(
            "/api/assessments/submit_test_session/",
            {
                "topic_id": self.locked.id,
                "answers": [{"question_id": self.question.id, "choice_id": self.right.id}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            [item["topic_id"] for item in response.json()["missing"]], [self.gate.id],
        )
        self.assertFalse(TestSessionResult.objects.filter(user=self.user).exists())
        self.assertFalse(AssessmentAttempt.objects.filter(user=self.user).exists())

    def test_an_unknown_topic_answers_404(self):
        response = self.client.post(
            "/api/assessments/submit_test_session/",
            {"topic_id": 10 ** 9, "answers": []},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
