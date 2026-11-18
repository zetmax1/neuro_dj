from django.db import transaction
from rest_framework import serializers
from assessments.models import Question, Choice


class InstructorChoiceSerializer(serializers.ModelSerializer):
    # Writable so that updates can edit existing choices in place.
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class InstructorQuestionSerializer(serializers.ModelSerializer):
    choices = InstructorChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id", "topic", "text", "explanation", "difficulty",
            "image", "time_limit_seconds", "is_active", "choices",
        ]
        read_only_fields = ["is_active"]

    def validate_topic(self, topic):
        """Y4: questions belong to exactly one active topic (a leaf of kind 'topic')."""
        if topic.kind != "topic" or topic.is_archived:
            raise serializers.ValidationError(
                f"'{topic.name}' is a {topic.kind}; questions can only belong to an active topic (Y4)."
            )
        return topic

    def validate_choices(self, value):
        """Enforce a strict maximum of 4 answer choices per question."""
        if len(value) > 4:
            raise serializers.ValidationError(
                "A question cannot have more than 4 answer choices."
            )
        if len(value) < 2:
            raise serializers.ValidationError(
                "A question must have at least 2 answer choices."
            )
        correct_count = sum(1 for c in value if c.get("is_correct"))
        if correct_count != 1:
            raise serializers.ValidationError(
                "Exactly one choice must be marked as correct."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        choices_data = validated_data.pop("choices")
        question = Question.objects.create(**validated_data)

        choices = [
            Choice(question=question, text=choice_data["text"], is_correct=choice_data["is_correct"])
            for choice_data in choices_data
        ]
        Choice.objects.bulk_create(choices)

        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        choices_data = validated_data.pop("choices", None)

        # Update question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if choices_data is not None:
            self._sync_choices(instance, choices_data)

        return instance

    @staticmethod
    def _sync_choices(question, choices_data):
        """
        Edit choices in place (matched by ``id``), create the ones without an
        id and delete the omitted ones. A choice that recorded answers point to
        is never deleted (D11): the request is rejected instead.
        """
        existing = {choice.pk: choice for choice in question.choices.all()}
        kept: set[int] = set()
        new_choices = []
        for data in choices_data:
            choice_id = data.get("id")
            if choice_id is None:
                new_choices.append(
                    Choice(question=question, text=data["text"], is_correct=data["is_correct"])
                )
                continue
            choice = existing.get(choice_id)
            if choice is None or choice_id in kept:
                raise serializers.ValidationError(
                    {"choices": f"Choice {choice_id} does not belong to this question."}
                )
            choice.text = data["text"]
            choice.is_correct = data["is_correct"]
            choice.save(update_fields=["text", "is_correct"])
            kept.add(choice_id)

        removed_ids = [pk for pk in existing if pk not in kept]
        if Choice.objects.filter(pk__in=removed_ids, selections__isnull=False).exists():
            raise serializers.ValidationError(
                {"choices": "Choices that learners have selected cannot be removed; edit their text instead."}
            )
        Choice.objects.filter(pk__in=removed_ids).delete()
        Choice.objects.bulk_create(new_choices)
