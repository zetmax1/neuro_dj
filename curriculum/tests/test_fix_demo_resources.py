"""
curriculum/tests/test_fix_demo_resources.py — Unit tests for fix_demo_resource_titles management command.
"""

from io import StringIO
from django.core.management import call_command
from django.test import TestCase

from curriculum.models import Topic, TopicResource


class TestFixDemoResourceTitlesCommand(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(name="Software engineering", slug="software-engineering")
        self.res1 = TopicResource.objects.create(
            topic=self.topic,
            title="test1",
            resource_type=TopicResource.ResourceType.VIDEO,
            external_url="https://www.youtube.com/watch?v=d4li3Bk95Co&list=RDd4li3Bk95Co",
        )
        self.res2 = TopicResource.objects.create(
            topic=self.topic,
            title="2-qism 45-modul",
            resource_type=TopicResource.ResourceType.DOCUMENT,
        )

    def test_fix_demo_resource_titles_sanitizes_placeholders(self):
        out = StringIO()
        call_command("fix_demo_resource_titles", stdout=out)

        self.res1.refresh_from_db()
        self.res2.refresh_from_db()

        self.assertNotIn("test1", self.res1.title)
        self.assertNotIn("2-qism", self.res2.title)
        self.assertTrue(len(self.res1.title) > 0)
        self.assertTrue(len(self.res2.title) > 0)


    def test_fix_demo_resource_titles_is_idempotent(self):
        out1 = StringIO()
        call_command("fix_demo_resource_titles", stdout=out1)

        count_after_first_run = TopicResource.objects.count()

        out2 = StringIO()
        call_command("fix_demo_resource_titles", stdout=out2)

        count_after_second_run = TopicResource.objects.count()

        # Idempotent: row count remains identical and second run outputs clean message
        self.assertEqual(count_after_first_run, count_after_second_run)
        self.assertIn("No updates required", out2.getvalue())
