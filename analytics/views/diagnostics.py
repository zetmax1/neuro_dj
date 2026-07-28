"""
analytics/views/diagnostics.py — Topic BKT/IRT Diagnostics endpoint.

GET /api/analytics/topic/<int:topic_id>/diagnostics/
"""

from __future__ import annotations

import logging
from typing import Any

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from curriculum.models import Topic
from assessments.models import (
    AssessmentAttempt,
    UserAbility,
    UserKnowledgeHistory,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=["Student Analytics"])
class TopicDiagnosticsView(APIView):
    """
    Returns time-series BKT mastery trend, IRT latent ability (theta),
    and recent item difficulty history for the authenticated user on a specific topic.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, topic_id: int) -> Response:
        try:
            topic = Topic.objects.get(pk=topic_id)
        except Topic.DoesNotExist:
            return Response(
                {"detail": f"Topic with id={topic_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        # 1. Mastery Trend from UserKnowledgeHistory (chronological)
        history_qs = list(
            UserKnowledgeHistory.objects
            .filter(user=user, topic=topic)
            .order_by("created_at")
        )

        mastery_trend: list[dict[str, Any]] = [
            {
                "attempt_number": idx + 1,
                "timestamp": entry.created_at.isoformat(),
                "mastery_probability": round(entry.calculated_mastery, 4),
                "mastery_pct": round(entry.calculated_mastery * 100, 1),
                "algorithm_used": entry.algorithm_used,
            }
            for idx, entry in enumerate(history_qs)
        ]

        # 2. Current IRT Theta (UserAbility)
        user_ability = UserAbility.objects.filter(user=user, topic=topic).first()
        current_theta: float = round(user_ability.theta, 3) if user_ability else 0.0

        # 3. Recent Questions Answered (last 10)
        attempts = list(
            AssessmentAttempt.objects
            .filter(user=user, question__topic=topic)
            .select_related("question")
            .order_by("-answered_at")[:10]
        )

        recent_items: list[dict[str, Any]] = [
            {
                "question_id": att.question_id,
                "irt_difficulty": round(getattr(att.question, "irt_difficulty", 0.0), 3),
                "was_correct": att.is_correct,
                "theta_at_time": current_theta,
                "answered_at": att.answered_at.isoformat(),
            }
            for att in reversed(attempts)
        ]

        avg_recent_difficulty: float = (
            round(sum(item["irt_difficulty"] for item in recent_items) / len(recent_items), 3)
            if recent_items
            else 0.0
        )

        response_data: dict[str, Any] = {
            "topic_id": topic.id,
            "topic_name": topic.name,
            "mastery_trend": mastery_trend,
            "current_theta": current_theta,
            "avg_recent_difficulty": avg_recent_difficulty,
            "recent_items": recent_items,
        }

        return Response(response_data, status=status.HTTP_200_OK)
