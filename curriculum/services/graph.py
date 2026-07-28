"""
curriculum/services/graph.py — Prerequisite DAG operations and algorithms.

Provides graph traversal, topological sorting (Kahn's algorithm), and DAG-based
unlocking checks for multi-prerequisite topics.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Any

from django.apps import apps
from django.conf import settings
from django.db.models import QuerySet

from curriculum.models import Topic, TopicPrerequisite

logger = logging.getLogger(__name__)


def get_all_prerequisites(topic: Topic) -> set[Topic]:
    """
    Compute the full transitive closure of prerequisite topics for `topic`.

    Iteratively collects all direct and indirect prerequisites by traversing
    the Directed Acyclic Graph (DAG) backwards.
    """
    visited_ids: set[int] = set()
    stack: list[int] = [topic.id]

    while stack:
        curr_id = stack.pop()
        prereq_ids = TopicPrerequisite.objects.filter(
            topic_id=curr_id
        ).values_list("prerequisite_id", flat=True)

        for p_id in prereq_ids:
            if p_id not in visited_ids and p_id != topic.id:
                visited_ids.add(p_id)
                stack.append(p_id)

    return set(Topic.objects.filter(id__in=visited_ids))


def topological_order(topic_queryset: QuerySet[Topic] | list[Topic]) -> list[Topic]:
    """
    Perform Kahn's algorithm topological sort over TopicPrerequisite edges,
    restricted to topics in `topic_queryset`.

    Ordering rule:
      If topic A requires topic B, B will appear BEFORE A in the returned list.
      Ties are resolved deterministically by position/id.
    """
    topics_list = list(topic_queryset)
    if not topics_list:
        return []

    topic_map: dict[int, Topic] = {t.id: t for t in topics_list}
    node_ids: set[int] = set(topic_map.keys())

    # Build in-degree map and adjacency list (prerequisite -> dependent_topic)
    in_degree: dict[int, int] = {t_id: 0 for t_id in node_ids}
    adj: dict[int, list[int]] = defaultdict(list)

    edges = TopicPrerequisite.objects.filter(
        topic_id__in=node_ids,
        prerequisite_id__in=node_ids,
    ).values_list("prerequisite_id", "topic_id")

    for prereq_id, dep_id in edges:
        in_degree[dep_id] += 1
        adj[prereq_id].append(dep_id)

    # Nodes with 0 in-degree (no prerequisites within node_ids)
    zero_in_degree = sorted(
        [t_id for t_id in node_ids if in_degree[t_id] == 0],
        key=lambda tid: (topic_map[tid].position, topic_map[tid].id),
    )
    queue = deque(zero_in_degree)

    sorted_ids: list[int] = []
    while queue:
        curr_id = queue.popleft()
        sorted_ids.append(curr_id)

        neighbors = sorted(
            adj[curr_id],
            key=lambda tid: (topic_map[tid].position, topic_map[tid].id),
        )
        for nbr_id in neighbors:
            in_degree[nbr_id] -= 1
            if in_degree[nbr_id] == 0:
                queue.append(nbr_id)

    # Append any remaining node_ids if disconnected or cycle edge cases exist
    if len(sorted_ids) < len(node_ids):
        remaining = sorted(
            [tid for tid in node_ids if tid not in set(sorted_ids)],
            key=lambda tid: (topic_map[tid].position, topic_map[tid].id),
        )
        sorted_ids.extend(remaining)

    return [topic_map[t_id] for t_id in sorted_ids]


def is_unlocked_dag(user: Any, topic: Topic) -> bool:
    """
    Determine whether a topic is unlocked for a user based on DAG prerequisites.

    Unlocking condition:
      - If topic has explicit TopicPrerequisite edges:
        Returns True ONLY IF ALL prerequisite topics have user's
        `mastery_percentage` (from UserKnowledgeState) >= settings.MASTERY_THRESHOLD.
      - If topic has NO TopicPrerequisite edges:
        Falls back to parent tree status: root topics (parent_id=None) are unlocked;
        child topics require parent topic mastery >= MASTERY_THRESHOLD.
    """
    raw_threshold = getattr(settings, "MASTERY_THRESHOLD", 0.70)
    threshold = raw_threshold / 100.0 if raw_threshold > 1.0 else float(raw_threshold)

    prereq_qs = TopicPrerequisite.objects.filter(topic=topic)
    prereq_count = prereq_qs.count()

    if prereq_count > 0:
        if user is None or not getattr(user, "is_authenticated", False):
            return False

        UserKnowledgeState = apps.get_model("assessments", "UserKnowledgeState")
        prereq_ids = list(prereq_qs.values_list("prerequisite_id", flat=True))

        mastered_count = UserKnowledgeState.objects.filter(
            user=user,
            topic_id__in=prereq_ids,
            mastery_percentage__gte=threshold,
        ).count()

        return mastered_count == prereq_count

    # Fallback when no explicit prerequisites exist:
    if topic.parent_id is None:
        return True

    if user is None or not getattr(user, "is_authenticated", False):
        return True

    UserKnowledgeState = apps.get_model("assessments", "UserKnowledgeState")
    parent_state = UserKnowledgeState.objects.filter(
        user=user,
        topic_id=topic.parent_id,
    ).first()

    if parent_state:
        return parent_state.mastery_percentage >= threshold
    return True
