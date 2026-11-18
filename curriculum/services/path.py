"""
curriculum/services/path.py — Learning path queryset builder.

Builds the Topic queryset every student-facing list endpoint reads, annotated
with the learner's state from ``StudentTopicState`` (3.4).

The annotation names are the field names the APIs report — ``p_mastery``,
``accuracy``, ``status`` — so the tree, the graph and the dashboard cannot
disagree about the same topic. The mixed-scale ``mastery_percentage`` (a
probability in some rows, a 0-100 grade in others) and the discrete
``mastery_level`` are gone with stage 4.

Callers that need the rows to exist, and to be current for the KB version,
call ``assessments.services.readiness.states_for`` first; this module only
reads what is there and defaults a missing row to "never answered".
"""

from __future__ import annotations

import logging

from django.apps import apps
from django.db.models import (
    BooleanField,
    CharField,
    FloatField,
    IntegerField,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from curriculum.models import Topic
from neuro_model import readiness as r

logger = logging.getLogger(__name__)


def _state_value(state_model, *, user, field: str, output_field, default):
    """One correlated subquery onto the learner's state row for this topic."""
    return Coalesce(
        Subquery(
            state_model.objects
            .filter(user=user, topic_id=OuterRef("pk"))
            .values(field)[:1],
            output_field=output_field,
        ),
        Value(default, output_field=output_field),
        output_field=output_field,
    )


def get_learning_path_queryset(*, user) -> QuerySet[Topic]:
    """
    All active topics with the learner's state and total resource duration.

    Annotations: ``user_p_mastery``, ``user_accuracy``, ``user_status``,
    ``user_mastered``, ``user_missing_count``, ``user_attempts`` and
    ``total_duration_minutes``. A topic the learner has no row for reads as
    closed with P(L) = 0, which is what "never seen" means.
    """
    state_model = apps.get_model("assessments", "StudentTopicState")

    return (
        Topic.objects
        .filter(is_archived=False)
        .annotate(
            user_p_mastery=_state_value(
                state_model, user=user, field="p_mastery",
                output_field=FloatField(), default=0.0,
            ),
            user_accuracy=_state_value(
                state_model, user=user, field="accuracy",
                output_field=FloatField(), default=0.0,
            ),
            user_status=_state_value(
                state_model, user=user, field="status",
                output_field=CharField(), default=r.CLOSED,
            ),
            user_mastered=_state_value(
                state_model, user=user, field="mastered_flag",
                output_field=BooleanField(), default=False,
            ),
            user_missing_count=_state_value(
                state_model, user=user, field="missing_count",
                output_field=IntegerField(), default=0,
            ),
            user_attempts=_state_value(
                state_model, user=user, field="attempts",
                output_field=IntegerField(), default=0,
            ),
            total_duration_minutes=Coalesce(
                Sum("resources__duration_minutes"),
                Value(0),
                output_field=IntegerField(),
            ),
        )
        .order_by("position", "id")
    )
