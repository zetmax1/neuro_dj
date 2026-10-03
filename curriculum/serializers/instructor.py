from rest_framework import serializers
from curriculum.models import Topic, TopicResource


class InstructorTopicSerializer(serializers.ModelSerializer):
    """
    Serializer for instructors to manage the knowledge tree.
    Includes total_duration_minutes aggregated from related resources.
    """
    total_duration_minutes = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Topic
        fields = [
            "id", "name", "slug", "parent", "description",
            "position", "is_unlocked", "is_archived", "instructor",
            "pass_mark_percentage", "test_question_count",
            "total_duration_minutes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["total_duration_minutes", "is_archived"]

    def validate_parent(self, parent):
        if parent is not None and parent.is_archived:
            raise serializers.ValidationError("An archived topic cannot receive new children.")
        return parent



class TopicResourceSerializer(serializers.ModelSerializer):
    """
    Serializer for TopicResource management.
    """
    class Meta:
        model = TopicResource
        fields = [
            "id",
            "topic",
            "title",
            "resource_type",
            "file",
            "external_url",
            "content",
            "duration_minutes",
            "created_at",
            "updated_at",
        ]
