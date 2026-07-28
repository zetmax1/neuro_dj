"""
curriculum/views/instructor.py — Instructor API views for topic + resource management.

Ownership filtering:
  Non-superuser instructors see only topics they created in the parent dropdown.
  Superusers/admins see all topics.

Duration aggregation:
  The topic queryset is annotated with total_duration_minutes (Sum of related
  resources' duration_minutes) for the frontend to display dynamic course durations.
"""

from django.db.models import IntegerField, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import BasePermission
from drf_spectacular.utils import extend_schema
from curriculum.models import Topic, TopicResource
from curriculum.serializers.instructor import InstructorTopicSerializer, TopicResourceSerializer

from django.core.cache import cache


class IsInstructorOrAdminOrReadOnly(BasePermission):
    """
    Permission class allowing read access to all authenticated users,
    but write access only to Admin/Instructor groups and staff.
    """
    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff or request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=["Admin", "Instructor"]).exists()



@extend_schema(tags=["Instructor Management"])
class InstructorTopicViewSet(viewsets.ModelViewSet):
    """
    ViewSet for instructors to Create, Read, Update, and Delete topics.
    Restricted to Admin/Instructor users.

    Ownership filtering:
      - Superusers/staff see all topics.
      - Regular instructors see only topics they created.

    Duration aggregation:
      - Each topic is annotated with total_duration_minutes from its resources.
    """
    permission_classes = [IsInstructorOrAdminOrReadOnly]
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
        # Non-superuser instructors only see their own topics.
        # Students (non-instructors/non-staff) should be able to read all topics.
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            if user.groups.filter(name__in=["Admin", "Instructor"]).exists():
                queryset = queryset.filter(instructor=user)
        return queryset

    def perform_create(self, serializer):
        # Auto-assign the creating user as the topic instructor
        serializer.save(instructor=self.request.user)
        self._invalidate_tree_cache()

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._invalidate_tree_cache()

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        self._invalidate_tree_cache()

    def _invalidate_tree_cache(self):
        """Clears the heavily cached student learning path tree endpoint."""
        cache.delete_pattern("*tree*")


@extend_schema(tags=["Instructor Management"])
class InstructorResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for instructors to manage curriculum resources.
    Supports binary file uploads (PDFs, PPTs, etc.).
    """
    permission_classes = [IsInstructorOrAdminOrReadOnly]
    serializer_class = TopicResourceSerializer
    parser_classes = (MultiPartParser, FormParser)
    queryset = TopicResource.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset
