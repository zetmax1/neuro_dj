"""
curriculum/views/instructor.py — Instructor API views for topic + resource management.

Ownership filtering:
  Non-superuser instructors see only topics they created in the parent dropdown.
  Superusers/admins see all topics.

Duration aggregation:
  The topic queryset is annotated with total_duration_minutes (Sum of related
  resources' duration_minutes) for the frontend to display dynamic course durations.
"""

from django.db import transaction
from django.db.models import IntegerField, ProtectedError, RestrictedError, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from accounts.permissions import IsInstructor
from curriculum.models import Topic, TopicResource
from curriculum.serializers.instructor import InstructorTopicSerializer, TopicResourceSerializer

from django.core.cache import cache


@extend_schema(tags=["Instructor Management"])
class InstructorTopicViewSet(viewsets.ModelViewSet):
    """
    ViewSet for instructors to Create, Read, Update, and Delete topics.
    Restricted to instructors (D15); students use the read-only endpoints in
    curriculum/views/student.py.

    Ownership filtering:
      - Superusers/staff see all topics.
      - Regular instructors see only topics they created.

    Duration aggregation:
      - Each topic is annotated with total_duration_minutes from its resources.

    Archiving (D11):
      - DELETE removes a topic only when nothing in its subtree is referenced
        by recorded answers or test results; otherwise the whole subtree is
        archived (200, ``{"archived": true}``) so the answer ledger stays intact.
      - Archived topics are hidden unless ``?include_archived=true``.
    """
    permission_classes = [IsInstructor]
    serializer_class = InstructorTopicSerializer

    def get_queryset(self):
        queryset = (
            Topic.objects
            .annotate(
                total_duration_minutes=Coalesce(
                    Sum("resources__duration_minutes"),
                    Value(0),
                    output_field=IntegerField(),
                ),
            )
        )
        if self.request.query_params.get("include_archived", "").lower() not in ("1", "true"):
            queryset = queryset.filter(is_archived=False)
        # Non-staff instructors only see the topics they created.
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(instructor=user)
        return queryset

    def perform_create(self, serializer):
        # Auto-assign the creating user as the topic instructor
        serializer.save(instructor=self.request.user)
        self._invalidate_tree_cache()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._invalidate_tree_cache()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            # MPTT shifts lft/rght before Django checks PROTECT; the atomic
            # block rolls that back when the delete is refused.
            with transaction.atomic():
                instance.delete()
        except (ProtectedError, RestrictedError):
            subtree = Topic.objects.get(pk=instance.pk).get_descendants(include_self=True)
            archived = Topic.objects.filter(pk__in=subtree.values("pk")).update(is_archived=True)
            self._invalidate_tree_cache()
            return Response(
                {"id": instance.pk, "archived": True, "archived_topics": archived},
                status=status.HTTP_200_OK,
            )
        self._invalidate_tree_cache()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _invalidate_tree_cache(self):
        """Best-effort cache invalidation; LocMem has no pattern delete."""
        if hasattr(cache, "delete_pattern"):
            cache.delete_pattern("*tree*")


@extend_schema(tags=["Instructor Management"])
class InstructorResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for instructors to manage curriculum resources.
    Supports binary file uploads (PDFs, PPTs, etc.).
    """
    permission_classes = [IsInstructor]
    serializer_class = TopicResourceSerializer
    parser_classes = (MultiPartParser, FormParser)
    queryset = TopicResource.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset
