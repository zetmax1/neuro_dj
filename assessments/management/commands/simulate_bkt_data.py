import random
import time
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from assessments.models import (
    AssessmentAttempt,
    Choice,
    DifficultyLevel,
    Question,
    UserKnowledgeHistory,
    UserKnowledgeState,
)
from assessments.services.orchestrator import process_submission
from curriculum.models import Topic

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Seed curriculum and simulate student interactions for BKT testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--students",
            type=int,
            default=50,
            help="Number of students to simulate",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Wipe existing database tables before seeding",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        students_count = options["students"]
        clear = options["clear"]

        if clear:
            self._clear_database()

        # Phase 1: Curriculum
        leaf_topics = self._seed_curriculum()
        
        # Phase 2: Users
        users = self._seed_users(count=students_count)

        # Phase 3: Simulation
        self._simulate_learning(users, leaf_topics)

        self.stdout.write(self.style.SUCCESS("Simulation complete!"))

    def _clear_database(self) -> None:
        """Safely wipes the tables involved in the simulation."""
        self.stdout.write(self.style.WARNING("Clearing database..."))
        with transaction.atomic():
            AssessmentAttempt.objects.all().delete()
            UserKnowledgeHistory.objects.all().delete()
            UserKnowledgeState.objects.all().delete()
            Question.objects.all().delete()
            # Deleting topics cascades to questions/choices
            Topic.objects.all().delete()
            # Only delete generated users to preserve admins
            User.objects.filter(is_staff=False).delete()
        self.stdout.write(self.style.SUCCESS("Database cleared."))

    def _seed_curriculum(self) -> list[Topic]:
        """
        Builds a 3-level tree and populates leaf nodes with questions.
        Returns the list of leaf topics.
        """
        self.stdout.write("Seeding curriculum tree...")

        with transaction.atomic():
            # Root Level
            cs = Topic.objects.create(
                name="Computer Science", slug="computer-science", is_unlocked=True
            )

            # Child Level
            ds = Topic.objects.create(
                name="Data Structures", slug="data-structures", parent=cs, is_unlocked=False
            )
            algos = Topic.objects.create(
                name="Algorithms", slug="algorithms", parent=cs, is_unlocked=False
            )

            # Leaf Level
            binary_trees = Topic.objects.create(
                name="Binary Trees", slug="binary-trees", parent=ds, is_unlocked=False
            )
            hash_maps = Topic.objects.create(
                name="Hash Maps", slug="hash-maps", parent=ds, is_unlocked=False
            )
            sorting = Topic.objects.create(
                name="Sorting", slug="sorting", parent=algos, is_unlocked=False
            )

            leaf_topics = [binary_trees, hash_maps, sorting]

            # Generate questions for leaf topics
            choices_to_create = []
            
            for topic in leaf_topics:
                for diff_level in [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]:
                    # 5 questions per difficulty
                    for i in range(5):
                        q = Question.objects.create(
                            topic=topic,
                            text=f"{topic.name} {diff_level.label} Question {i+1}: {fake.sentence()}",
                            explanation=fake.paragraph(),
                            difficulty=diff_level,
                        )
                        # 1 correct, 3 incorrect
                        choices_to_create.append(
                            Choice(question=q, text=f"Correct Answer for Q{q.pk}", is_correct=True)
                        )
                        for j in range(3):
                            choices_to_create.append(
                                Choice(question=q, text=f"Wrong Answer {j+1} for Q{q.pk}", is_correct=False)
                            )
            
            Choice.objects.bulk_create(choices_to_create)
            
            self.stdout.write(self.style.SUCCESS(f"Created 3 leaf topics and {len(leaf_topics)*15} questions."))
            return leaf_topics

    def _seed_users(self, count: int = 50) -> list[Any]:
        """Creates realistic users using Faker."""
        self.stdout.write(f"Seeding {count} users...")
        
        users = []
        with transaction.atomic():
            for _ in range(count):
                email = fake.unique.email()
                user = User.objects.create_user(
                    email=email,
                    password="Password123!",
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} users."))
        return users

    def _simulate_learning(self, users: list[Any], leaf_topics: list[Topic]) -> None:
        """
        Simulate interactions using the BKT orchestrator.
        """
        self.stdout.write("Simulating learning processes...")
        
        start_time = time.time()
        total_interactions = 0

        # We will iterate through each user and simulate them answering questions in topics
        for idx, user in enumerate(users):
            # For each user, we pick 1 or 2 topics to focus on to show different learning paths
            topics_to_attempt = random.sample(leaf_topics, k=random.randint(1, len(leaf_topics)))
            
            for topic in topics_to_attempt:
                # User attempts 10-25 questions in this topic
                num_attempts = random.randint(10, 25)
                
                # Fetch questions for the topic
                questions = list(Question.objects.filter(topic=topic).prefetch_related('choices'))
                
                for _ in range(num_attempts):
                    # Pick a random question
                    question = random.choice(questions)
                    
                    # Weighted probability based on difficulty
                    if question.difficulty == DifficultyLevel.EASY:
                        chance = 0.80
                    elif question.difficulty == DifficultyLevel.MEDIUM:
                        chance = 0.50
                    else:  # HARD
                        chance = 0.20
                        
                    is_correct = random.random() < chance
                    
                    if is_correct:
                        # Find the correct choice
                        choice = next(c for c in question.choices.all() if c.is_correct)
                    else:
                        # Find a random wrong choice
                        wrong_choices = [c for c in question.choices.all() if not c.is_correct]
                        choice = random.choice(wrong_choices)
                        
                    # Pass through the exact same API orchestrator
                    # Note: We aren't testing 'is_unlocked' gating rigorously for this script, 
                    # but the orchestrator will update it for parents if they meet mastery threshold.
                    process_submission(
                        user=user,
                        question_id=question.id,
                        choice_id=choice.id
                    )
                    
                    total_interactions += 1
            
            # Progress update
            if (idx + 1) % 10 == 0 or (idx + 1) == len(users):
                self.stdout.write(f"Processed {idx + 1}/{len(users)} users...")

        duration = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"Simulated {total_interactions} interactions in {duration:.2f} seconds."
            )
        )
