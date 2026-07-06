"""
curriculum/views/topic.py — API view for the learning path tree.

Endpoint:
  GET /api/learning_path/tree/

Database optimization:
  - Single query fetches all topics with mastery annotations via
    Subquery/OuterRef (built by curriculum.services).
  - Tree nesting is constructed in Python from the flat list — O(n).
  - is_unlocked is computed from the same pre-fetched data — O(1).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from django.db.models import QuerySet
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response

from curriculum.models import Topic
from curriculum.serializers.topic import TopicTreeSerializer
from curriculum.services import get_learning_path_queryset

logger = logging.getLogger(__name__)


class LearningPathTreeView(generics.ListAPIView):
    """
    Returns the full hierarchical topic tree annotated with the
    authenticated user's mastery_percentage and is_unlocked status.

    Uses rest_framework.generics.ListAPIView with an overridden
    get_queryset() that delegates to the curriculum service layer.

    Performance budget: 1 DB query.
      - All topics fetched in a single SQL with correlated subqueries.
      - Tree nesting is built in Python from the flat list — O(n).
      - is_unlocked is computed from the same pre-fetched data — O(1).

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
          - Applies .with_tree_fields() for tree_depth, tree_path, tree_ordering
          - Annotates mastery_score + mastery_level via Subquery/OuterRef
            using lazy model resolution (apps.get_model) for cross-app access
        """
        return get_learning_path_queryset(user=self.request.user)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Override list() to transform the flat queryset into a nested tree.

        Steps (all in Python, zero additional DB queries):
          1. Evaluate the annotated queryset once (flat list of all topics).
          2. Build a parent_id → children lookup dict in O(n).
          3. Pre-compute a topic_id → mastery_level lookup for is_unlocked.
          4. Serialize only root nodes; children are resolved recursively
             from the context dict.
        """
        # Step 1: Single DB query — all topics with mastery annotations
        queryset: QuerySet[Topic] = self.get_queryset()
        topics: list[Topic] = list(queryset)

        # Step 2: O(n) parent→children grouping in Python
        topics_by_parent: dict[int | None, list[Topic]] = defaultdict(list)
        # Step 3: O(n) topic_id→mastery_level lookup for is_unlocked checks
        mastery_by_topic_id: dict[int, int] = {}

        for topic in topics:
            topics_by_parent[topic.parent_id].append(topic)
            mastery_by_topic_id[topic.pk] = (
                getattr(topic, "user_mastery_level", 0) or 0
            )

        # Root nodes have parent_id=None
        root_topics: list[Topic] = topics_by_parent.get(None, [])

        serializer = self.get_serializer(
            root_topics,
            many=True,
            context={
                "request": request,
                "topics_by_parent": topics_by_parent,
                "mastery_by_topic_id": mastery_by_topic_id,
            },
        )
        return Response(serializer.data)
