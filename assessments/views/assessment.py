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

from assessments.models import Choice, Question
from assessments.serializers.assessment import (
    QuestionSerializer,
    SubmissionResultSerializer,
    SubmitAnswerSerializer,
)
from assessments.services import get_next_question, process_submission
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)


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
