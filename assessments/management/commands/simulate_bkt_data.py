import random
import time
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from assessments.models import Choice, DifficultyLevel, Question
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
            help="Delete previously simulated users (is_simulated=True) and their data first",
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
        """Delete simulated accounts only; their attempts and states cascade with them."""
        self.stdout.write(self.style.WARNING("Removing simulated users and their data..."))
        with transaction.atomic():
            deleted, _ = User.all_objects.filter(is_simulated=True).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} simulated row(s)."))

    def _seed_curriculum(self) -> list[Topic]:
        """
        Ensure a separate 3-level simulation tree (slugs prefixed with "sim-") and
        return its leaf topics. Existing curriculum rows are never touched.
        """
        self.stdout.write("Ensuring simulation curriculum tree...")

        with transaction.atomic():
            cs, _ = Topic.objects.get_or_create(
                slug="sim-computer-science",
                defaults={"name": "[SIM] Computer Science", "is_unlocked": True},
            )
            ds, _ = Topic.objects.get_or_create(
                slug="sim-data-structures",
                defaults={"name": "[SIM] Data Structures", "parent": cs, "is_unlocked": False},
            )
            algos, _ = Topic.objects.get_or_create(
                slug="sim-algorithms",
                defaults={"name": "[SIM] Algorithms", "parent": cs, "is_unlocked": False},
            )
            leaf_specs = [
                ("sim-binary-trees", "[SIM] Binary Trees", ds),
                ("sim-hash-maps", "[SIM] Hash Maps", ds),
                ("sim-sorting", "[SIM] Sorting", algos),
            ]

            leaf_topics = []
            choices_to_create = []
            for slug, name, parent in leaf_specs:
                topic, created = Topic.objects.get_or_create(
                    slug=slug, defaults={"name": name, "parent": parent, "is_unlocked": False},
                )
                leaf_topics.append(topic)
                if not created:
                    continue
                for diff_level in [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]:
                    for i in range(5):
                        q = Question.objects.create(
                            topic=topic,
                            text=f"{topic.name} {diff_level.label} Question {i+1}: {fake.sentence()}",
                            explanation=fake.paragraph(),
                            difficulty=diff_level,
                        )
                        choices_to_create.append(
                            Choice(question=q, text=f"Correct Answer for Q{q.pk}", is_correct=True)
                        )
                        for j in range(3):
                            choices_to_create.append(
                                Choice(question=q, text=f"Wrong Answer {j+1} for Q{q.pk}", is_correct=False)
                            )

            Choice.objects.bulk_create(choices_to_create)
            return leaf_topics

    def _seed_users(self, count: int = 50) -> list[Any]:
        """Creates simulated accounts (is_simulated=True, no usable password)."""
        self.stdout.write(f"Seeding {count} simulated users...")

        users = []
        with transaction.atomic():
            for _ in range(count):
                user = User.objects.create_user(
                    email=f"sim-{fake.unique.uuid4()}@simulated.invalid",
                    password=None,
                    first_name="Simulated",
                    last_name="Student",
                    is_simulated=True,
                )
                users.append(user)

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} simulated users."))
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
