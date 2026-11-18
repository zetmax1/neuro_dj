"""
assessments/views/knowledge.py — API view for the learner's topic states.

Endpoint:
  GET /api/knowledge_states/

The rows are materialised and brought up to the current KB version by the
readiness service first (TY6), so the list cannot serve counters computed
under an older knowledge base.
"""

from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from assessments.models import StudentTopicState
from assessments.serializers.knowledge import StudentTopicStateSerializer
from assessments.services import readiness


@extend_schema(tags=["Student Assessments"])
class StudentTopicStateListView(generics.ListAPIView):
    """
    Every topic state of the authenticated learner.

    Performance: the readiness sync is one SELECT in the steady case, then
    one query with select_related('topic').
    """

    serializer_class = StudentTopicStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[StudentTopicState]:
        readiness.states_for(user=self.request.user)
        return (
            StudentTopicState.objects
            .filter(user=self.request.user)
            .select_related("topic")
            .order_by("-updated_at")
        )
