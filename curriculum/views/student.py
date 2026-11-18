"""
Read-only curriculum endpoints for students (decision D15).

  GET /api/curriculum/topics/<id>/
  GET /api/curriculum/topics/<id>/resources/
"""

from django.db.models import IntegerField, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from curriculum.models import Topic, TopicResource
from curriculum.serializers.student import StudentTopicResourceSerializer, StudentTopicSerializer


@extend_schema(tags=["Student Curriculum"])
class StudentTopicDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentTopicSerializer
    queryset = Topic.objects.filter(is_archived=False).annotate(
        total_duration_minutes=Coalesce(
            Sum("resources__duration_minutes"), Value(0), output_field=IntegerField(),
        ),
    )


@extend_schema(tags=["Student Curriculum"])
class StudentTopicResourceListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentTopicResourceSerializer
    pagination_class = None

    def get_queryset(self):
        topic = get_object_or_404(Topic, pk=self.kwargs["pk"], is_archived=False)
        return TopicResource.objects.filter(topic=topic).order_by("id")
