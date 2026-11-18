"""
seed_load_test — the synthetic course and learners the Locust run uses (stage 10).

V-F2 fixes the size: one course of 500 topics and 1500 prerequisites. The
topics sit in sections of 20; every prerequisite joins two topics, an earlier
one to a later one within ``--span`` places, so G_L is acyclic by
construction and the dependencies are local, as in a real course. Each topic
gets ``--questions`` items with difficulties spread over [-1.5, 1.5].

Everything goes through the code production uses: nodes and prerequisites
through ``curriculum.services.kb`` (Algorithm 2.1 and the version bump run for
every one), so the seed also exercises the KB writer at this size.

D13: the learners are ``is_simulated`` accounts named
``load-<tag>-NN@simulated.invalid``; each run passes its own ``--tag``, so it
starts from learners with no answers instead of inheriting the last run's
progress. The command refuses a database that holds any account that is not
simulated, so it can only be pointed at a database made for it
(``benchmarks/load_test.py`` uses ``<db>_locust``) and never touches real data.
The password comes from ``LOAD_TEST_PASSWORD`` and is not stored anywhere.

Idempotent: an existing course or account is reused and nothing is deleted; a
topic with fewer than ``--questions`` items is topped up.
"""

from __future__ import annotations

import os
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count

from assessments.models import Choice, Question
from curriculum.models import Topic, TopicKind, TopicPrerequisite
from curriculum.services import kb

User = get_user_model()

COURSE_SLUG = "load-course"
SECTION_SIZE = 20
CHOICES_PER_QUESTION = 4


def learner_email(tag: str, index: int) -> str:
    return f"load-{tag}-{index:02d}@simulated.invalid"


class Command(BaseCommand):
    help = "Seed the synthetic V-F2 course and simulated learners for the Locust run (D13)."

    def add_arguments(self, parser):
        parser.add_argument("--topics", type=int, default=500)
        parser.add_argument("--prerequisites", type=int, default=1500)
        parser.add_argument("--span", type=int, default=40,
                            help="A prerequisite joins topics at most this many places apart.")
        # Ten, so a learner who keeps missing a topic does not run out of items
        # before mastering it (answered-correctly items are not served again).
        parser.add_argument("--questions", type=int, default=10, help="Questions per topic.")
        parser.add_argument("--learners", type=int, default=50)
        parser.add_argument("--tag", default="manual", help="Names this run's learners.")
        parser.add_argument("--seed", type=int, default=20261020)

    def handle(self, *args, **options):
        password = os.environ.get("LOAD_TEST_PASSWORD")
        if not password:
            raise CommandError("Set LOAD_TEST_PASSWORD; the learners' password is never stored.")
        real = User.all_objects.filter(is_simulated=False)
        if real.exists():
            raise CommandError(
                f"This database holds {real.count()} account(s) that are not simulated. "
                "seed_load_test runs only on a database made for it (D13)."
            )
        if options["prerequisites"] > options["topics"] * options["span"]:
            raise CommandError("Not enough topic pairs within --span for that many prerequisites.")

        rng = random.Random(options["seed"])
        course = Topic.objects.filter(slug=COURSE_SLUG).first()
        if course is None:
            course = self._build_course(rng, options)
        else:
            self.stdout.write(f"Course {COURSE_SLUG!r} exists (id {course.pk}); reused.")
        self._questions(rng, options["questions"])
        self._learners(options["tag"], options["learners"], password)

        topics = Topic.objects.filter(kind=TopicKind.TOPIC, slug__startswith="load-t").count()
        relations = TopicPrerequisite.objects.filter(topic__slug__startswith="load-t").count()
        questions = Question.objects.filter(topic__slug__startswith="load-t").count()
        self.stdout.write(self.style.SUCCESS(
            f"course={course.pk} topics={topics} prerequisites={relations} "
            f"questions={questions} learners={options['learners']}"
        ))

    def _build_course(self, rng: random.Random, options) -> Topic:
        n = options["topics"]
        self.stdout.write(f"Building {n} topics…")
        course = kb.create_node(name="[LOAD] Synthetic course", slug=COURSE_SLUG, kind=TopicKind.COURSE)
        topics: list[Topic] = []
        section = None
        for index in range(n):
            if index % SECTION_SIZE == 0:
                number = index // SECTION_SIZE
                section = kb.create_node(
                    name=f"[LOAD] Section {number:02d}", slug=f"load-s{number:02d}",
                    parent=course, kind=TopicKind.SECTION,
                )
            topics.append(kb.create_node(
                name=f"[LOAD] Topic {index:03d}", slug=f"load-t{index:03d}",
                parent=section, kind=TopicKind.TOPIC,
            ))

        self.stdout.write(f"Adding {options['prerequisites']} prerequisites…")
        pairs: set[tuple[int, int]] = set()
        while len(pairs) < options["prerequisites"]:
            later = rng.randrange(1, n)
            earlier = rng.randrange(max(0, later - options["span"]), later)
            pairs.add((earlier, later))
        for earlier, later in sorted(pairs):
            kb.add_prerequisite(prerequisite=topics[earlier], topic=topics[later])
        return course

    def _questions(self, rng: random.Random, per_topic: int) -> None:
        topics = Topic.objects.filter(kind=TopicKind.TOPIC, slug__startswith="load-t").order_by("slug")
        have = dict(
            Question.objects.filter(topic__in=topics)
            .values_list("topic_id").annotate(n=Count("id")).values_list("topic_id", "n")
        )
        new = [
            Question(
                topic=topic,
                text=f"{topic.name}, item {k}",
                irt_difficulty=round(rng.uniform(-1.5, 1.5), 3),
            )
            for topic in topics
            for k in range(have.get(topic.pk, 0), per_topic)
        ]
        if not new:
            return
        self.stdout.write(f"Adding {len(new)} questions…")
        with transaction.atomic():
            questions = Question.objects.bulk_create(new)
            Choice.objects.bulk_create([
                Choice(question=question, text=f"option {c}", is_correct=(c == 0))
                for question in questions
                for c in range(CHOICES_PER_QUESTION)
            ])

    def _learners(self, tag: str, count: int, password: str) -> None:
        for index in range(count):
            user = User.all_objects.filter(email=learner_email(tag, index)).first()
            if user is None:
                User.objects.create_user(
                    email=learner_email(tag, index), password=password,
                    first_name="Load", last_name=f"{tag}-{index:02d}", is_simulated=True,
                )
            else:
                user.set_password(password)
                user.save(update_fields=["password"])
