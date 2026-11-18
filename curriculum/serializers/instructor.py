from rest_framework import serializers

from curriculum.models import Topic, TopicKind, TopicPrerequisite, TopicResource
from curriculum.services import kb


class InstructorTopicSerializer(serializers.ModelSerializer):
    """
    Serializer for instructors to manage the knowledge tree.
    Includes total_duration_minutes aggregated from related resources.

    Writes go through curriculum.services.kb (create_node / update_node), which
    validates the tree (Y1–Y3, kinds) and bumps the KB version.
    """
    total_duration_minutes = serializers.IntegerField(read_only=True, default=0)
    # D39: what the structure editor needs to know before offering a kind
    # change — a section with children is not a leaf, and a topic holding
    # questions cannot become a section (Y4).
    question_count = serializers.IntegerField(read_only=True, default=0)
    child_count = serializers.IntegerField(read_only=True, default=0)
    kind = serializers.ChoiceField(
        choices=TopicKind.choices,
        required=False,
        help_text="course (root), section or topic (leaf; only topics hold questions). "
                  "Defaults to course for a root and topic otherwise.",
    )
    position = serializers.IntegerField(required=False, min_value=0)

    class Meta:
        model = Topic
        fields = [
            "id", "name", "slug", "parent", "kind", "description",
            "position", "is_archived", "instructor",
            "pass_mark_percentage", "test_question_count",
            "total_duration_minutes", "question_count", "child_count",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "total_duration_minutes", "question_count", "child_count", "is_archived",
        ]

    def validate_parent(self, parent):
        if parent is not None and parent.is_archived:
            raise serializers.ValidationError("An archived topic cannot receive new children.")
        return parent

    def create(self, validated_data):
        return kb.create_node(**validated_data)

    def update(self, instance, validated_data):
        return kb.update_node(instance, **validated_data)


class PrerequisiteSerializer(serializers.ModelSerializer):
    """One relation of E_P: ``prerequisite`` must be mastered before ``topic``."""
    prerequisite_name = serializers.CharField(source="prerequisite.name", read_only=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    weight = serializers.FloatField(required=False, default=1.0)

    class Meta:
        model = TopicPrerequisite
        fields = ["id", "prerequisite", "prerequisite_name", "topic", "topic_name", "weight", "created_at"]
        read_only_fields = ["id", "created_at"]
        # Duplicates, self-loops, Y2/Y3 and ω are decided by the KB service so
        # that every rejection carries the same {"reason", "detail"} shape.
        validators = []

    def create(self, validated_data):
        return kb.add_prerequisite(**validated_data)

    def update(self, instance, validated_data):
        if {"prerequisite", "topic"} & set(validated_data) and (
            validated_data.get("prerequisite", instance.prerequisite) != instance.prerequisite
            or validated_data.get("topic", instance.topic) != instance.topic
        ):
            raise serializers.ValidationError("Endpoints cannot change; delete and add the relation instead.")
        return kb.update_weight(instance, validated_data.get("weight", instance.weight))


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
