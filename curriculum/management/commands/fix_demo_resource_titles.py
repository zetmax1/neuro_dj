"""
curriculum/management/commands/fix_demo_resource_titles.py

Management command to replace placeholder or unrelated TopicResource titles, URLs, and content
with realistic, topic-appropriate educational materials across all curriculum topics.

Idempotent: Safe to run multiple times without duplicating rows or introducing state drift.
"""

from __future__ import annotations

import re
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from curriculum.models import Topic, TopicResource


class Command(BaseCommand):
    help = (
        "Replaces placeholder, test, or unrelated TopicResource titles and links "
        "with realistic, topic-appropriate educational materials."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate resource updates without committing changes to the database.",
        )

    def handle(self, *args: Any, **options: bool) -> None:
        dry_run: bool = options.get("dry-run", False)

        self.stdout.write(
            self.style.MIGRATE_HEADING("--- Starting Demo Resource Title Sanitization ---")
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode. No changes will be saved."))

        updated_count = 0

        # Explicit mapping for known initial seeded resource IDs
        # (Resource ID -> (Title, ResourceType, ExternalURL, Content, DurationMinutes))
        explicit_updates: dict[int, tuple[str, str, str, str, int]] = {
            1: (
                "Introduction to Computer Science Lecture",
                TopicResource.ResourceType.VIDEO,
                "https://www.youtube.com/embed/zOjov-2OZ0E",
                "Foundational lecture on computational theory, abstraction, and programming paradigms.",
                15,
            ),
            9: (
                "Computer Systems & Machine Architecture Guide",
                TopicResource.ResourceType.DOCUMENT,
                "",
                "Comprehensive reference on CPU registers, instruction set architectures, and memory hierarchies.",
                20,
            ),
            10: (
                "Functional Programming Paradigm Guide",
                TopicResource.ResourceType.DOCUMENT,
                "",
                "Pure functions, immutability, higher-order functions, and lambda calculus principles.",
                12,
            ),
            11: (
                "Automated System Testing & Validation Guide",
                TopicResource.ResourceType.DOCUMENT,
                "",
                "End-to-end testing strategies, assertion libraries, and automated test runners.",
                15,
            ),
            12: (
                "Low-Level Systems & Operating System Concepts",
                TopicResource.ResourceType.DOCUMENT,
                "",
                "Process scheduling, threads, virtual memory, and file system primitives.",
                25,
            ),
            13: (
                "Asynchronous & Concurrency Patterns",
                TopicResource.ResourceType.DOCUMENT,
                "",
                "Async/await runtime mechanics, thread safety, locks, and deadlock prevention.",
                18,
            ),
            14: (
                "Software Architecture & System Design Principles",
                TopicResource.ResourceType.VIDEO,
                "https://www.youtube.com/embed/sB24n4-N_Q4",
                "Overview of modular design, microservices, and clean architecture principles.",
                22,
            ),
            15: (
                "Agile Methodologies & SDLC Frameworks",
                TopicResource.ResourceType.DOCUMENT,
                "",
                "Detailed breakdown of Scrum, Kanban, sprint planning, and retrospective practices.",
                15,
            ),
            16: (
                "SOLID Principles & Object-Oriented Design",
                TopicResource.ResourceType.TEXT_CONTENT,
                "",
                "In-depth guide to Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion.",
                14,
            ),
            17: (
                "Design Patterns in Practice (Gang of Four)",
                TopicResource.ResourceType.VIDEO,
                "https://www.youtube.com/embed/v9ejT8FO-7I",
                "Creational, Structural, and Behavioral design pattern implementations in software engineering.",
                20,
            ),
            18: (
                "Continuous Integration & CI/CD Pipelines",
                TopicResource.ResourceType.DOCUMENT,
                "",
                "Best practices for unit testing, integration tests, and automated build pipeline workflows.",
                16,
            ),
            19: (
                "Event-Driven Architecture & Message Queues",
                TopicResource.ResourceType.VIDEO,
                "https://www.youtube.com/embed/STKCRSUsyP0",
                "Understanding event loops, message brokers (RabbitMQ/Kafka), and asynchronous background processing.",
                18,
            ),
            20: (
                "Asynchronous Event Dispatching Guide",
                TopicResource.ResourceType.TEXT_CONTENT,
                "",
                "Implementing event signals, background task queues, and reactive event triggers in modern web systems.",
                12,
            ),
        }

        # Placeholder detection patterns (case-insensitive)
        placeholder_regex = re.compile(
            r"(test\d*|along\s+with|2-qism|45-modul|volkenshteyn|reyting|packt|selenium|rickroll|d4li3bk95co|l7hcfu75vwi|ghqdlifylq8)",
            re.IGNORECASE,
        )

        with transaction.atomic():
            # Step 1: Apply explicit updates to specific seeded IDs
            for res_id, (title, rtype, url, content, duration) in explicit_updates.items():
                try:
                    resource = TopicResource.objects.get(pk=res_id)
                    needs_update = (
                        resource.title != title
                        or resource.resource_type != rtype
                        or resource.external_url != url
                        or resource.content != content
                        or resource.duration_minutes != duration
                    )
                    if needs_update:
                        self.stdout.write(
                            f"  [ID {res_id}] Updating '{resource.title}' -> '{title}' ({resource.topic.name})"
                        )
                        resource.title = title
                        resource.resource_type = rtype
                        resource.external_url = url
                        resource.content = content
                        resource.duration_minutes = duration
                        if not dry_run:
                            resource.save()
                        updated_count += 1
                except TopicResource.DoesNotExist:
                    continue

            # Step 2: Generic scanner to catch any other placeholder titles/urls across all resources
            all_resources = TopicResource.objects.select_related("topic").all()
            for res in all_resources:
                if res.id in explicit_updates:
                    continue

                # Check title or external_url for leftover placeholder patterns
                is_placeholder = bool(
                    placeholder_regex.search(res.title)
                    or placeholder_regex.search(res.external_url)
                )

                if is_placeholder:
                    topic_name = res.topic.name.strip()
                    new_title = f"{topic_name} - Core Concepts & Reference"
                    new_content = f"Educational reference material covering key concepts and methods of {topic_name}."
                    
                    self.stdout.write(
                        f"  [ID {res.id}] Generic cleanup '{res.title}' -> '{new_title}' ({topic_name})"
                    )
                    res.title = new_title
                    res.content = new_content
                    if "youtube.com" in res.external_url and ("dQw4w9WgXcQ" in res.external_url or "d4li" in res.external_url):
                        res.external_url = "https://www.youtube.com/embed/zOjov-2OZ0E"
                    
                    if not dry_run:
                        res.save()
                    updated_count += 1

            # Step 3: Ensure all topics have at least one clean educational resource
            for topic in Topic.objects.all():
                if topic.resources.count() == 0:
                    title = f"Introduction to {topic.name}"
                    self.stdout.write(f"  [Topic ID {topic.id}] Creating default resource '{title}'")
                    if not dry_run:
                        TopicResource.objects.create(
                            topic=topic,
                            title=title,
                            resource_type=TopicResource.ResourceType.TEXT_CONTENT,
                            content=f"Comprehensive overview of fundamental principles, theoretical models, and practical applications in {topic.name}.",
                            duration_minutes=15,
                        )
                    updated_count += 1

            if dry_run:
                transaction.set_rollback(True)

        if updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS("All TopicResource titles are already clean and topic-appropriate. No updates required.")
            )
        else:
            msg = f"Successfully updated/sanitized {updated_count} TopicResource records."
            if dry_run:
                msg += " (Dry Run - no DB changes persisted)"
            self.stdout.write(self.style.SUCCESS(msg))
