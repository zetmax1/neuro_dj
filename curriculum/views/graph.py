"""
curriculum/views/graph.py — API view for the Prerequisite Graph endpoint.

Endpoint:
  GET /api/curriculum/prerequisite-graph/
"""

from __future__ import annotations

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
from neuro_model import readiness as r


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

    Each node also carries the learner's own state (3.4): ``p_mastery``,
    ``accuracy``, ``status``, ``mastered`` and ``missing_count``. They come
    from the one readiness service, so this endpoint, the tree and the
    dashboard report the same numbers for the same topic.
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

        # The one readiness service owns the learner's state; sections and
        # courses hold no state of their own (D22), so they report the
        # defaults. Imported here, not at module level: curriculum does not
        # depend on assessments (see curriculum/models.py).
        from assessments.services import readiness

        states = readiness.states_for(user=user, snapshot=snapshot) if user else {}

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
                    **_learner_state(states.get(node)),
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


def _learner_state(state) -> dict:
    """
    One topic's state for the graph payload.

    A node the learner has no row for reads as closed with P(L) = 0, which is
    what "never seen" means; an anonymous request gets the same defaults.
    """
    if state is None:
        return {
            "p_mastery": 0.0,
            "accuracy": 0.0,
            "status": r.CLOSED,
            "mastered": False,
            "missing_count": 0,
        }
    return {
        "p_mastery": state.p_mastery,
        "accuracy": state.accuracy,
        "status": state.status,
        "mastered": state.mastered_flag,
        "missing_count": state.missing_count,
    }
