"""Read-only serializers for the student-facing curriculum endpoints."""

from rest_framework import serializers

from curriculum.models import Topic, TopicResource


class StudentTopicSerializer(serializers.ModelSerializer):
    total_duration_minutes = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Topic
        fields = [
            "id", "name", "slug", "parent", "description", "position",
            "is_unlocked", "pass_mark_percentage", "test_question_count",
            "total_duration_minutes",
        ]
        read_only_fields = fields


class StudentTopicResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicResource
        fields = [
            "id", "topic", "title", "resource_type", "file", "external_url",
            "content", "duration_minutes", "created_at", "updated_at",
        ]
        read_only_fields = fields
