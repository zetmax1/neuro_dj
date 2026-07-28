from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = "Initializes default user groups and assigns permissions for RBAC."

    def handle(self, *args, **options) -> None:
        self.stdout.write("Setting up RBAC groups and permissions...")

        # 1. Define groups
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        instructor_group, _ = Group.objects.get_or_create(name="Instructor")
        student_group, _ = Group.objects.get_or_create(name="Student")

        # 2. Get content types
        # Note: TopicResource won't exist until we run migrations, but setup_roles can run after migrate.
        try:
            from curriculum.models import Topic, TopicResource
            from assessments.models import Question, Choice

            content_types = {
                "topic": ContentType.objects.get_for_model(Topic),
                "topicresource": ContentType.objects.get_for_model(TopicResource),
                "question": ContentType.objects.get_for_model(Question),
                "choice": ContentType.objects.get_for_model(Choice),
            }
        except Exception as e:
            self.stderr.write(f"Warning: Models not fully loaded or migrated yet: {e}")
            return

        # 3. Create or fetch permission helpers
        def get_perms(model_name: str, actions: list[str]) -> list[Permission]:
            ct = content_types[model_name]
            perms = []
            for action in actions:
                codename = f"{action}_{model_name}"
                try:
                    perm = Permission.objects.get(codename=codename, content_type=ct)
                    perms.append(perm)
                except Permission.DoesNotExist:
                    self.stderr.write(f"Permission {codename} not found for model {model_name}")
            return perms

        # 4. Assign permissions to Instructor
        instructor_actions = ["add", "change", "delete", "view"]
        instructor_perms = []
        for model in ["topic", "topicresource", "question", "choice"]:
            instructor_perms.extend(get_perms(model, instructor_actions))
        instructor_group.permissions.set(instructor_perms)

        # 5. Assign permissions to Student (Read-Only)
        student_perms = []
        for model in ["topic", "topicresource", "question", "choice"]:
            student_perms.extend(get_perms(model, ["view"]))
        student_group.permissions.set(student_perms)

        # 6. Assign all permissions to Admin
        all_perms = Permission.objects.filter(
            content_type__app_label__in=["curriculum", "assessments"]
        )
        admin_group.permissions.set(all_perms)

        self.stdout.write(self.style.SUCCESS("Successfully configured groups: Admin, Instructor, Student."))
