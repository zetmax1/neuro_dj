"""
curriculum/services.py — Service layer for the curriculum domain.

Contains the optimized queryset builder for the learning path tree API.

Cross-app access pattern:
  This module needs `assessments.UserKnowledgeState` to annotate topics
  with mastery data. To respect the one-way dependency rule (assessments
  → curriculum, NEVER curriculum → assessments), we use Django's
  `apps.get_model()` for lazy model resolution at runtime. This avoids
  any import-level coupling while still allowing the SQL subquery.
"""

from __future__ import annotations

import logging

from django.apps import apps
from django.db.models import IntegerField, OuterRef, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce

from curriculum.models import Topic

logger = logging.getLogger(__name__)


def get_learning_path_queryset(*, user) -> QuerySet[Topic]:
    """
    Build the annotated Topic queryset for the learning-path API.

    Returns all topics with the authenticated user's mastery percentage
    and mastery level injected via Subquery/OuterRef.

    Cross-app model access:
      Uses `apps.get_model('assessments', 'UserKnowledgeState')` to avoid
      a direct import from assessments — preserving the one-way dependency.

    Performance: 1 DB query (single SQL with two correlated subqueries).
    """
    # Lazy model resolution — no import-level dependency on assessments
    UserKnowledgeState = apps.get_model("assessments", "UserKnowledgeState")

    mastery_subquery = Subquery(
        UserKnowledgeState.objects
        .filter(user=user, topic_id=OuterRef("pk"))
        .values("score")[:1],
        output_field=IntegerField(),
    )

    mastery_level_subquery = Subquery(
        UserKnowledgeState.objects
        .filter(user=user, topic_id=OuterRef("pk"))
        .values("mastery_level")[:1],
        output_field=IntegerField(),
    )

    return (
        Topic.objects
        .with_tree_fields()  # Adds tree_depth, tree_path, tree_ordering
        .annotate(
            user_mastery_score=Coalesce(mastery_subquery, Value(0)),
            user_mastery_level=Coalesce(mastery_level_subquery, Value(0)),
        )
        .order_by("tree_ordering")
    )
