"""
D16 and audit 7.3: the refresh token is an httpOnly cookie, the access token is
returned in the body only, and every cookie endpoint is CSRF-protected.
"""

from __future__ import annotations

import secrets

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = secrets.token_urlsafe(16)


@pytest.fixture
def user():
    return User.objects.create_user(email="cookie@example.org", password=PASSWORD)


def _login(client) -> dict:
    return client.post(
        "/api/accounts/token/",
        {"email": "cookie@example.org", "password": PASSWORD},
        format="json",
    )


def _csrf(client) -> str:
    return client.get("/api/accounts/csrf/").json()["csrfToken"]


@pytest.mark.django_db
def test_login_returns_the_access_token_and_no_refresh_token(user, settings):
    response = _login(APIClient())

    assert response.status_code == 200
    body = response.json()
    assert "access" in body
    assert "refresh" not in body, "a refresh token in the body is readable by scripts"
    assert settings.JWT_REFRESH_COOKIE["name"] in response.cookies


@pytest.mark.django_db
def test_the_refresh_cookie_is_httponly_and_path_scoped(user, settings):
    cookie = _login(APIClient()).cookies[settings.JWT_REFRESH_COOKIE["name"]]

    assert cookie["httponly"] is True
    assert cookie["path"] == "/api/accounts/token/"
    assert cookie["samesite"] == "Lax"
    assert int(cookie["max-age"]) == int(
        settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
    )


@pytest.mark.django_db
def test_the_cookie_is_secure_outside_debug(user, settings):
    settings.JWT_REFRESH_COOKIE = {**settings.JWT_REFRESH_COOKIE, "secure": True}
    cookie = _login(APIClient()).cookies[settings.JWT_REFRESH_COOKIE["name"]]
    assert cookie["secure"] is True


@pytest.mark.django_db
def test_refresh_reads_the_cookie_and_rotates_it(user, settings):
    client = APIClient()
    _login(client)
    name = settings.JWT_REFRESH_COOKIE["name"]
    before = client.cookies[name].value

    response = client.post("/api/accounts/token/refresh/")

    assert response.status_code == 200
    assert set(response.json()) == {"access"}
    assert client.cookies[name].value != before


@pytest.mark.django_db
def test_the_new_access_token_authenticates(user):
    client = APIClient()
    _login(client)
    access = client.post("/api/accounts/token/refresh/").json()["access"]

    profile = APIClient().get(
        "/api/accounts/profile/", HTTP_AUTHORIZATION=f"Bearer {access}",
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == "cookie@example.org"


@pytest.mark.django_db
def test_refresh_without_a_cookie_is_401():
    response = APIClient().post("/api/accounts/token/refresh/")
    assert response.status_code == 401
    assert response.json()["code"] == "no_refresh_cookie"


@pytest.mark.django_db
def test_a_tampered_cookie_is_401_and_is_cleared(user, settings):
    client = APIClient()
    _login(client)
    name = settings.JWT_REFRESH_COOKIE["name"]
    client.cookies[name] = "not-a-token"

    response = client.post("/api/accounts/token/refresh/")

    assert response.status_code == 401
    assert response.cookies[name].value == ""


@pytest.mark.django_db
def test_logout_blacklists_the_token_and_clears_the_cookie(user, settings):
    client = APIClient()
    _login(client)
    name = settings.JWT_REFRESH_COOKIE["name"]
    token = client.cookies[name].value

    response = client.post("/api/accounts/token/logout/")

    assert response.status_code == 204
    assert response.cookies[name].value == ""
    client.cookies[name] = token
    assert client.post("/api/accounts/token/refresh/").status_code == 401


@pytest.mark.django_db
def test_logout_without_a_session_is_still_204():
    assert APIClient().post("/api/accounts/token/logout/").status_code == 204


# ---------------------------------------------------------------------------
# CSRF — the reason a cookie needs it
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_csrf_endpoint_returns_a_token_and_sets_the_cookie():
    client = APIClient()
    response = client.get("/api/accounts/csrf/")
    assert response.status_code == 200
    assert response.json()["csrfToken"]
    assert "csrftoken" in response.cookies


@pytest.mark.django_db
@pytest.mark.parametrize("path", [
    "/api/accounts/token/refresh/",
    "/api/accounts/token/logout/",
])
def test_cookie_endpoints_refuse_a_request_without_csrf(user, path):
    client = APIClient(enforce_csrf_checks=True)
    _csrf(client)  # the cookie alone is not enough
    _login_with_csrf(client)

    response = client.post(path)
    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]


@pytest.mark.django_db
def test_login_refuses_a_request_without_csrf(user):
    """Login CSRF would plant the attacker's session in the victim's browser."""
    client = APIClient(enforce_csrf_checks=True)
    response = client.post(
        "/api/accounts/token/",
        {"email": "cookie@example.org", "password": PASSWORD},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_the_whole_flow_works_with_csrf_enforced(user, settings):
    client = APIClient(enforce_csrf_checks=True)
    token = _csrf(client)
    name = settings.JWT_REFRESH_COOKIE["name"]

    login = client.post(
        "/api/accounts/token/",
        {"email": "cookie@example.org", "password": PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert login.status_code == 200
    assert name in client.cookies

    refreshed = client.post("/api/accounts/token/refresh/", HTTP_X_CSRFTOKEN=token)
    assert refreshed.status_code == 200

    logout = client.post("/api/accounts/token/logout/", HTTP_X_CSRFTOKEN=token)
    assert logout.status_code == 204


def _login_with_csrf(client) -> None:
    token = _csrf(client)
    response = client.post(
        "/api/accounts/token/",
        {"email": "cookie@example.org", "password": PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 200
