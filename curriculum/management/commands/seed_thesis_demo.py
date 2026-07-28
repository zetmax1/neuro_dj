"""
curriculum/management/commands/seed_thesis_demo.py

Management command to seed/reset the database to a clean, presentable demo state
for thesis defense.

Includes:
  - Clean MPTT curriculum hierarchy & multi-branch DAG prerequisite convergence.
  - Topic resources with clean educational titles.
  - Realistic 15-20 answer attempt history per demo student executed through the real
    BKT/IRT engine pipeline (process_submission), populating UserKnowledgeHistory,
    UserAbility (theta), and UserKnowledgeState.
  - Idempotent: Can be run repeatedly to reset the demo environment.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from curriculum.models import Topic, TopicPrerequisite
from curriculum.services.graph import is_unlocked_dag
from assessments.models import (
    AssessmentAttempt,
    Choice,
    DifficultyLevel,
    Question,
    UserAbility,
    UserKnowledgeHistory,
    UserKnowledgeState,
)
from assessments.services.orchestrator import process_submission

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = (
        "Resets and seeds the database with a clean curriculum DAG topology, "
        "prerequisite convergence, and realistic student BKT/IRT learning curves "
        "for thesis defense."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            self.style.MIGRATE_HEADING("=== Starting Thesis Demo Database Seeding ===")
        )

        # 1. Engine Check
        active_engine = getattr(settings, "STUDENT_MODEL_ENGINE", "streak")
        if active_engine != "hybrid_bkt_irt":
            self.stdout.write(
                self.style.WARNING(
                    f"[WARNING] settings.STUDENT_MODEL_ENGINE is currently '{active_engine}'. "
                    f"For thesis demo, 'hybrid_bkt_irt' is strongly recommended."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("[OK] Student model engine confirmed as 'hybrid_bkt_irt'.")
            )

        with transaction.atomic():
            # 2. Build Curriculum Topics (MPTT Hierarchy)
            self.stdout.write("Setting up curriculum topic hierarchy...")

            cs, _ = Topic.objects.get_or_create(
                slug="computer-science",
                defaults={
                    "name": "Computer Science",
                    "description": "Foundational computation, theory, and software principles.",
                    "position": 1,
                    "is_unlocked": True,
                },
            )

            ds, _ = Topic.objects.get_or_create(
                slug="data-structures",
                defaults={
                    "name": "Data Structures",
                    "description": "Core structures for organizing and managing memory efficiently.",
                    "parent": cs,
                    "position": 1,
                    "is_unlocked": True,
                },
            )

            algo, _ = Topic.objects.get_or_create(
                slug="algorithms",
                defaults={
                    "name": "Algorithms",
                    "description": "Computational procedures for solving logical problems.",
                    "parent": cs,
                    "position": 2,
                    "is_unlocked": True,
                },
            )

            binary_trees, _ = Topic.objects.get_or_create(
                slug="binary-trees",
                defaults={
                    "name": "Binary Trees",
                    "description": "Hierarchical structures where each node has at most two children.",
                    "parent": ds,
                    "position": 1,
                    "is_unlocked": True,
                },
            )

            hash_maps, _ = Topic.objects.get_or_create(
                slug="hash-maps",
                defaults={
                    "name": "Hash Maps",
                    "description": "Key-value mapping data structures utilizing hash functions.",
                    "parent": ds,
                    "position": 2,
                    "is_unlocked": True,
                },
            )

            sorting, _ = Topic.objects.get_or_create(
                slug="sorting",
                defaults={
                    "name": "Sorting",
                    "description": "Algorithms for ordering elements (QuickSort, MergeSort).",
                    "parent": algo,
                    "position": 1,
                    "is_unlocked": True,
                },
            )

            graphs, _ = Topic.objects.get_or_create(
                slug="graph-traversals",
                defaults={
                    "name": "Graph Traversals",
                    "description": "Techniques for visiting nodes in network graphs (BFS/DFS).",
                    "parent": algo,
                    "position": 2,
                    "is_unlocked": True,
                },
            )

            se, _ = Topic.objects.get_or_create(
                slug="software-engineering",
                defaults={
                    "name": "Software engineering",
                    "description": "System architecture, lifecycle models, and engineering practices.",
                    "position": 2,
                    "is_unlocked": True,
                },
            )

            events, _ = Topic.objects.get_or_create(
                slug="event-management",
                defaults={
                    "name": "event management",
                    "description": "Event-driven architecture and asynchronous event loops.",
                    "parent": se,
                    "position": 1,
                    "is_unlocked": True,
                },
            )

            demo_topic, _ = Topic.objects.get_or_create(
                slug="demo-topic",
                defaults={
                    "name": "Demo Topic",
                    "description": "Advanced capstone module integrating tree and graph algorithms.",
                    "position": 3,
                    "is_unlocked": True,
                },
            )

            # Rebuild MPTT tree pointers
            Topic.objects.rebuild()

            # 3. Setup Cross-Branch DAG Prerequisite Convergence
            self.stdout.write("Configuring multi-branch DAG prerequisite edges...")

            # Algorithms requires Data Structures
            TopicPrerequisite.objects.get_or_create(topic=algo, prerequisite=ds)

            # Software engineering requires Hash Maps
            TopicPrerequisite.objects.get_or_create(topic=se, prerequisite=hash_maps)

            # Demo Topic requires BOTH Binary Trees (DS branch) AND Graph Traversals (Algorithms branch)
            TopicPrerequisite.objects.get_or_create(topic=demo_topic, prerequisite=binary_trees)
            TopicPrerequisite.objects.get_or_create(topic=demo_topic, prerequisite=graphs)

            # 4. Clean Resource Titles
            self.stdout.write("Sanitizing resource titles...")
            call_command("fix_demo_resource_titles")

            # 5. Create Questions & Choices for Assessment
            self.stdout.write("Ensuring assessment questions exist...")

            questions_spec = [
                # Binary Trees Questions
                {
                    "topic": binary_trees,
                    "text": "What is the worst-case time complexity of searching in an unbalanced BST?",
                    "explanation": "If the tree degenerates into a linked list, search complexity is O(n).",
                    "difficulty": DifficultyLevel.MEDIUM,
                    "b": 0.3,
                    "choices": [("O(1)", False), ("O(log n)", False), ("O(n)", True), ("O(n log n)", False)],
                },
                {
                    "topic": binary_trees,
                    "text": "Which tree traversal visits Root first, then Left subtree, then Right subtree?",
                    "explanation": "Pre-order traversal visits Node, Left, Right.",
                    "difficulty": DifficultyLevel.EASY,
                    "b": -0.5,
                    "choices": [("In-order", False), ("Pre-order", True), ("Post-order", False), ("Level-order", False)],
                },
                {
                    "topic": binary_trees,
                    "text": "In an AVL tree, what is the maximum allowed height difference between subtrees of any node?",
                    "explanation": "An AVL tree maintains balance with a balance factor of at most 1.",
                    "difficulty": DifficultyLevel.HARD,
                    "b": 1.1,
                    "choices": [("0", False), ("1", True), ("2", False), ("Unlimited", False)],
                },
                # Hash Maps Questions
                {
                    "topic": hash_maps,
                    "text": "What is the average-case lookup complexity in a Hash Map?",
                    "explanation": "Average hash table lookup is O(1).",
                    "difficulty": DifficultyLevel.EASY,
                    "b": -0.8,
                    "choices": [("O(1)", True), ("O(log n)", False), ("O(n)", False), ("O(n log n)", False)],
                },
                {
                    "topic": hash_maps,
                    "text": "Which collision handling technique stores colliding keys in linked list buckets?",
                    "explanation": "Separate chaining uses linked lists for bucket collisions.",
                    "difficulty": DifficultyLevel.MEDIUM,
                    "b": 0.2,
                    "choices": [("Linear Probing", False), ("Separate Chaining", True), ("Double Hashing", False)],
                },
                # Graphs Questions
                {
                    "topic": graphs,
                    "text": "Which queue structure is used to implement Breadth-First Search (BFS)?",
                    "explanation": "BFS uses a FIFO queue to visit nodes level-by-level.",
                    "difficulty": DifficultyLevel.EASY,
                    "b": -0.4,
                    "choices": [("FIFO Queue", True), ("LIFO Stack", False), ("Priority Queue", False)],
                },
                {
                    "topic": graphs,
                    "text": "Which algorithm finds single-source shortest paths in weighted graphs with non-negative weights?",
                    "explanation": "Dijkstra's algorithm computes shortest path trees in O(E + V log V).",
                    "difficulty": DifficultyLevel.MEDIUM,
                    "b": 0.5,
                    "choices": [("Kruskal", False), ("Dijkstra", True), ("Floyd-Warshall", False)],
                },
                # Demo Topic Questions
                {
                    "topic": demo_topic,
                    "text": "Which combined data structure enables O(1) key lookups alongside LRU queue ordering?",
                    "explanation": "Combining a Hash Map with a Doubly Linked List enables O(1) LRU operations.",
                    "difficulty": DifficultyLevel.MEDIUM,
                    "b": 0.4,
                    "choices": [("Hash Map + Doubly Linked List", True), ("Binary Tree + Stack", False), ("Heap + Queue", False)],
                },
                {
                    "topic": demo_topic,
                    "text": "What is the topological sort ordering constraint in a Directed Acyclic Graph (DAG)?",
                    "explanation": "Topological ordering requires that for every directed edge u -> v, u comes before v.",
                    "difficulty": DifficultyLevel.HARD,
                    "b": 0.9,
                    "choices": [("u comes before v", True), ("v comes before u", False), ("Random order", False)],
                },
            ]

            for q_data in questions_spec:
                q, _created = Question.objects.get_or_create(
                    topic=q_data["topic"],
                    text=q_data["text"],
                    defaults={
                        "explanation": q_data["explanation"],
                        "difficulty": q_data["difficulty"],
                        "irt_difficulty": q_data["b"],
                        "irt_discrimination": 1.2,
                    },
                )
                for choice_text, is_correct in q_data["choices"]:
                    Choice.objects.get_or_create(
                        question=q,
                        text=choice_text,
                        defaults={"is_correct": is_correct},
                    )

            # 6. Seed Demo Student Users and Simulate Algorithmic Attempts
            self.stdout.write("Simulating student learning curves through algorithmic engine pipeline...")

            demo_students_info = [
                {
                    "email": "hybrid_demo@test.com",
                    "first_name": "Demo",
                    "last_name": "Student",
                    "target_topics": [binary_trees, graphs, hash_maps, demo_topic],
                    "target_accuracy": 0.85,
                },
                {
                    "email": "yuta@gmail.com",
                    "first_name": "Yuta",
                    "last_name": "Okkotsu",
                    "target_topics": [binary_trees, graphs, sorting],
                    "target_accuracy": 0.60,
                },
                {
                    "email": "alex@neuro.learn",
                    "first_name": "Alex",
                    "last_name": "Rivera",
                    "target_topics": [cs, ds, hash_maps],
                    "target_accuracy": 0.30,
                },
            ]

            now_ts = now()

            for student_info in demo_students_info:
                email = student_info["email"]
                user, _created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": student_info["first_name"],
                        "last_name": student_info["last_name"],
                        "is_active": True,
                    },
                )
                if _created or not user.check_password("password123"):
                    user.set_password("password123")
                    user.save()

                # Idempotent cleanup for this demo user
                AssessmentAttempt.objects.filter(user=user).delete()
                UserKnowledgeState.objects.filter(user=user).delete()
                UserKnowledgeHistory.objects.filter(user=user).delete()
                UserAbility.objects.filter(user=user).delete()

                # Simulate ~15-20 attempts across target topics
                attempt_count = 0
                for topic in student_info["target_topics"]:
                    topic_questions = list(Question.objects.filter(topic=topic).prefetch_related("choices"))
                    if not topic_questions:
                        continue

                    # Simulate 5-6 attempts per topic
                    for step in range(6):
                        q = topic_questions[step % len(topic_questions)]
                        
                        # Decide correctness based on step progression to simulate learning curve
                        if student_info["target_accuracy"] >= 0.80:
                            is_correct = (step >= 1)  # Mostly correct (high mastery)
                        elif student_info["target_accuracy"] >= 0.50:
                            is_correct = (step % 2 == 0)  # Mixed trajectory
                        else:
                            is_correct = (step == 0)  # Mostly incorrect (low mastery)

                        correct_choice = q.choices.filter(is_correct=True).first()
                        incorrect_choice = q.choices.filter(is_correct=False).first()
                        selected_choice = correct_choice if is_correct else (incorrect_choice or correct_choice)

                        if not selected_choice:
                            continue

                        # Execute submission through real orchestrator (calculates BKT/IRT & writes history)
                        res = process_submission(
                            user=user,
                            question_id=q.id,
                            choice_id=selected_choice.id,
                        )

                        attempt_count += 1

                        # Spread attempt timestamps backward slightly over the past 3 days for line chart
                        latest_attempt = AssessmentAttempt.objects.filter(user=user).order_by("-id").first()
                        latest_history = UserKnowledgeHistory.objects.filter(user=user, topic=topic).order_by("-id").first()

                        offset_days = 3 - (attempt_count * 0.15)
                        simulated_time = now_ts - timedelta(days=max(0.1, offset_days))

                        if latest_attempt:
                            AssessmentAttempt.objects.filter(pk=latest_attempt.pk).update(answered_at=simulated_time)
                        if latest_history:
                            UserKnowledgeHistory.objects.filter(pk=latest_history.pk).update(created_at=simulated_time)

                self.stdout.write(
                    f"  Seeded {attempt_count} attempts for {user.email} (BKT/IRT history populated)."
                )

            # Verification of DAG unlock condition for demo student
            demo_user = User.objects.get(email="hybrid_demo@test.com")
            dag_unlocked = is_unlocked_dag(demo_user, demo_topic)
            if dag_unlocked:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Demo Topic DAG unlock check PASSED: '{demo_topic.name}' is unlocked for {demo_user.email}."
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"[FAIL] Demo Topic DAG unlock check FAILED: '{demo_topic.name}' is NOT unlocked for {demo_user.email}."
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "=== Thesis Demo Database Seeding Completed Successfully! ===\n"
                "Demo Credentials:\n"
                "  - Email: hybrid_demo@test.com  | Password: password123\n"
                "  - Email: yuta@gmail.com        | Password: password123\n"
                "  - Email: alex@neuro.learn      | Password: password123\n"
                "DAG Prerequisite Convergence:\n"
                "  - 'Demo Topic' converges from 'Binary Trees' and 'Graph Traversals'\n"
            )
        )
