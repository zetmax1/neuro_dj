"""
curriculum/views/instructor.py — Instructor API views for the knowledge base.

Topics, prerequisites and warnings. Every write goes through
curriculum.services.kb; a rejected change answers 400 with
``{"reason": ..., "detail": ..., "chain": [...]}`` (chain only for cycles).

Ownership filtering:
  Non-superuser instructors see only topics they created in the parent dropdown.
  Superusers/admins see all topics.

Duration aggregation:
  The topic queryset is annotated with total_duration_minutes (Sum of related
  resources' duration_minutes) for the frontend to display dynamic course durations.

Counters for the node editor (D39):
  ``question_count`` and ``child_count`` tell the structure editor in advance
  which ``kind`` changes the KB service will accept — a section with children
  cannot become a topic (topics are leaves) and a topic holding questions
  cannot become a section (Y4). The duration is a subquery so that the two
  counts, which join other tables, cannot multiply its sum.
"""

from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsInstructor
from curriculum.models import Topic, TopicPrerequisite, TopicResource
from curriculum.serializers.instructor import (
    InstructorTopicSerializer,
    PrerequisiteSerializer,
    TopicResourceSerializer,
)
from curriculum.services import kb
from curriculum.services.graph import get_snapshot


def _duration_subquery():
    """Σ duration_minutes of a node's resources, as a subquery (see module docstring)."""
    return Coalesce(
        Subquery(
            TopicResource.objects
            .filter(topic=OuterRef("pk"))
            .values("topic")
            .annotate(total=Sum("duration_minutes"))
            .values("total")[:1],
            output_field=IntegerField(),
        ),
        Value(0),
        output_field=IntegerField(),
    )


class KBErrorMixin:
    """Turns a rejected KB change into a 400 response."""

    def handle_exception(self, exc):
        if isinstance(exc, kb.KBError):
            return Response(exc.payload(), status=status.HTTP_400_BAD_REQUEST)
        return super().handle_exception(exc)


@extend_schema(tags=["Instructor Management"])
class InstructorTopicViewSet(KBErrorMixin, viewsets.ModelViewSet):
    """
    ViewSet for instructors to Create, Read, Update, and Delete topics.
    Restricted to instructors (D15); students use the read-only endpoints in
    curriculum/views/student.py.

    Ownership filtering:
      - Superusers/staff see all topics.
      - Regular instructors see only topics they created.

    Archiving (D11):
      - DELETE removes a topic only when nothing in its subtree is referenced
        by recorded answers or test results; otherwise the whole subtree is
        archived (200, ``{"archived": true}``) so the answer ledger stays intact.
      - Archived topics are hidden unless ``?include_archived=true``.
    """
    permission_classes = [IsInstructor]
    serializer_class = InstructorTopicSerializer

    def get_queryset(self):
        queryset = (
            Topic.objects
            .annotate(
                total_duration_minutes=_duration_subquery(),
                # distinct=True: the two joins below produce a row per pair,
                # so a plain count would multiply.
                question_count=Count("questions", distinct=True),
                child_count=Count(
                    "children", distinct=True, filter=Q(children__is_archived=False),
                ),
            )
            .order_by("position", "id")
        )
        if self.request.query_params.get("include_archived", "").lower() not in ("1", "true"):
            queryset = queryset.filter(is_archived=False)
        # Non-staff instructors only see the topics they created.
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(instructor=user)
        return queryset

    def perform_create(self, serializer):
        # Auto-assign the creating user as the topic instructor
        serializer.save(instructor=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        outcome, count = kb.delete_node(instance)
        if outcome == "archived":
            return Response(
                {"id": instance.pk, "archived": True, "archived_topics": count},
                status=status.HTTP_200_OK,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="reorder")
    def reorder(self, request: Request, pk=None) -> Response:
        """
        POST {"direction": "up" | "down"} — move the node one slot among its
        siblings (D39). The whole row is renumbered in one KB change, so the
        answer is the siblings in their new order. 400 with reason ``at_edge``
        when the node is already first or last.
        """
        instance = self.get_object()
        siblings = kb.reorder_sibling(instance, direction=str(request.data.get("direction", "")))
        return Response({
            "id": instance.pk,
            "parent": instance.parent_id,
            "siblings": [
                {"id": node.pk, "name": node.name, "position": node.position}
                for node in siblings
            ],
        })


@extend_schema(tags=["Instructor Management"])
class InstructorPrerequisiteViewSet(
    KBErrorMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    E_P relations entered by instructors (BB3, BB6, BB7).

    - ``GET``: relations between active nodes; ``?course=<id>`` keeps those
      touching that course. ``?expand=leaf`` returns the inherited topic
      graph G_L instead (``inherited`` marks edges produced by section- or
      course-level relations, ``via`` lists the producing relation ids).
    - ``POST {prerequisite, topic, weight}``: Algorithm 2.1; 400 with
      ``reason`` ``self`` / ``nested`` (Y2) / ``cycle`` (Y3, with ``chain``) /
      ``duplicate`` / ``weight`` / ``archived``.
    - ``PATCH {weight}``: change ω. ``DELETE``: remove the relation.
    """
    permission_classes = [IsInstructor]
    serializer_class = PrerequisiteSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = (
            TopicPrerequisite.objects
            .filter(topic__is_archived=False, prerequisite__is_archived=False)
            .select_related("topic", "prerequisite")
        )
        course = self.request.query_params.get("course")
        if course:
            snapshot = get_snapshot()
            try:
                nodes = [n for n in snapshot.tree.parent if snapshot.root_of(n) == int(course)]
            except (KeyError, ValueError):
                nodes = []
            queryset = queryset.filter(Q(topic_id__in=nodes) | Q(prerequisite_id__in=nodes))
        return queryset.order_by("id")

    def list(self, request: Request, *args, **kwargs) -> Response:
        if request.query_params.get("expand") == "leaf":
            return Response(leaf_edges_payload(get_snapshot()))
        return super().list(request, *args, **kwargs)

    def perform_destroy(self, instance):
        kb.remove_prerequisite(instance)


def leaf_edges_payload(snapshot) -> list[dict]:
    """G_L edges with their weight, origin and the inherited flag (addendum A4-3)."""
    return [
        {
            "source": a,
            "target": b,
            "weight": edge.weight,
            "inherited": not edge.direct,
            "via": list(edge.via),
        }
        for (a, b), edge in sorted(snapshot.edges.items(), key=lambda item: (snapshot.pos[item[0][0]], snapshot.pos[item[0][1]]))
    ]


def warnings_payload(snapshot) -> dict:
    """Redundant edges and order conflicts κ (GR3) — reported, never auto-fixed."""
    return {
        "kb_version": snapshot.version,
        "redundant_edges": [
            {"source": a, "target": b, "via": list(snapshot.edges[(a, b)].via)}
            for a, b in snapshot.redundant
        ],
        "kappa": snapshot.kappa,
        "order_conflicts": [
            {"source": a, "target": b, "via": list(snapshot.edges[(a, b)].via)}
            for a, b in snapshot.conflicts
        ],
    }


@extend_schema(tags=["Instructor Management"])
class KBWarningsView(APIView):
    """GET /api/curriculum/instructor/kb/warnings/ — redundant edges and κ."""
    permission_classes = [IsInstructor]

    def get(self, request: Request) -> Response:
        return Response(warnings_payload(get_snapshot()))


@extend_schema(tags=["Instructor Management"])
class InstructorResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for instructors to manage curriculum resources.
    Supports binary file uploads (PDFs, PPTs, etc.).
    """
    permission_classes = [IsInstructor]
    serializer_class = TopicResourceSerializer
    parser_classes = (MultiPartParser, FormParser)
    queryset = TopicResource.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        return queryset
