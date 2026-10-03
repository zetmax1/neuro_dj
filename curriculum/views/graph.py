"""
curriculum/views/graph.py — API view for the Prerequisite Graph endpoint.

Endpoint:
  GET /api/curriculum/prerequisite-graph/
"""

from __future__ import annotations

from collections import defaultdict

from django.conf import settings

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import is_instructor
from curriculum.models import Topic, TopicKind
from curriculum.serializers.graph import PrerequisiteGraphSerializer
from curriculum.services.graph import get_snapshot
from curriculum.views.instructor import leaf_edges_payload, warnings_payload


@extend_schema(
    tags=["Curriculum Graph"],
    responses={200: PrerequisiteGraphSerializer},
)
class PrerequisiteGraphView(APIView):
    """
    The knowledge base for React Flow (addendum A4-2 – A4-5).

    - ``nodes``: every active node in programme order ``pos`` with ``kind``,
      ``parent``, ``depth`` and, for topics, ``lev`` (Algorithm 2.2);
    - ``edges``: the E_P relations as instructors entered them, with ω;
    - ``leaf_edges``: the inherited topic graph G_L — ``inherited`` marks edges
      produced only by section/course relations, ``via`` the relation ids;
    - ``warnings`` (instructors only): redundant edges and κ.

    ``is_unlocked`` / ``mastery_pct`` are the legacy per-node values; the
    per-learner states of chapter II replace them in stage 4.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        snapshot = get_snapshot()
        labels = dict(
            (pk, (name, slug))
            for pk, name, slug in Topic.objects.filter(pk__in=list(snapshot.pos)).values_list("pk", "name", "slug")
        )
        node_ids = snapshot.topics_in_programme_order()

        user = request.user if request.user and request.user.is_authenticated else None

        # Pre-compute mastery percentages for all topics in one query
        mastery_map: dict[int, float] = {}
        mastery_levels: dict[int, int] = {}
        if user:
            from assessments.models import UserKnowledgeState
            for topic_id, pct, level in UserKnowledgeState.objects.filter(user=user).values_list(
                "topic_id", "mastery_percentage", "mastery_level",
            ):
                mastery_map[topic_id] = pct
                mastery_levels[topic_id] = level

        threshold = getattr(settings, "MASTERY_THRESHOLD", 0.70)
        prereqs_map: dict[int, list[int]] = defaultdict(list)
        for rel in snapshot.prerequisites:
            prereqs_map[rel.target].append(rel.source)
        mastered_ids: set[int] = {tid for tid, pct in mastery_map.items() if pct >= threshold}

        def is_unlocked(node: int) -> bool:
            if node in prereqs_map:
                return all(pid in mastered_ids for pid in prereqs_map[node])
            parent = snapshot.tree.parent[node]
            if parent is None:
                return True
            return mastery_levels.get(parent, 0) >= 1 or parent in mastered_ids

        nodes = []
        for node in node_ids:
            name, slug = labels[node]
            kind = snapshot.kind(node)
            nodes.append({
                "id": str(node),
                "label": name,
                "slug": slug,
                "data": {
                    "label": name,
                    "slug": slug,
                    "kind": kind,
                    "parent": snapshot.tree.parent[node],
                    "pos": snapshot.pos[node],
                    "depth": snapshot.depth[node],
                    "lev": snapshot.lev.get(node) if kind == TopicKind.TOPIC else None,
                    "is_unlocked": is_unlocked(node) if user else True,
                    "mastery_pct": round(mastery_map.get(node, 0.0) * 100),
                },
            })

        edges = [
            {
                "id": f"e{rel.source}-{rel.target}",
                "source": str(rel.source),
                "target": str(rel.target),
                "prerequisite_id": rel.id,
                "weight": rel.weight,
            }
            for rel in snapshot.prerequisites
        ]
        leaf_edges = [
            {**edge, "id": f"l{edge['source']}-{edge['target']}",
             "source": str(edge["source"]), "target": str(edge["target"])}
            for edge in leaf_edges_payload(snapshot)
        ]

        payload = {
            "kb_version": snapshot.version,
            "nodes": nodes,
            "edges": edges,
            "leaf_edges": leaf_edges,
        }
        if user is not None and is_instructor(user):
            payload["warnings"] = warnings_payload(snapshot)
        return Response(PrerequisiteGraphSerializer(payload).data, status=status.HTTP_200_OK)
