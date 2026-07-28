"""
curriculum/views/graph.py — API view for the Prerequisite Graph endpoint.

Endpoint:
  GET /api/curriculum/prerequisite-graph/
"""

from __future__ import annotations

from collections import defaultdict

from django.conf import settings

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from curriculum.models import Topic, TopicPrerequisite
from curriculum.serializers.graph import PrerequisiteGraphSerializer


@extend_schema(
    tags=["Curriculum Graph"],
    responses={200: PrerequisiteGraphSerializer},
)
class PrerequisiteGraphView(APIView):
    """
    Returns all topics as nodes and all TopicPrerequisite relationships as edges,
    formatted for React Flow graph visualization.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        topics = list(Topic.objects.all().order_by("tree_id", "lft"))
        prereqs = list(TopicPrerequisite.objects.all().select_related("topic", "prerequisite"))

        user = request.user if request.user and request.user.is_authenticated else None

        # Pre-compute mastery percentages for all topics in one query
        mastery_map: dict[int, float] = {}
        if user:
            from assessments.models import UserKnowledgeState
            for state in UserKnowledgeState.objects.filter(user=user).values_list("topic_id", "mastery_percentage"):
                mastery_map[state[0]] = state[1]

        # Pre-compute DAG unlock status using vectorized lookup
        threshold = getattr(settings, "MASTERY_THRESHOLD", 0.70)
        prereqs_map: dict[int, list[int]] = defaultdict(list)
        for p in prereqs:
            prereqs_map[p.topic_id].append(p.prerequisite_id)

        mastered_ids: set[int] = {tid for tid, pct in mastery_map.items() if pct >= threshold}
        mastery_levels: dict[int, int] = {}
        if user:
            from assessments.models import UserKnowledgeState
            for state in UserKnowledgeState.objects.filter(user=user).values_list("topic_id", "mastery_level"):
                mastery_levels[state[0]] = state[1]

        def is_unlocked(t: Topic) -> bool:
            if t.id in prereqs_map:
                return all(pid in mastered_ids for pid in prereqs_map[t.id])
            if t.parent_id is None:
                return True
            return mastery_levels.get(t.parent_id, 0) >= 1 or t.parent_id in mastered_ids

        nodes = [
            {
                "id": str(t.id),
                "label": t.name,
                "slug": t.slug,
                "data": {
                    "label": t.name,
                    "slug": t.slug,
                    "is_unlocked": is_unlocked(t) if user else True,
                    "mastery_pct": round(mastery_map.get(t.id, 0.0) * 100),
                },
            }
            for t in topics
        ]

        edges = [
            {
                "id": f"e{p.prerequisite_id}-{p.topic_id}",
                "source": str(p.prerequisite_id),
                "target": str(p.topic_id),
            }
            for p in prereqs
        ]

        serializer = PrerequisiteGraphSerializer({"nodes": nodes, "edges": edges})
        return Response(serializer.data, status=status.HTTP_200_OK)

