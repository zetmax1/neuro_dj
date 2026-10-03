"""Stage 0 data-protection rules for seed and simulation commands."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from assessments.models import AssessmentAttempt
from curriculum.models import Topic

User = get_user_model()


@pytest.mark.django_db
def test_seed_data_requires_explicit_confirmation():
    Topic.objects.create(name="Keep", slug="keep")
    with pytest.raises(CommandError, match="--yes-delete-all"):
        call_command("seed_data", stdout=StringIO())
    assert Topic.objects.filter(slug="keep").exists()


@pytest.mark.django_db
def test_seed_data_refuses_when_real_users_exist():
    User.objects.create_user(email="real.student@example.org", password=None)
    Topic.objects.create(name="Keep", slug="keep")
    with pytest.raises(CommandError, match="non-demo user"):
        call_command("seed_data", "--yes-delete-all", stdout=StringIO())
    assert Topic.objects.filter(slug="keep").exists()


@pytest.mark.django_db
def test_simulator_clear_only_removes_simulated_accounts():
    real = User.objects.create_user(email="real.student@example.org", password=None)
    keep = Topic.objects.create(name="Real curriculum", slug="real-curriculum")

    call_command("simulate_bkt_data", "--students", "2", stdout=StringIO())
    simulated = User.all_objects.filter(is_simulated=True)
    assert simulated.count() == 2
    assert all(not u.has_usable_password() for u in simulated)
    assert AssessmentAttempt.objects.filter(user__is_simulated=True).exists()

    call_command("simulate_bkt_data", "--students", "1", "--clear", stdout=StringIO())
    assert User.all_objects.filter(is_simulated=True).count() == 1
    assert User.all_objects.filter(pk=real.pk).exists()
    assert Topic.objects.filter(pk=keep.pk).exists()


@pytest.mark.django_db
def test_seed_thesis_demo_takes_password_from_env(monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "env-chosen-demo-pass")
    out = StringIO()
    call_command("seed_thesis_demo", stdout=out)
    user = User.objects.get(email="hybrid_demo@test.com")
    assert user.check_password("env-chosen-demo-pass")
    assert "env-chosen-demo-pass" not in out.getvalue()


@pytest.mark.django_db
def test_seed_thesis_demo_generates_and_prints_password_once(monkeypatch):
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    out = StringIO()
    call_command("seed_thesis_demo", stdout=out)
    lines = [line for line in out.getvalue().splitlines() if line.startswith("Generated demo password")]
    assert len(lines) == 1
    generated = lines[0].rsplit(": ", 1)[1]
    assert User.objects.get(email="yuta@gmail.com").check_password(generated)
