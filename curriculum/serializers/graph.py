"""
curriculum/serializers/graph.py — Serializer for React Flow Prerequisite Graph.
"""

from __future__ import annotations

from rest_framework import serializers


class ReactFlowNodeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    slug = serializers.CharField(required=False)
    data = serializers.DictField(
        required=False,
        help_text=(
            "kind, parent, pos (D4), depth, lev (topics only), and the learner's "
            "state: p_mastery, accuracy, status, mastered, missing_count (3.4)."
        ),
    )


class PrerequisiteEdgeSerializer(serializers.Serializer):
    """A relation of E_P as the instructor entered it (any two nodes)."""
    id = serializers.CharField()
    source = serializers.CharField()
    target = serializers.CharField()
    prerequisite_id = serializers.IntegerField()
    weight = serializers.FloatField()


class LeafEdgeSerializer(serializers.Serializer):
    """An edge of the inherited topic graph G_L."""
    id = serializers.CharField()
    source = serializers.CharField()
    target = serializers.CharField()
    weight = serializers.FloatField()
    inherited = serializers.BooleanField(help_text="Produced only by section- or course-level relations.")
    via = serializers.ListField(child=serializers.IntegerField(), help_text="Ids of the producing E_P relations.")


class PrerequisiteGraphSerializer(serializers.Serializer):
    kb_version = serializers.IntegerField()
    nodes = ReactFlowNodeSerializer(many=True)
    edges = PrerequisiteEdgeSerializer(many=True)
    leaf_edges = LeafEdgeSerializer(many=True)
    warnings = serializers.DictField(required=False, help_text="Instructors only: redundant edges and κ.")
