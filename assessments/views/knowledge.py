"""
assessments/views/knowledge.py — API view for user knowledge states.

Endpoint:
  GET /api/knowledge_states/

Performance: 1 query with select_related('topic').
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import generics, permissions

from assessments.models import UserKnowledgeState
from assessments.serializers.knowledge import UserKnowledgeStateSerializer


class UserKnowledgeStateListView(generics.ListAPIView):
    """
    Returns all knowledge states for the authenticated user.

    Performance: 1 query with select_related('topic') — the forward FK
    is JOINed in SQL so topic_name resolves without a second query.
    """

    serializer_class = UserKnowledgeStateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[UserKnowledgeState]:
        return (
            UserKnowledgeState.objects
            .filter(user=self.request.user)
            .select_related("topic")
            .order_by("-updated_at")
        )
