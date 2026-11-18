"""
Stage 10, audit 7.1 (“``accounts`` has no tests”): the account lifecycle end
to end, filling what the per-decision files leave open.

- Registration: a new account is a student, consent is off, privilege fields
  in the request are ignored, duplicates (soft-deleted ones too), mismatched
  and weak passwords are refused.
- Roles (D15, Q0-6): one table — role, the instructor endpoints and the admin
  endpoints agree for every kind of account.
- Profile: only the name can be edited; DELETE is a soft delete that ends
  every way back in (password, access token, refresh cookie). A refresh
  cookie that outlives its account is a 401 that clears it — it was a 500.
- D11 at the end of the retention window: an admin's DELETE is the same soft
  delete, and an anonymised account cannot sign in again.
- D16: the rotated cookie keeps every attribute, logout expires the cookie on
  its own path, and rotation blacklists exactly the retired token.
- CSRF: a token that does not match the cookie is refused, not just a missing one.

Cookie, consent, pseudonym and admin-role details already covered elsewhere
(``test_auth_cookies``, ``test_research_consent``, ``test_user_admin``,
``test_permissions``) are not repeated.
"""

from __future__ import annotations

import secrets
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.permissions import get_role, is_admin, is_instructor
from accounts.tasks import RETENTION_DAYS, gdpr_hard_delete_users

User = get_user_model()
PASSWORD = secrets.token_urlsafe(16)

INSTRUCTOR_ENDPOINT = "/api/assessments/instructor/questions/"
ADMIN_ENDPOINT = "/api/accounts/users/"


def _register(client, **fields):
    body = {
        "email": "new.learner@example.org",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
        **fields,
    }
    return client.post("/api/accounts/register/", body, format="json")


def _login(client, email, password=PASSWORD):
    return client.post(
        "/api/accounts/token/", {"email": email, "password": password}, format="json",
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_registration_creates_a_student_who_can_sign_in():
    client = APIClient()
    response = _register(client, first_name="Ali")

    assert response.status_code == 201
    assert "password" not in response.json() and "password_confirm" not in response.json()
    user = User.objects.get(email="new.learner@example.org")
    assert list(user.groups.values_list("name", flat=True)) == ["Student"]
    assert get_role(user) == "student" and not is_instructor(user)
    assert not (user.is_staff or user.is_superuser)
    assert user.research_consent is False and user.research_consent_at is None
    assert user.check_password(PASSWORD) and user.password != PASSWORD  # hashed

    assert _login(APIClient(), "new.learner@example.org").status_code == 200


@pytest.mark.django_db
def test_registration_ignores_privilege_fields():
    """A self-registered account can never start as staff, admin or instructor."""
    response = _register(
        APIClient(), is_staff=True, is_superuser=True, role="admin",
        groups=["Admin", "Instructor"], is_simulated=True,
    )

    assert response.status_code == 201
    user = User.objects.get(email="new.learner@example.org")
    assert not (user.is_staff or user.is_superuser or user.is_simulated)
    assert get_role(user) == "student"


@pytest.mark.django_db
def test_registration_refuses_an_email_that_exists_even_soft_deleted():
    User.objects.create_user(email="taken@example.org", password=None)
    gone = User.objects.create_user(email="gone@example.org", password=None)
    gone.delete()  # soft delete: the address stays reserved

    for email in ("taken@example.org", "gone@example.org"):
        response = _register(APIClient(), email=email)
        assert response.status_code == 400
        assert "email" in response.json()
    assert User.all_objects.filter(email="gone@example.org").count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(("password", "confirm"), [
    ("a-Long-enough-pass-1", "a-Long-enough-pass-2"),  # mismatch
    ("12345678901", "12345678901"),                    # numeric and common
    ("Ab1", "Ab1"),                                    # too short
    ("password", "password"),                          # common
])
def test_registration_refuses_bad_passwords(password, confirm):
    response = _register(APIClient(), password=password, password_confirm=confirm)

    assert response.status_code == 400
    assert "password" in response.json()
    assert not User.all_objects.filter(email="new.learner@example.org").exists()


# ---------------------------------------------------------------------------
# Roles (D15, Q0-6): one rule, three places that read it
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize(("groups", "flags", "role"), [
    ((), {}, "student"),
    (("Student",), {}, "student"),
    (("Instructor",), {}, "instructor"),
    ((), {"is_staff": True}, "instructor"),
    (("Admin",), {}, "admin"),
    ((), {"is_staff": True, "is_superuser": True}, "admin"),
])
def test_role_permissions_and_endpoints_agree(groups, flags, role):
    user = User.objects.create_user(email="role@example.org", password=None, **flags)
    for name in groups:
        user.groups.add(Group.objects.get_or_create(name=name)[0])
    client = APIClient()
    client.force_authenticate(user=user)

    assert get_role(user) == role
    assert client.get("/api/accounts/profile/").json()["role"] == role
    assert is_instructor(user) == (role != "student")
    assert is_admin(user) == (role == "admin")
    assert client.get(INSTRUCTOR_ENDPOINT).status_code == (200 if role != "student" else 403)
    assert client.get(ADMIN_ENDPOINT).status_code == (200 if role == "admin" else 403)


def test_an_anonymous_visitor_has_no_role_rights():
    anonymous = AnonymousUser()
    assert not is_instructor(anonymous) and not is_admin(anonymous)
    assert not is_instructor(None)


# ---------------------------------------------------------------------------
# Profile and the learner's own delete
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_the_profile_edits_the_name_and_nothing_else():
    user = User.objects.create_user(email="me@example.org", password=None)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        "/api/accounts/profile/",
        {"first_name": "Nodira", "email": "other@example.org", "is_staff": True},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert (user.first_name, user.email, user.is_staff) == ("Nodira", "me@example.org", False)


@pytest.mark.django_db
def test_deleting_the_account_is_soft_and_closes_every_way_back_in(settings):
    user = User.objects.create_user(email="leaving@example.org", password=PASSWORD)
    client = APIClient()
    access = _login(client, "leaving@example.org").json()["access"]
    name = settings.JWT_REFRESH_COOKIE["name"]
    refresh_cookie = client.cookies[name].value

    response = APIClient().delete("/api/accounts/profile/", HTTP_AUTHORIZATION=f"Bearer {access}")

    assert response.status_code == 204
    row = User.all_objects.get(pk=user.pk)
    assert row.is_deleted and not row.is_active and row.deleted_at is not None
    assert not User.objects.filter(pk=user.pk).exists()  # hidden from the default manager
    # Password, access token and refresh cookie all stop working.
    assert _login(APIClient(), "leaving@example.org").status_code == 401
    assert APIClient().get(
        "/api/accounts/profile/", HTTP_AUTHORIZATION=f"Bearer {access}",
    ).status_code == 401
    replay = APIClient()
    replay.cookies[name] = refresh_cookie
    assert replay.post("/api/accounts/token/refresh/").status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("end", ["soft_deleted", "deactivated", "hard_deleted"])
def test_a_refresh_cookie_outliving_its_account_is_401_and_cleared(settings, end):
    """It used to be a 500 for a deleted account and a 401 that kept the cookie for a deactivated one."""
    user = User.objects.create_user(email="ended@example.org", password=PASSWORD)
    client = APIClient()
    _login(client, "ended@example.org")
    if end == "soft_deleted":
        user.delete()
    elif end == "deactivated":
        User.objects.filter(pk=user.pk).update(is_active=False)
    else:
        user.hard_delete()

    response = client.post("/api/accounts/token/refresh/")

    assert response.status_code == 401
    assert response.json()["code"] == "token_not_valid"
    assert response.cookies[settings.JWT_REFRESH_COOKIE["name"]].value == ""


# ---------------------------------------------------------------------------
# D11 through the admin path
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_client():
    admin = User.objects.create_user(email="admin@example.org", password=None)
    admin.groups.add(Group.objects.get_or_create(name="Admin")[0])
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("consent", [True, False])
def test_an_admin_delete_is_soft_and_retention_applies_d11(admin_client, consent):
    learner = User.objects.create_user(
        email="learner@example.org", password=PASSWORD, research_consent=consent,
    )

    assert admin_client.delete(f"{ADMIN_ENDPOINT}{learner.pk}/").status_code == 204
    row = User.all_objects.get(pk=learner.pk)
    assert row.is_deleted and not row.is_active
    assert gdpr_hard_delete_users() == {"anonymised": 0, "deleted": 0}  # inside the window

    User.all_objects.filter(pk=learner.pk).update(
        deleted_at=timezone.now() - timedelta(days=RETENTION_DAYS + 1),
    )
    if consent:
        assert gdpr_hard_delete_users() == {"anonymised": 1, "deleted": 0}
        anonymised = User.all_objects.get(pk=learner.pk)
        assert anonymised.is_anonymised and not anonymised.has_usable_password()
        assert _login(APIClient(), anonymised.email).status_code == 401
    else:
        assert gdpr_hard_delete_users() == {"anonymised": 0, "deleted": 1}
        assert not User.all_objects.filter(pk=learner.pk).exists()
    assert _login(APIClient(), "learner@example.org").status_code == 401


# ---------------------------------------------------------------------------
# D16: cookie attributes survive rotation; logout; blacklist
# ---------------------------------------------------------------------------

@pytest.fixture
def account():
    return User.objects.create_user(email="jwt.cookie@example.org", password=PASSWORD)


@pytest.mark.django_db
def test_the_rotated_cookie_keeps_httponly_secure_samesite_and_path(account, settings):
    settings.JWT_REFRESH_COOKIE = {**settings.JWT_REFRESH_COOKIE, "secure": True, "samesite": "Strict"}
    client = APIClient()
    _login(client, account.email)

    rotated = client.post("/api/accounts/token/refresh/").cookies[settings.JWT_REFRESH_COOKIE["name"]]

    assert rotated["httponly"] is True
    assert rotated["secure"] is True
    assert rotated["samesite"] == "Strict"
    assert rotated["path"] == "/api/accounts/token/"


@pytest.mark.django_db
def test_logout_expires_the_cookie_on_its_own_path(account, settings):
    client = APIClient()
    _login(client, account.email)

    cleared = client.post("/api/accounts/token/logout/").cookies[settings.JWT_REFRESH_COOKIE["name"]]

    # A deletion on another path would leave the real cookie in the browser.
    assert cleared.value == ""
    assert cleared["path"] == "/api/accounts/token/"
    assert int(cleared["max-age"]) == 0


@pytest.mark.django_db
def test_rotation_blacklists_exactly_the_retired_token(account, settings):
    client = APIClient()
    _login(client, account.email)
    name = settings.JWT_REFRESH_COOKIE["name"]
    retired = RefreshToken(client.cookies[name].value)

    assert client.post("/api/accounts/token/refresh/").status_code == 200
    current = RefreshToken(client.cookies[name].value)

    blacklisted = set(BlacklistedToken.objects.values_list("token__jti", flat=True))
    assert blacklisted == {retired["jti"]}
    assert current["jti"] not in blacklisted
    assert client.post("/api/accounts/token/refresh/").status_code == 200  # the new one works


# ---------------------------------------------------------------------------
# CSRF: a wrong token, not only a missing one
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("path", [
    "/api/accounts/token/",
    "/api/accounts/token/refresh/",
    "/api/accounts/token/logout/",
])
def test_a_csrf_token_that_does_not_match_the_cookie_is_refused(account, path):
    client = APIClient(enforce_csrf_checks=True)
    client.get("/api/accounts/csrf/")  # sets the csrftoken cookie
    forged = APIClient(enforce_csrf_checks=True).get("/api/accounts/csrf/").json()["csrfToken"]

    response = client.post(
        path, {"email": account.email, "password": PASSWORD}, format="json",
        HTTP_X_CSRFTOKEN=forged,
    )

    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]
