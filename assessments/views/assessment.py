"""
assessments/views/assessment.py — API views for quiz retrieval and evaluation.

Endpoints:
  - GET  /api/assessments/next_question/?topic_id=<id>
  - POST /api/assessments/submit_answer/
  - GET  /api/assessments/test_session/?topic_id=<id>
  - POST /api/assessments/submit_test_session/
  - GET  /api/assessments/tests/

The views are intentionally thin — they validate input, delegate to
assessments.services for all business logic, and serialize the output.

A topic whose prerequisites are unmet answers 403 with the unmet ones:
``{"missing": [{"topic_id", "name", "p_mastery"}]}``. The decision belongs to
``assessments.services.readiness`` alone (stage 4); no view computes it.
"""

from __future__ import annotations

import logging

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from curriculum.models import Topic
from curriculum.services.graph import get_snapshot

from assessments.models import (
    AttemptSource,
    Choice,
    DifficultyLevel,
    Question,
    StudentTopicState,
    TestSessionResult,
    TopicStatus,
)
from assessments.serializers.assessment import (
    QuestionSerializer,
    SubmissionResultSerializer,
    SubmitAnswerSerializer,
)
from assessments.services import (
    get_next_question,
    get_stratified_test_questions,
    ledger,
    process_submission,
    readiness,
)
from assessments.services.orchestrator import TopicClosed
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)


def _closed_response(blocked: readiness.Blocked) -> Response:
    """403 for a topic whose prerequisites the learner has not mastered."""
    return Response(blocked.payload(), status=status.HTTP_403_FORBIDDEN)


@extend_schema(tags=["Student Assessments"])
class TestSessionView(APIView):
    """
    GET /api/assessments/test_session/?topic_id=<id>
    Generates a full stratified test session (10 questions: 40% Easy, 30% Medium, 30% Hard).
    Returns topic settings (pass_mark_percentage, test_question_count) and list of questions with choices.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        topic_id = request.query_params.get("topic_id")
        if not topic_id:
            return Response(
                {"detail": "Query parameter 'topic_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            topic = Topic.objects.get(pk=topic_id, is_archived=False)
        except Topic.DoesNotExist:
            return Response(
                {"detail": f"Topic with id {topic_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        blocked = readiness.check_open(user=request.user, topic_id=topic.pk)
        if blocked is not None:
            return _closed_response(blocked)

        questions = get_stratified_test_questions(topic_id=int(topic_id))

        serializer = QuestionSerializer(questions, many=True)
        return Response(
            {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "pass_mark_percentage": topic.pass_mark_percentage,
                "test_question_count": len(questions),
                "configured_target_count": topic.test_question_count,
                "questions": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Student Assessments"])
class SubmitTestSessionView(APIView):
    """
    POST /api/assessments/submit_test_session/
    Evaluates the full test session with difficulty-weighted grading (Easy=1pt, Medium=2pt, Hard=3pt).
    Calculates final grade %, compares against topic.pass_mark_percentage and stores the grade
    as a TestSessionResult. Every answer is appended to the ledger (source=test_session, or
    review_repeat under D25) and linked to that result.

    D7: the grade is an exam score and is never written to the mastery probability.
    Running the answers through the student model is stage 5.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        topic_id = request.data.get("topic_id")
        answers = request.data.get("answers", [])

        if not topic_id:
            return Response(
                {"detail": "Field 'topic_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            topic = Topic.objects.get(pk=topic_id, is_archived=False)
        except Topic.DoesNotExist:
            return Response(
                {"detail": f"Topic with id {topic_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        DIFFICULTY_WEIGHTS = {
            DifficultyLevel.EASY: 1,
            DifficultyLevel.MEDIUM: 2,
            DifficultyLevel.HARD: 3,
        }

        total_points = 0
        earned_points = 0

        breakdown = {
            "easy": {"correct": 0, "total": 0, "points": 0},
            "medium": {"correct": 0, "total": 0, "points": 0},
            "hard": {"correct": 0, "total": 0, "points": 0},
        }

        answers_summary = []
        answered_choices: list[Choice] = []

        for item in answers:
            q_id = item.get("question_id")
            c_id = item.get("choice_id")

            try:
                question = Question.objects.select_related("topic").get(pk=q_id)
            except Question.DoesNotExist:
                continue

            weight = DIFFICULTY_WEIGHTS.get(question.difficulty, 1)
            total_points += weight

            diff_key = (
                "easy"
                if question.difficulty == DifficultyLevel.EASY
                else ("medium" if question.difficulty == DifficultyLevel.MEDIUM else "hard")
            )
            breakdown[diff_key]["total"] += 1

            is_correct = False
            selected_choice_obj = None

            if c_id:
                try:
                    selected_choice_obj = Choice.objects.select_related("question__topic").get(
                        pk=c_id, question=question,
                    )
                    is_correct = selected_choice_obj.is_correct
                except Choice.DoesNotExist:
                    is_correct = False

            if is_correct:
                earned_points += weight
                breakdown[diff_key]["correct"] += 1
                breakdown[diff_key]["points"] += weight

            if selected_choice_obj:
                answered_choices.append(selected_choice_obj)

            answers_summary.append(
                {
                    "question_id": question.id,
                    "difficulty": question.difficulty,
                    "difficulty_display": question.get_difficulty_display(),
                    "is_correct": is_correct,
                    "weight": weight,
                    "points_earned": weight if is_correct else 0,
                    "explanation": question.explanation,
                }
            )

        grade_percentage = round((earned_points / total_points * 100), 1) if total_points > 0 else 0.0
        is_passed = grade_percentage >= topic.pass_mark_percentage

        with transaction.atomic():
            session = TestSessionResult.objects.create(
                user=request.user,
                topic=topic,
                total_questions=len(answers_summary),
                earned_points=earned_points,
                total_points=total_points,
                score_percentage=grade_percentage,
                pass_mark_percentage=topic.pass_mark_percentage,
                passed=is_passed,
            )

            # Advisory locks for every touched topic first (sorted), then the
            # state row: the same order as process_submission.
            ledger.lock_learner_topics(
                request.user.pk,
                {topic.pk, *(c.question.topic_id for c in answered_choices)},
            )
            for choice in answered_choices:
                source = ledger.classify_source(
                    user=request.user,
                    question=choice.question,
                    requested=AttemptSource.TEST_SESSION,
                )
                ledger.record_attempt(
                    user=request.user, choice=choice, source=source, session=session,
                )

            # D7: the grade is an exam score, never a mastery probability, so
            # only the answer counters move here. Running test answers through
            # the student model — and with it P(L), M and Algorithm 2.3 — is
            # stage 5. Nothing unlocks on a passing grade any more: readiness
            # is decided by the M flags of the prerequisites (3.4).
            readiness.states_for(user=request.user)
            state = StudentTopicState.objects.select_for_update().get(
                user=request.user, topic=topic,
            )
            state.attempts += len(answers_summary)
            state.correct += sum(1 for a in answers_summary if a["is_correct"])
            state.accuracy = state.correct / state.attempts if state.attempts else 0.0
            state.save(update_fields=["attempts", "correct", "accuracy", "updated_at"])

        return Response(
            {
                "session_id": session.pk,
                "topic_id": topic.id,
                "topic_name": topic.name,
                "total_questions": len(answers_summary),
                "total_points": total_points,
                "earned_points": earned_points,
                "grade_percentage": grade_percentage,
                "pass_mark_percentage": topic.pass_mark_percentage,
                "is_passed": is_passed,
                "breakdown": breakdown,
                "answers_summary": answers_summary,
            },
            status=status.HTTP_200_OK,
        )



@extend_schema(tags=["Student Assessments"])
class TestsListView(APIView):
    """
    GET /api/assessments/tests/ — List all available assessment tests with question counts, difficulty, and user mastery.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        topics = Topic.objects.filter(is_archived=False)
        snapshot = get_snapshot()
        result = []
        user = request.user

        states = readiness.states_for(user=user, snapshot=snapshot)

        for topic in topics:
            descendant_ids = sorted(snapshot.leaves_of(topic.pk))
            questions = Question.objects.filter(topic_id__in=descendant_ids, is_active=True)
            q_count = questions.count()

            state = states.get(topic.id)

            if questions.exists():
                avg_diff = sum(q.difficulty for q in questions) / q_count
                diff_str = "Easy" if avg_diff <= 1.5 else ("Medium" if avg_diff <= 2.5 else "Hard")
            else:
                diff_str = "Adaptive"

            result.append({
                "id": topic.id,
                "name": topic.name,
                "slug": topic.slug,
                "description": topic.description or f"Adaptive test assessment covering {topic.name}.",
                "parent_name": topic.parent.name if topic.parent else "Core Curriculum",
                "question_count": q_count,
                "p_mastery": state.p_mastery if state else 0.0,
                "accuracy": state.accuracy if state else 0.0,
                "status": state.status if state else TopicStatus.CLOSED,
                "mastered": state.mastered_flag if state else False,
                "missing_count": state.missing_count if state else 0,
                "difficulty_level": diff_str,
                "estimated_minutes": max(5, q_count * 2),
            })

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Student Assessments"])
class NextQuestionView(APIView):

    """
    Returns the next appropriate question for the authenticated user
    based on their current knowledge state for the given topic.

    Query params:
      - topic_id (required): The topic to get the next question for.

    Response:
      - 200: QuestionSerializer payload (nested choices, no is_correct).
      - 400: Missing or invalid topic_id.
      - 403: The topic is closed; the body lists the unmet prerequisites.
      - 404: Topic not found, or no more questions available.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        topic_id_raw: str | None = request.query_params.get("topic_id")
        if not topic_id_raw:
            return Response(
                {"detail": "Query parameter 'topic_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            topic_id: int = int(topic_id_raw)
        except (ValueError, TypeError):
            return Response(
                {"detail": "'topic_id' must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            blocked = readiness.check_open(user=request.user, topic_id=topic_id)
            if blocked is not None:
                return _closed_response(blocked)
            question: Question | None = get_next_question(
                user=request.user,
                topic_id=topic_id,
            )
        except Topic.DoesNotExist:
            return Response(
                {"detail": f"Topic with id={topic_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if question is None:
            topic_ids = sorted(get_snapshot().leaves_of(topic_id))
            has_questions = Question.objects.filter(topic_id__in=topic_ids, is_active=True).exists()

            if not has_questions:
                return Response(
                    {
                        "detail": "No questions available for this topic yet.",
                        "reason": "no_questions",
                        "topic_id": topic_id,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            else:
                return Response(
                    {
                        "detail": "No more questions available for this topic.",
                        "reason": "completed",
                        "topic_id": topic_id,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )


        serializer = QuestionSerializer(question)
        return Response(serializer.data)


@extend_schema(tags=["Student Assessments"])
class SubmitAnswerView(APIView):
    """
    Accepts the user's quiz answer, delegates to the service layer,
    and returns the learner's new state + next adaptive question.

    Request body: { "question_id": int, "choice_id": int }
    403 when the topic is closed, with the unmet prerequisites in the body.

    The view is thin:
      1. SubmitAnswerSerializer validates the input.
      2. services.process_submission() handles the entire transactional flow.
      3. SubmissionResultSerializer formats the DTO for the response.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        input_serializer = SubmitAnswerSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            result = process_submission(
                user=request.user,
                question_id=input_serializer.validated_data["question_id"],
                choice_id=input_serializer.validated_data["choice_id"],
            )
        except Choice.DoesNotExist:
            return Response(
                {"detail": "Invalid question_id or choice_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TopicClosed as closed:
            return Response(closed.payload(), status=status.HTTP_403_FORBIDDEN)

        output_serializer = SubmissionResultSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
