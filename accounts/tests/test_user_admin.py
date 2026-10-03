"""
Addendum 2.7: the admin user page — roles, the simulated flag, deactivation.

Access follows the ``admin`` role the API reports (D15), not ``is_staff``.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from accounts.permissions import get_role

User = get_user_model()


def _client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def admin():
    user = User.objects.create_user(email="admin@example.org", password=None)
    user.groups.add(Group.objects.get_or_create(name="Admin")[0])
    return user


@pytest.fixture
def learner():
    return User.objects.create_user(email="learner@example.org", password=None)


def _rows(response):
    data = response.json()
    return data["results"] if isinstance(data, dict) else data


@pytest.mark.django_db
def test_an_admin_group_member_who_is_not_staff_can_manage_users(admin, learner):
    """The old IsAdminUser guard checked is_staff and locked this admin out."""
    assert admin.is_staff is False
    response = _client(admin).get("/api/accounts/users/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_a_staff_instructor_cannot_manage_users(learner):
    staff = User.objects.create_user(email="staff@example.org", password=None, is_staff=True)
    assert get_role(staff) == "instructor"
    assert _client(staff).get("/api/accounts/users/").status_code == 403


@pytest.mark.django_db
def test_a_student_cannot_manage_users(learner):
    assert _client(learner).get("/api/accounts/users/").status_code == 403


@pytest.mark.django_db
def test_the_list_reports_role_and_simulated(admin, learner):
    User.objects.create_user(email="sim@example.org", password=None, is_simulated=True)
    rows = {row["email"]: row for row in _rows(_client(admin).get("/api/accounts/users/"))}

    assert rows["learner@example.org"]["role"] == "student"
    assert rows["admin@example.org"]["role"] == "admin"
    assert rows["sim@example.org"]["is_simulated"] is True
    assert rows["learner@example.org"]["is_simulated"] is False


@pytest.mark.django_db
def test_filters_by_role_and_by_simulated(admin, learner):
    User.objects.create_user(email="sim@example.org", password=None, is_simulated=True)
    client = _client(admin)

    students = {row["email"] for row in _rows(client.get("/api/accounts/users/?role=student"))}
    assert students == {"learner@example.org", "sim@example.org"}

    real = {row["email"] for row in _rows(client.get("/api/accounts/users/?simulated=false"))}
    assert "sim@example.org" not in real
    assert "learner@example.org" in real


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["instructor", "admin", "student"])
def test_an_admin_assigns_a_role(admin, learner, role):
    response = _client(admin).patch(
        f"/api/accounts/users/{learner.pk}/", {"role": role}, format="json",
    )
    assert response.status_code == 200
    assert response.json()["role"] == role
    learner.refresh_from_db()
    assert get_role(learner) == role


@pytest.mark.django_db
def test_changing_role_replaces_the_previous_one(admin, learner):
    client = _client(admin)
    client.patch(f"/api/accounts/users/{learner.pk}/", {"role": "admin"}, format="json")
    client.patch(f"/api/accounts/users/{learner.pk}/", {"role": "instructor"}, format="json")
    learner.refresh_from_db()
    assert set(learner.groups.values_list("name", flat=True)) == {"Instructor"}


@pytest.mark.django_db
def test_a_superuser_cannot_be_demoted(admin):
    root = User.objects.create_superuser(email="root@example.org", password="x-unused-x")
    response = _client(admin).patch(
        f"/api/accounts/users/{root.pk}/", {"role": "student"}, format="json",
    )
    assert response.status_code == 400
    assert response.json()["reason"] == ["superuser"]


@pytest.mark.django_db
def test_a_staff_member_cannot_become_a_student(admin):
    staff = User.objects.create_user(email="staff@example.org", password=None, is_staff=True)
    response = _client(admin).patch(
        f"/api/accounts/users/{staff.pk}/", {"role": "student"}, format="json",
    )
    assert response.status_code == 400
    assert response.json()["reason"] == ["staff"]


@pytest.mark.django_db
def test_an_admin_cannot_change_their_own_role(admin):
    response = _client(admin).patch(
        f"/api/accounts/users/{admin.pk}/", {"role": "student"}, format="json",
    )
    assert response.status_code == 400
    assert response.json()["reason"] == ["self"]


@pytest.mark.django_db
def test_deactivation_is_reversible(admin, learner):
    client = _client(admin)

    off = client.patch(f"/api/accounts/users/{learner.pk}/", {"is_active": False}, format="json")
    assert off.status_code == 200 and off.json()["is_active"] is False
    learner.refresh_from_db()
    assert learner.is_active is False and learner.is_deleted is False

    on = client.patch(f"/api/accounts/users/{learner.pk}/", {"is_active": True}, format="json")
    assert on.json()["is_active"] is True


@pytest.mark.django_db
def test_an_unknown_role_is_refused(admin, learner):
    response = _client(admin).patch(
        f"/api/accounts/users/{learner.pk}/", {"role": "owner"}, format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_put_is_not_allowed(admin, learner):
    response = _client(admin).put(
        f"/api/accounts/users/{learner.pk}/", {"role": "student"}, format="json",
    )
    assert response.status_code == 405
