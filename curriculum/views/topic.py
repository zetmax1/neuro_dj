"""
curriculum/views/topic.py — API view for the learning path tree.

Endpoint:
  GET /api/learning_path/tree/

Database optimization:
  - The readiness service materialises and syncs the learner's states first
    (one SELECT in the steady case), so the counters cannot predate the
    current KB version (TY6).
  - A single query then fetches all topics with the state annotations via
    Subquery/OuterRef (built by curriculum.services).
  - Tree nesting is constructed in Python from the flat list — O(n).
  - Whether a topic is answerable is its ``status``, decided by the one
    readiness service; the view no longer computes it.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from curriculum.models import Topic
from curriculum.serializers.topic import TopicTreeSerializer
from curriculum.services import get_learning_path_queryset
from curriculum.services.graph import get_snapshot

from assessments.services import readiness

logger = logging.getLogger(__name__)



@extend_schema(tags=["Student Curriculum"])
class LearningPathTreeView(generics.ListAPIView):
    """
    Returns the full hierarchical topic tree annotated with the authenticated
    learner's ``p_mastery``, ``accuracy`` and ``status`` (3.4).

    Uses rest_framework.generics.ListAPIView with an overridden
    get_queryset() that delegates to the curriculum service layer.

    Performance budget: 1 readiness sync + 1 DB query for the tree.
      - All topics fetched in a single SQL with correlated subqueries.
      - Tree nesting is built in Python from the flat list — O(n).

    Pagination is disabled because the frontend needs the complete tree
    to render the Learning Path map in a single render pass.
    """

    serializer_class = TopicTreeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Frontend needs the full tree at once

    def get_queryset(self) -> QuerySet[Topic]:
        """
        Return the optimized topic queryset with user mastery annotations.

        Delegates to curriculum.services.get_learning_path_queryset() which:
          - Orders siblings by (position, id); the view sorts by ``pos`` (D4)
          - Annotates p_mastery, accuracy, status, mastered, missing_count and
            attempts via Subquery/OuterRef, using lazy model resolution
            (apps.get_model) for cross-app access
        """
        return get_learning_path_queryset(user=self.request.user)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Override list() to transform the flat queryset into a nested tree.

        Steps:
          1. Sync the learner's states (TY6), then evaluate the annotated
             queryset once — a flat list of all topics.
          2. Build a parent_id → children lookup dict in O(n).
          3. Serialize only root nodes; children are resolved recursively
             from the context dict.
        """
        # Step 1: readiness first, so the annotations below read counters that
        # belong to the current KB version.
        snapshot = get_snapshot()
        readiness.states_for(user=request.user, snapshot=snapshot)

        queryset: QuerySet[Topic] = self.get_queryset()
        topics: list[Topic] = sorted(
            (t for t in queryset if t.pk in snapshot.pos),
            key=lambda t: snapshot.pos[t.pk],
        )

        # Step 2: O(n) parent→children grouping in Python
        topics_by_parent: dict[int | None, list[Topic]] = defaultdict(list)
        for topic in topics:
            topics_by_parent[topic.parent_id].append(topic)

        # Root nodes have parent_id=None
        root_topics: list[Topic] = topics_by_parent.get(None, [])

        serializer = self.get_serializer(
            root_topics,
            many=True,
            context={
                "request": request,
                "topics_by_parent": topics_by_parent,
                "kb": snapshot,
            },
        )
        return Response(serializer.data)
