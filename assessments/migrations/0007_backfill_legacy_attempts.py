"""
Stage 1 (D10): mark every pre-ledger answer as ``source=legacy`` and fill its
identity columns.

- ``topic``: the question's topic (the only information available);
- ``course``: the root of that topic's tree, found by walking ``parent_id``;
- ``attempt_no``: 1, 2, 3, … per (user, topic) ordered by (answered_at, id).

Legacy rows include synthetic easy-skip answers that cannot be told apart from
real ones, so they are never used in experiments. Model columns stay NULL.
No row is deleted or re-timed.
"""

from collections import defaultdict

from django.db import migrations


def _root_resolver(Topic):
    parent_of = dict(Topic.objects.values_list("id", "parent_id"))

    def root_of(topic_id):
        seen = set()
        while parent_of.get(topic_id) is not None:
            if topic_id in seen:
                raise RuntimeError(f"Topic parent chain loops at id={topic_id}")
            seen.add(topic_id)
            topic_id = parent_of[topic_id]
        return topic_id

    return root_of


def backfill_legacy_attempts(apps, schema_editor):
    Attempt = apps.get_model("assessments", "AssessmentAttempt")
    Topic = apps.get_model("curriculum", "Topic")
    root_of = _root_resolver(Topic)

    rows = (
        Attempt.objects
        .order_by("user_id", "question__topic_id", "answered_at", "id")
        .values_list("id", "user_id", "question__topic_id")
    )
    counters = defaultdict(int)
    updated = []
    for attempt_id, user_id, topic_id in rows:
        counters[(user_id, topic_id)] += 1
        updated.append(Attempt(
            id=attempt_id,
            topic_id=topic_id,
            course_id=root_of(topic_id),
            attempt_no=counters[(user_id, topic_id)],
            source="legacy",
        ))
    Attempt.objects.bulk_update(
        updated, ["topic", "course", "attempt_no", "source"], batch_size=1000,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0006_attempt_ledger_fields'),
    ]

    operations = [
        migrations.RunPython(backfill_legacy_attempts, migrations.RunPython.noop),
    ]
