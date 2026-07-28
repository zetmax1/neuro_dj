"""
assessments/views/assessment.py — API views for quiz retrieval and evaluation.

Endpoints:
  - GET  /api/assessments/next_question/?topic_id=<id>
  - POST /api/assessments/submit_answer/

Both views are intentionally thin — they validate input, delegate to
assessments.services for all business logic, and serialize the output.
"""

from __future__ import annotations

import logging

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from curriculum.models import Topic

from assessments.models import Choice, DifficultyLevel, MasteryLevel, Question, UserKnowledgeState, AssessmentAttempt
from assessments.serializers.assessment import (
    QuestionSerializer,
    SubmissionResultSerializer,
    SubmitAnswerSerializer,
)
from assessments.services import get_next_question, get_stratified_test_questions, process_submission
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)


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
            topic = Topic.objects.get(pk=topic_id)
        except Topic.DoesNotExist:
            return Response(
                {"detail": f"Topic with id {topic_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

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
    Calculates final grade %, compares against topic.pass_mark_percentage, records attempts, and updates mastery.
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
            topic = Topic.objects.get(pk=topic_id)
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

        for item in answers:
            q_id = item.get("question_id")
            c_id = item.get("choice_id")

            try:
                question = Question.objects.get(pk=q_id)
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
                    selected_choice_obj = Choice.objects.get(pk=c_id, question=question)
                    is_correct = selected_choice_obj.is_correct
                except Choice.DoesNotExist:
                    is_correct = False

            if is_correct:
                earned_points += weight
                breakdown[diff_key]["correct"] += 1
                breakdown[diff_key]["points"] += weight

            # Record AssessmentAttempt
            if selected_choice_obj:
                AssessmentAttempt.objects.create(
                    user=request.user,
                    question=question,
                    selected_choice=selected_choice_obj,
                    is_correct=is_correct,
                )

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

        # Update User Knowledge State
        state, _ = UserKnowledgeState.objects.get_or_create(
            user=request.user,
            topic=topic,
        )
        state.total_attempts += len(answers)
        state.correct_attempts += sum(1 for a in answers_summary if a["is_correct"])

        # Update mastery percentage continuously
        new_mastery = max(state.mastery_percentage, grade_percentage)
        state.mastery_percentage = new_mastery
        if is_passed and grade_percentage >= 70.0:
            state.mastery_level = MasteryLevel.MASTERED
        elif is_passed:
            state.mastery_level = MasteryLevel.ADVANCED
        state.save()

        # Unlock dependent child topics if passed
        if is_passed:
            topic.children.filter(is_unlocked=False).update(is_unlocked=True)

        return Response(
            {
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
        topics = Topic.objects.all()
        result = []
        user = request.user

        states = {
            state.topic_id: state
            for state in UserKnowledgeState.objects.filter(user=user)
        }

        for topic in topics:
            descendant_ids = list(topic.get_descendants(include_self=True).values_list("id", flat=True))
            questions = Question.objects.filter(topic_id__in=descendant_ids, is_active=True)
            q_count = questions.count()

            state = states.get(topic.id)
            mastery_pct = round(state.mastery_percentage, 1) if state else 0.0

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
                "is_unlocked": topic.is_unlocked,
                "mastery_percentage": mastery_pct,
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
            topic = Topic.objects.get(pk=topic_id)
            topic_ids = list(topic.get_descendants(include_self=True).values_list("id", flat=True))
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
    and returns the updated mastery state + next adaptive question.

    Request body: { "question_id": int, "choice_id": int }

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

        output_serializer = SubmissionResultSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
