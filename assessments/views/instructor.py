from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema
from assessments.models import Question
from assessments.serializers.instructor import InstructorQuestionSerializer

@extend_schema(tags=["Instructor Management"])
class InstructorQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for instructors to manage the question bank.
    Restricted to Admin/Instructor users.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = InstructorQuestionSerializer
    
    def get_queryset(self):
        queryset = Question.objects.select_related("topic").prefetch_related("choices")
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset

