"""
curriculum/serializers/graph.py — Serializer for React Flow Prerequisite Graph.
"""

from __future__ import annotations

from rest_framework import serializers


class ReactFlowNodeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    slug = serializers.CharField(required=False)
    data = serializers.DictField(required=False)


class ReactFlowEdgeSerializer(serializers.Serializer):
    id = serializers.CharField()
    source = serializers.CharField()
    target = serializers.CharField()


class PrerequisiteGraphSerializer(serializers.Serializer):
    nodes = ReactFlowNodeSerializer(many=True)
    edges = ReactFlowEdgeSerializer(many=True)
