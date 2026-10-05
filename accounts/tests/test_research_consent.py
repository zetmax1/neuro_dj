"""
8a: research consent, the pseudonym and what deletion means (D42, D43, D11).

Three things are checked here, and the ethics question at the defence is the
reason all three are tests rather than prose:

- consent is **off** until the learner turns it on, and a learner who never
  does loses no part of the platform;
- the pseudonym is random, unique and derived from nothing — not the id, not
  the email, not the name (D43);
- deleting an account does what D11 says it does: a consenting learner's
  answers survive under the pseudonym with the identity stripped, and a
  non-consenting learner's answers go with them.
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import ANONYMISED_EMAIL_DOMAIN, PSEUDONYM_LENGTH, new_pseudonym
from accounts.tasks import RETENTION_DAYS, gdpr_hard_delete_users
from assessments.models import AssessmentAttempt, Choice, DifficultyLevel, Question
from assessments.services.orchestrator import process_submission
from curriculum.testing import make_topic

User = get_user_model()

pytestmark = pytest.mark.django_db

CONSENT = "/api/me/consent/"


@pytest.fixture
def student():
    return User.objects.create_user(email="consent.student@example.org", password=None)


@pytest.fixture
def api(student):
    client = APIClient()
    client.force_authenticate(student)
    return client


def answer_once(user, name="t1"):
    """One real adaptive answer, so there is something an export could carry."""
    topic = make_topic(name)
    question = Question.objects.create(
        topic=topic, text="?", difficulty=DifficultyLevel.MEDIUM, irt_difficulty=0.0,
    )
    right = Choice.objects.create(question=question, text="right", is_correct=True)
    Choice.objects.create(question=question, text="wrong", is_correct=False)
    process_submission(user=user, question_id=question.pk, choice_id=right.pk)
    return topic


# ---------------------------------------------------------------------------
# D42 — consent
# ---------------------------------------------------------------------------

def test_a_new_account_has_not_consented(student):
    assert student.research_consent is False
    # Never consented is not the same as "declined at 10:04".
    assert student.research_consent_at is None


def test_registration_works_without_the_checkbox():
    response = APIClient().post(
        "/api/accounts/register/",
        {
            "email": "plain@example.org",
            "password": "Str0ng-Passphrase-42",
            "password_confirm": "Str0ng-Passphrase-42",
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    created = User.objects.get(email="plain@example.org")
    assert created.research_consent is False
    assert created.research_consent_at is None


def test_registration_can_carry_the_checkbox():
    response = APIClient().post(
        "/api/accounts/register/",
        {
            "email": "willing@example.org",
            "password": "Str0ng-Passphrase-42",
            "password_confirm": "Str0ng-Passphrase-42",
            "research_consent": True,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    created = User.objects.get(email="willing@example.org")
    assert created.research_consent is True
    assert created.research_consent_at is not None


def test_consent_is_given_and_withdrawn_through_the_endpoint(api, student):
    assert api.get(CONSENT).json() == {"research_consent": False, "research_consent_at": None}

    given = api.patch(CONSENT, {"research_consent": True}, format="json")
    assert given.status_code == 200
    assert given.json()["research_consent"] is True
    student.refresh_from_db()
    assert student.research_consent is True
    first_stamp = student.research_consent_at
    assert first_stamp is not None

    withdrawn = api.patch(CONSENT, {"research_consent": False}, format="json")
    assert withdrawn.status_code == 200
    assert withdrawn.json()["research_consent"] is False
    student.refresh_from_db()
    assert student.research_consent is False
    # Withdrawal is as much a fact as consent, so it is stamped too (D42).
    assert student.research_consent_at > first_stamp


def test_the_endpoint_never_leaks_the_pseudonym(api):
    """D43: the pseudonym is the key an export row is filed under."""
    body = api.patch(CONSENT, {"research_consent": True}, format="json").json()
    assert "research_pseudonym" in [field.name for field in User._meta.get_fields()]
    assert set(body) == {"research_consent", "research_consent_at"}

    profile = api.get("/api/accounts/profile/").json()
    assert profile["research_consent"] is True
    assert "research_pseudonym" not in profile


def test_consent_cannot_be_set_on_someone_else(api):
    """There is no id in the path, so the only account addressed is the caller."""
    other = User.objects.create_user(email="other@example.org", password=None)
    api.patch(CONSENT, {"research_consent": True, "id": other.pk}, format="json")
    other.refresh_from_db()
    assert other.research_consent is False


def test_the_profile_update_path_cannot_flip_consent(api, student):
    """Consent is its own decision, not a side effect of saving a name."""
    response = api.patch(
        "/api/accounts/profile/",
        {"first_name": "Nilufar", "research_consent": True},
        format="json",
    )
    assert response.status_code == 200
    student.refresh_from_db()
    assert student.first_name == "Nilufar"
    assert student.research_consent is False


def test_consent_is_not_a_condition_of_using_the_platform(api, student):
    """D42: a learner who declines uses the platform in full."""
    assert student.research_consent is False
    topic = answer_once(student)
    assert AssessmentAttempt.objects.filter(user=student, topic=topic).count() == 1
    assert api.get("/api/learning/trajectory/").status_code == 200
    assert api.get("/api/me/summary/").status_code == 200


def test_the_consent_endpoint_needs_an_account():
    assert APIClient().get(CONSENT).status_code == 401
    assert APIClient().patch(CONSENT, {"research_consent": True}, format="json").status_code == 401


def test_an_admin_can_filter_the_user_list_by_consent(student):
    admin = User.objects.create_user(email="admin@example.org", password=None, is_staff=True)
    admin.is_superuser = True
    admin.save(update_fields=["is_superuser"])
    student.research_consent = True
    student.save(update_fields=["research_consent"])

    client = APIClient()
    client.force_authenticate(admin)
    rows = client.get("/api/accounts/users/", {"consent": "true"}).json()["results"]
    assert [row["email"] for row in rows] == [student.email]
    assert rows[0]["research_consent"] is True

    without = client.get("/api/accounts/users/", {"consent": "false"}).json()["results"]
    assert student.email not in [row["email"] for row in without]


# ---------------------------------------------------------------------------
# D43 — the pseudonym
# ---------------------------------------------------------------------------

def test_a_pseudonym_is_assigned_when_the_row_is_created(student):
    assert re.fullmatch(r"[0-9a-f]{%d}" % PSEUDONYM_LENGTH, student.research_pseudonym)


def test_a_pseudonym_is_not_derived_from_the_account(student):
    """It must not be recomputable from a leaked user list (D43)."""
    pseudonym = student.research_pseudonym
    for part in (str(student.pk), student.email, student.email.split("@")[0]):
        assert part not in pseudonym
        assert pseudonym not in part


def test_pseudonyms_differ_between_accounts():
    users = [
        User.objects.create_user(email=f"p{index}@example.org", password=None)
        for index in range(25)
    ]
    assert len({user.research_pseudonym for user in users}) == len(users)
    assert len({new_pseudonym() for _ in range(200)}) == 200


def test_every_existing_account_got_its_own_pseudonym():
    """The migration assigns one per row, not one for the table."""
    values = list(User.all_objects.values_list("research_pseudonym", flat=True))
    assert all(values)
    assert len(set(values)) == len(values)


# ---------------------------------------------------------------------------
# D11 — what deletion means
# ---------------------------------------------------------------------------

def test_a_consenting_learner_is_anonymised_and_their_answers_survive(student):
    student.research_consent = True
    student.save(update_fields=["research_consent"])
    answer_once(student)
    pseudonym = student.research_pseudonym

    student.delete()  # soft delete
    User.all_objects.filter(pk=student.pk).update(
        deleted_at=timezone.now() - timedelta(days=RETENTION_DAYS + 1),
    )

    assert gdpr_hard_delete_users() == {"anonymised": 1, "deleted": 0}

    kept = User.all_objects.get(pk=student.pk)
    assert kept.research_pseudonym == pseudonym
    assert kept.email == f"anon-{pseudonym}@{ANONYMISED_EMAIL_DOMAIN}"
    assert kept.first_name == "" and kept.last_name == ""
    assert kept.has_usable_password() is False
    assert kept.is_active is False
    assert kept.is_anonymised is True
    # The answers are research data the learner agreed to; they stay.
    assert AssessmentAttempt.objects.filter(user_id=student.pk).count() == 1


def test_a_learner_without_consent_is_deleted_with_their_answers(student):
    answer_once(student)
    student.delete()
    User.all_objects.filter(pk=student.pk).update(
        deleted_at=timezone.now() - timedelta(days=RETENTION_DAYS + 1),
    )

    assert gdpr_hard_delete_users() == {"anonymised": 0, "deleted": 1}
    assert not User.all_objects.filter(pk=student.pk).exists()
    assert not AssessmentAttempt.objects.filter(user_id=student.pk).exists()


def test_an_account_inside_the_retention_window_is_left_alone(student):
    student.delete()
    assert gdpr_hard_delete_users() == {"anonymised": 0, "deleted": 0}
    assert User.all_objects.filter(pk=student.pk).exists()


def test_an_already_anonymised_account_is_not_processed_again(student):
    student.research_consent = True
    student.save(update_fields=["research_consent"])
    student.delete()
    User.all_objects.filter(pk=student.pk).update(
        deleted_at=timezone.now() - timedelta(days=RETENTION_DAYS + 1),
    )

    assert gdpr_hard_delete_users() == {"anonymised": 1, "deleted": 0}
    # A second nightly run must not report it again.
    assert gdpr_hard_delete_users() == {"anonymised": 0, "deleted": 0}


def test_withdrawing_consent_before_deletion_removes_the_answers(student):
    """
    The sharp edge of D42 + D11, and the reason the interface says it: a
    learner who withdraws and then deletes their account is in the
    no-consent branch, so their answers are deleted with them.
    """
    student.research_consent = True
    student.save(update_fields=["research_consent"])
    answer_once(student)

    client = APIClient()
    client.force_authenticate(student)
    client.patch(CONSENT, {"research_consent": False}, format="json")

    student.refresh_from_db()
    student.delete()
    User.all_objects.filter(pk=student.pk).update(
        deleted_at=timezone.now() - timedelta(days=RETENTION_DAYS + 1),
    )

    assert gdpr_hard_delete_users() == {"anonymised": 0, "deleted": 1}
    assert not AssessmentAttempt.objects.filter(user_id=student.pk).exists()
