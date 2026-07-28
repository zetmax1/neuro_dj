"""
curriculum/management/commands/benchmark_tree.py — Tree Traversal Benchmark.

Compares the performance of MPTT (nested set, lft/rght range queries)
against Recursive CTE (django-tree-queries style) for get_descendants()
at three different tree depths: shallow, medium, and deep.

Usage:
    python manage.py benchmark_tree [--topic-id <id>] [--iterations <n>]

Output:
    A formatted ASCII table suitable for pasting directly into a thesis
    "Natijalar" (Results) section.

Methodology:
    - MPTT: Uses the actual django-mptt get_descendants() which generates
      a WHERE lft BETWEEN ... AND rght SQL query (O(1) indexed lookup).
    - Recursive CTE: Simulated using raw SQL WITH RECURSIVE ... to match
      what django-tree-queries would produce. This is a fair comparison
      because the CTE is exactly the SQL that django-tree-queries generates.
    - Each measurement is repeated `--iterations` times and averaged.
    - SQL query count is captured via django.test.utils.CaptureQueriesContext.
"""

from __future__ import annotations

import time
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from curriculum.models import Topic


class Command(BaseCommand):
    help = (
        "Benchmark MPTT (lft/rght) vs Recursive CTE get_descendants() "
        "at shallow/medium/deep tree depths."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--topic-id",
            type=int,
            default=None,
            help="Root topic ID to benchmark from. Defaults to the first root.",
        )
        parser.add_argument(
            "--iterations",
            type=int,
            default=100,
            help="Number of iterations per measurement (default: 100).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        topic_id = options["topic_id"]
        iterations = options["iterations"]

        if topic_id:
            try:
                root = Topic.objects.get(pk=topic_id)
            except Topic.DoesNotExist:
                raise CommandError(f"Topic with id={topic_id} not found.")
        else:
            root = Topic.objects.filter(parent__isnull=True).first()
            if not root:
                raise CommandError("No root topics found. Seed data first.")

        self.stdout.write(
            f"\n{'='*72}\n"
            f"  Tree Traversal Benchmark: MPTT vs Recursive CTE\n"
            f"  Root Topic: {root.name} (id={root.pk})\n"
            f"  Iterations per measurement: {iterations}\n"
            f"  Database: {connection.vendor}\n"
            f"{'='*72}\n"
        )

        # Build test subjects at three depths:
        # Shallow = root itself (level 0)
        # Medium  = first child of root (level 1) if exists
        # Deep    = first grandchild (level 2) if exists, else deepest available
        depths = self._select_depth_topics(root)

        results = []
        for label, topic in depths:
            desc_count = topic.get_descendants().count()
            mptt_result = self._benchmark_mptt(topic, iterations)
            cte_result = self._benchmark_cte(topic, iterations)
            results.append({
                "depth": label,
                "topic": topic.name,
                "level": topic.level,
                "descendants": desc_count,
                "mptt_queries": mptt_result["queries"],
                "mptt_time_ms": mptt_result["avg_ms"],
                "cte_queries": cte_result["queries"],
                "cte_time_ms": cte_result["avg_ms"],
            })

        self._print_table(results)

    def _select_depth_topics(self, root: Topic) -> list[tuple[str, Topic]]:
        """Select topics at shallow/medium/deep levels relative to root."""
        depths: list[tuple[str, Topic]] = [("Shallow (root)", root)]

        children = root.get_children()
        if children.exists():
            child = children.first()
            depths.append(("Medium (child)", child))

            grandchildren = child.get_children()
            if grandchildren.exists():
                depths.append(("Deep (grandchild)", grandchildren.first()))
            else:
                # If no grandchildren, use the child with most descendants
                best = max(children, key=lambda c: c.get_descendant_count())
                if best != child:
                    depths.append(("Deep (alt child)", best))

        return depths

    def _benchmark_mptt(
        self, topic: Topic, iterations: int
    ) -> dict[str, Any]:
        """Benchmark MPTT's native get_descendants() (lft/rght range query)."""
        # Warm-up
        list(topic.get_descendants())

        # Count SQL queries on a single run
        with CaptureQueriesContext(connection) as ctx:
            list(topic.get_descendants())
        query_count = len(ctx)

        # Time multiple iterations
        start = time.perf_counter()
        for _ in range(iterations):
            list(topic.get_descendants())
        elapsed = time.perf_counter() - start

        return {
            "queries": query_count,
            "avg_ms": round((elapsed / iterations) * 1000, 3),
        }

    def _benchmark_cte(
        self, topic: Topic, iterations: int
    ) -> dict[str, Any]:
        """
        Benchmark Recursive CTE approach (simulates django-tree-queries).

        This executes the exact recursive CTE SQL that django-tree-queries
        would generate for get_descendants().
        """
        cte_sql = """
            WITH RECURSIVE topic_tree AS (
                SELECT id, parent_id, name, 0 AS depth
                FROM curriculum_topic
                WHERE id = %s
                UNION ALL
                SELECT t.id, t.parent_id, t.name, tt.depth + 1
                FROM curriculum_topic t
                INNER JOIN topic_tree tt ON t.parent_id = tt.id
            )
            SELECT id, name, depth FROM topic_tree WHERE id != %s
            ORDER BY depth
        """

        # Warm-up
        with connection.cursor() as cursor:
            cursor.execute(cte_sql, [topic.pk, topic.pk])
            cursor.fetchall()

        # Count SQL queries
        with CaptureQueriesContext(connection) as ctx:
            with connection.cursor() as cursor:
                cursor.execute(cte_sql, [topic.pk, topic.pk])
                cursor.fetchall()
        query_count = len(ctx)

        # Time multiple iterations
        start = time.perf_counter()
        for _ in range(iterations):
            with connection.cursor() as cursor:
                cursor.execute(cte_sql, [topic.pk, topic.pk])
                cursor.fetchall()
        elapsed = time.perf_counter() - start

        return {
            "queries": query_count,
            "avg_ms": round((elapsed / iterations) * 1000, 3),
        }

    def _print_table(self, results: list[dict[str, Any]]) -> None:
        """Print results as a formatted ASCII table for thesis."""
        # Header
        header = (
            f"{'Depth':<22} │ {'Topic':<20} │ {'Level':>5} │ "
            f"{'Desc.':>5} │ {'MPTT Queries':>12} │ {'MPTT Time':>10} │ "
            f"{'CTE Queries':>11} │ {'CTE Time':>10} │ {'Speedup':>8}"
        )
        separator = "─" * len(header)

        self.stdout.write(f"\n{separator}")
        self.stdout.write(header)
        self.stdout.write(separator)

        for r in results:
            speedup = (
                r["cte_time_ms"] / r["mptt_time_ms"]
                if r["mptt_time_ms"] > 0
                else float("inf")
            )
            row = (
                f"{r['depth']:<22} │ {r['topic']:<20} │ {r['level']:>5} │ "
                f"{r['descendants']:>5} │ {r['mptt_queries']:>12} │ "
                f"{r['mptt_time_ms']:>8.3f}ms │ {r['cte_queries']:>11} │ "
                f"{r['cte_time_ms']:>8.3f}ms │ {speedup:>6.2f}x"
            )
            self.stdout.write(row)

        self.stdout.write(separator)
        self.stdout.write(
            "\nNote: MPTT uses a single indexed WHERE lft BETWEEN ... AND rght query."
        )
        self.stdout.write(
            "      CTE uses WITH RECURSIVE ... which re-traverses the tree each time.\n"
        )
