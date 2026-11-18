"""
curriculum/management/commands/seed_thesis_demo.py

Management command to seed/reset the database to a clean, presentable demo state
for thesis defense.

Includes:
  - Clean curriculum hierarchy (course → section → topic) & multi-branch DAG
    prerequisite convergence, written through curriculum.services.kb.
  - Topic resources with clean educational titles.
  - Realistic 15-20 answer attempt history per demo student executed through the real
    BKT/IRT engine pipeline (process_submission), populating UserKnowledgeHistory,
    UserAbility (theta), and StudentTopicState.
  - Idempotent: Can be run repeatedly to reset the demo environment.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.timezone import now

from accounts.demo import DEMO_EMAILS, DemoPassword
from assessments.services import readiness, student_model
from curriculum.models import TopicKind
from curriculum.services import kb
from curriculum.services.graph import get_snapshot
from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    DifficultyLevel,
    Question,
    TestSessionResult,
    UserAbility,
    UserKnowledgeHistory,
    StudentTopicState,
)
from assessments.services.orchestrator import process_submission

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = (
        "Resets and seeds the database with a clean curriculum DAG topology, "
        "prerequisite convergence, and realistic student BKT/IRT learning curves "
        "for thesis defense. Demo accounts that hold answers from other sources "
        "(adaptive, test sessions, legacy) are only reset with --reset-demo-answers."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-demo-answers",
            action="store_true",
            help="Also delete answers of the demo accounts that were not written by this seed.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        foreign = (
            AssessmentAttempt.objects
            .filter(user__email__in=DEMO_EMAILS)
            .exclude(source=AttemptSource.SEED)
            .count()
        )
        if foreign and not options["reset_demo_answers"]:
            raise CommandError(
                f"The demo accounts hold {foreign} answer(s) that this seed did not write "
                "(adaptive, test-session or legacy). Re-run with --reset-demo-answers to "
                "delete them, or keep them and skip the reset."
            )

        self.stdout.write(
            self.style.MIGRATE_HEADING("=== Starting Thesis Demo Database Seeding ===")
        )

        # 1. Engine and ablation flags (D34: there is only one engine).
        self.stdout.write(
            self.style.SUCCESS(f"[OK] Engine: {student_model.ENGINE_VERSION}.")
        )
        if settings.THESIS_FLAGS != {"use_irt": True, "use_prereq_init": True}:
            self.stdout.write(
                self.style.WARNING(
                    f"[WARNING] settings.THESIS_FLAGS is {settings.THESIS_FLAGS}. "
                    "The demo expects the full model (both flags on)."
                )
            )

        demo_password = DemoPassword(self.stdout)

        with transaction.atomic():
            # 2. Build Curriculum Topics
            self.stdout.write("Setting up curriculum topic hierarchy...")

            # Created through the KB service (idempotent by slug): kinds,
            # positions, Y1–Y3 and the KB version are handled there.
            def node(slug, name, parent=None, kind=None, position=None, description=""):
                return kb.ensure_node(
                    slug=slug, name=name, parent=parent, kind=kind,
                    position=position, description=description,
                )

            cs = node("computer-science", "Computer Science", position=1,
                      description="Foundational computation, theory, and software principles.")
            ds = node("data-structures", "Data Structures", cs, TopicKind.SECTION, 1,
                      "Core structures for organizing and managing memory efficiently.")
            algo = node("algorithms", "Algorithms", cs, TopicKind.SECTION, 2,
                        "Computational procedures for solving logical problems.")
            binary_trees = node("binary-trees", "Binary Trees", ds, TopicKind.TOPIC, 1,
                                "Hierarchical structures where each node has at most two children.")
            hash_maps = node("hash-maps", "Hash Maps", ds, TopicKind.TOPIC, 2)
            sorting = node("sorting", "Sorting", algo, TopicKind.TOPIC, 1)
            graphs = node("graph-traversals", "Graph Traversals", algo, TopicKind.TOPIC, 2)
            se = node("software-engineering", "Software engineering", position=2)
            node("event-management", "event management", se, TopicKind.TOPIC, 1)
            # A topic of the CS course that converges two branches of the DAG.
            demo_topic = node("demo-topic", "Demo Topic", cs, TopicKind.TOPIC, 3)

            # 3. Setup Cross-Branch DAG Prerequisite Convergence
            self.stdout.write("Configuring multi-branch DAG prerequisite edges...")

            # Algorithms requires Data Structures
            kb.ensure_prerequisite(topic=algo, prerequisite=ds)

            # Software engineering requires Hash Maps
            kb.ensure_prerequisite(topic=se, prerequisite=hash_maps)

            # Demo Topic requires BOTH Binary Trees (DS branch) AND Graph Traversals (Algorithms branch)
            kb.ensure_prerequisite(topic=demo_topic, prerequisite=binary_trees)
            kb.ensure_prerequisite(topic=demo_topic, prerequisite=graphs)

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

            # Every account here must be listed in accounts.demo.DEMO_EMAILS.
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
                    "target_topics": [binary_trees, hash_maps],
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
                if _created or demo_password.from_env:
                    user.set_password(demo_password.value)
                    user.save()

                # Idempotent cleanup for this demo user. Answers go first: they
                # RESTRICT their test sessions and carry the linked history rows.
                AssessmentAttempt.objects.filter(user=user).delete()
                TestSessionResult.objects.filter(user=user).delete()
                StudentTopicState.objects.filter(user=user).delete()
                UserKnowledgeHistory.objects.filter(user=user).delete()
                UserAbility.objects.filter(user=user).delete()

                # Simulate ~15-20 attempts across target topics
                attempt_count = 0
                skipped_closed: list[str] = []
                # Programme order (pos, D4), so a prerequisite is answered —
                # and can become mastered — before what depends on it. The
                # demo learner goes through the same readiness gate a real one
                # does (stage 4), so anything still closed is skipped rather
                # than forced.
                snapshot = get_snapshot()
                ordered_targets = sorted(
                    student_info["target_topics"],
                    key=lambda t: snapshot.pos.get(t.pk, 0),
                )
                for topic in ordered_targets:
                    topic_questions = list(Question.objects.filter(topic=topic).prefetch_related("choices"))
                    if not topic_questions:
                        continue

                    if readiness.check_open(user=user, topic_id=topic.pk) is not None:
                        skipped_closed.append(topic.name)
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

                        attempt_count += 1

                        # Spread answers over the past 3 days for the line chart. The
                        # time is set when the seed row is written, so no other row
                        # is ever re-timed (D10).
                        offset_days = 3 - (attempt_count * 0.15)
                        simulated_time = now_ts - timedelta(days=max(0.1, offset_days))

                        # Execute submission through real orchestrator (calculates BKT/IRT & writes history)
                        process_submission(
                            user=user,
                            question_id=q.id,
                            choice_id=selected_choice.id,
                            source=AttemptSource.SEED,
                            answered_at=simulated_time,
                        )

                self.stdout.write(
                    f"  Seeded {attempt_count} attempts for {user.email} (BKT/IRT history populated)."
                )
                if skipped_closed:
                    self.stdout.write(
                        self.style.WARNING(
                            "  Skipped (prerequisites not mastered): "
                            + ", ".join(skipped_closed)
                        )
                    )

            # The readiness service is the only authority on this (stage 4):
            # the demo topic is reachable when every u ∈ Pre(w) is mastered.
            demo_user = User.objects.get(email="hybrid_demo@test.com")
            blocked = readiness.check_open(user=demo_user, topic_id=demo_topic.pk)
            if blocked is None:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] '{demo_topic.name}' is open for {demo_user.email}."
                    )
                )
            else:
                names = ", ".join(item["name"] for item in blocked.missing)
                self.stdout.write(
                    self.style.WARNING(
                        f"[INFO] '{demo_topic.name}' is still closed for {demo_user.email}; "
                        f"unmastered prerequisites: {names or '—'}."
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "=== Thesis Demo Database Seeding Completed Successfully! ===\n"
                "Demo accounts: hybrid_demo@test.com, yuta@gmail.com, alex@neuro.learn\n"
                "  (password: DEMO_PASSWORD, or the generated value printed above for new accounts)\n"
                "DAG Prerequisite Convergence:\n"
                "  - 'Demo Topic' converges from 'Binary Trees' and 'Graph Traversals'\n"
            )
        )
