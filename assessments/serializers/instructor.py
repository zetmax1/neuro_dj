from django.db import transaction
from rest_framework import serializers
from assessments.models import Question, Choice


class InstructorChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]


class InstructorQuestionSerializer(serializers.ModelSerializer):
    choices = InstructorChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id", "topic", "text", "explanation", "difficulty",
            "image", "time_limit_seconds", "choices",
        ]

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
            Choice(question=question, **choice_data)
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

        # If choices are provided, we replace them (simple approach for nested updates)
        if choices_data is not None:
            instance.choices.all().delete()
            choices = [
                Choice(question=instance, **choice_data)
                for choice_data in choices_data
            ]
            Choice.objects.bulk_create(choices)

        return instance
