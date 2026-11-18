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

from django.db.models import Count, Sum
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from curriculum.models import Topic
from curriculum.services.graph import get_snapshot

from assessments.models import Choice, Question, TopicStatus
from assessments.serializers.assessment import (
    QuestionSerializer,
    SubmissionResultSerializer,
    SubmitAnswerSerializer,
)
from assessments.services import (
    get_next_question,
    get_stratified_test_questions,
    process_submission,
    readiness,
    test_session,
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

    Two separate things (D7). The paper gets a difficulty-weighted exam score
    (easy 1, medium 2, hard 3) compared against the topic's pass mark and
    stored as a ``TestSessionResult``; that percentage never becomes
    ``p_mastery``. The answers themselves go through Algorithm 2.4 and
    Algorithm 2.3 in submission order, by the same path the adaptive endpoint
    uses, so they do move P(L), θ and b_q.

    The whole submission is one transaction in
    ``assessments.services.test_session``; the view only validates and
    serialises.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        topic_id = request.data.get("topic_id")
        if not topic_id:
            return Response(
                {"detail": "Field 'topic_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            outcome = test_session.submit(
                user=request.user,
                topic_id=topic_id,
                answers=request.data.get("answers", []),
            )
        except test_session.UnknownTopic as unknown:
            return Response({"detail": str(unknown)}, status=status.HTTP_404_NOT_FOUND)
        except TopicClosed as closed:
            return Response(closed.payload(), status=status.HTTP_403_FORBIDDEN)

        grade = outcome.grade
        state = outcome.state
        return Response(
            {
                "session_id": outcome.session.pk,
                "topic_id": outcome.session.topic_id,
                "topic_name": outcome.session.topic.name,
                "total_questions": grade.total_questions,
                "total_points": grade.total_points,
                "earned_points": grade.earned_points,
                "grade_percentage": grade.percentage,
                "pass_mark_percentage": grade.pass_mark,
                "is_passed": grade.passed,
                "breakdown": grade.breakdown,
                "answers_summary": outcome.answers,
                # The learner's state after the answers went through the model.
                "p_mastery": state.p_mastery if state else 0.0,
                "accuracy": state.accuracy if state else 0.0,
                "status": state.status if state else TopicStatus.CLOSED,
                "mastered": state.mastered_flag if state else False,
                "opened_topics": list(outcome.opened_topics),
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
        snapshot = get_snapshot()
        user = request.user
        states = readiness.states_for(user=user, snapshot=snapshot)

        # One query for every topic's question count and difficulty total, so
        # the per-topic figures below are rolled up in Python (audit 7.4: this
        # used to be ~4 queries per topic).
        per_topic = {
            row["topic_id"]: (row["n"], row["difficulty_total"])
            for row in Question.objects
            .filter(is_active=True, topic__is_archived=False)
            .values("topic_id")
            .annotate(n=Count("id"), difficulty_total=Sum("difficulty"))
        }

        result = []
        for topic in Topic.objects.filter(is_archived=False).select_related("parent"):
            leaves = snapshot.leaves_of(topic.pk)
            counts = [per_topic.get(leaf, (0, 0)) for leaf in leaves]
            q_count = sum(count for count, _ in counts)
            difficulty_total = sum(total for _, total in counts)

            if q_count:
                average = difficulty_total / q_count
                diff_str = "Easy" if average <= 1.5 else ("Medium" if average <= 2.5 else "Hard")
            else:
                diff_str = "Adaptive"

            state = states.get(topic.pk)
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
            # One snapshot for the readiness check and the selection.
            snapshot = get_snapshot()
            blocked = readiness.check_open(user=request.user, topic_id=topic_id, snapshot=snapshot)
            if blocked is not None:
                return _closed_response(blocked)
            question: Question | None = get_next_question(
                user=request.user,
                topic_id=topic_id,
                snapshot=snapshot,
            )
        except Topic.DoesNotExist:
            return Response(
                {"detail": f"Topic with id={topic_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if question is None:
            topic_ids = sorted(snapshot.leaves_of(topic_id))
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
