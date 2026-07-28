"""
analytics/views/learning_curve.py — Time-series mastery data endpoint.

GET /api/analytics/learning_curve/?topic_id=<id>

Returns a chronological sequence of all mastery data points recorded
for the authenticated user on a specific topic, sourced from the
immutable ``UserKnowledgeHistory`` ledger.

Query strategy:
    - Single queryset with ``.select_related('topic')`` to prevent N+1.
    - Ordered by ``created_at ASC`` for chronological plotting.
    - Uses the composite index ``idx_history_user_topic_ts`` for O(log n).
    - Annotates ``mastery_pct`` at the Python level (round(float × 100))
      since it's a trivial transform, avoiding DB-level annotation overhead.
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

from assessments.models import UserKnowledgeHistory

from analytics.serializers.learning_curve import LearningCurveResponseSerializer

logger = logging.getLogger(__name__)


@extend_schema(tags=["Student Analytics"])
class LearningCurveView(APIView):
    """
    Returns a chronological array of mastery data points for the
    authenticated user on a specific topic.

    Query params:
        topic_id (required): Integer PK of the topic.

    Response (200):
        {
            "topic_id": 5,
            "topic_name": "Linear Equations",
            "topic_slug": "linear-equations",
            "total_data_points": 12,
            "current_mastery_pct": 83,
            "data_points": [
                {
                    "calculated_mastery": 0.15,
                    "mastery_pct": 15,
                    "algorithm_used": "bkt",
                    "timestamp": "2026-07-10T09:15:00Z"
                },
                ...
            ]
        }
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        # ── Validate topic_id param ───────────────────────────────────
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

        # ── Fetch topic (404 if not found) ────────────────────────────
        try:
            topic: Topic = Topic.objects.get(pk=topic_id)
        except Topic.DoesNotExist:
            return Response(
                {"detail": f"Topic with id={topic_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── Query: Chronological mastery data points ──────────────────
        # Uses composite index (user, topic, created_at) for fast scan.
        # select_related('topic') preloads topic data in a single JOIN.
        history_qs = (
            UserKnowledgeHistory.objects
            .filter(user=request.user, topic=topic)
            .select_related("topic")
            .order_by("created_at")
            .values_list(
                "calculated_mastery",
                "algorithm_used",
                "created_at",
                named=True,
            )
        )

        # ── Transform to serializable data points ─────────────────────
        data_points: list[dict[str, Any]] = [
            {
                "calculated_mastery": entry.calculated_mastery,
                "mastery_pct": round(entry.calculated_mastery * 100),
                "algorithm_used": entry.algorithm_used,
                "timestamp": entry.created_at,
            }
            for entry in history_qs
        ]

        # ── Determine current mastery from the last data point ────────
        current_mastery_pct: int = (
            data_points[-1]["mastery_pct"] if data_points else 0
        )

        # ── Build response envelope ───────────────────────────────────
        response_data: dict[str, Any] = {
            "topic_id": topic.pk,
            "topic_name": topic.name,
            "topic_slug": topic.slug,
            "total_data_points": len(data_points),
            "current_mastery_pct": current_mastery_pct,
            "data_points": data_points,
        }

        serializer = LearningCurveResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
