"""
curriculum/services/path.py — Learning path queryset builder.

Contains the optimized Topic queryset builder with mastery annotations.
"""

from __future__ import annotations

import logging

from django.apps import apps
from django.db.models import IntegerField, OuterRef, QuerySet, Sum, Subquery, Value
from django.db.models.functions import Coalesce

from curriculum.models import Topic

logger = logging.getLogger(__name__)


def get_learning_path_queryset(*, user) -> QuerySet[Topic]:
    """
    Build the annotated Topic queryset for the learning-path API.

    Returns all topics with the authenticated user's mastery percentage,
    mastery level, and total_duration_minutes injected via annotations.
    """
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
        .annotate(
            user_mastery_score=Coalesce(mastery_subquery, Value(0)),
            user_mastery_level=Coalesce(mastery_level_subquery, Value(0)),
            total_duration_minutes=Coalesce(
                Sum("resources__duration_minutes"),
                Value(0),
                output_field=IntegerField(),
            ),
        )
        .order_by('tree_id', 'lft')
    )
