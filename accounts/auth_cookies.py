"""
accounts/auth_cookies.py — the refresh token lives in an httpOnly cookie (D16).

Audit 7.3 found both JWTs in ``localStorage``, where any script on the page —
an injected one included — can read them. The split D16 prescribes:

- the **access token** is returned in the response body and kept in memory by
  the SPA only; it is short-lived and lost on reload;
- the **refresh token** is set as an ``HttpOnly`` cookie, so no script can read
  it, scoped to ``/api/accounts/token/`` so it is sent to the token endpoints
  and nowhere else, ``Secure`` outside DEBUG, and ``SameSite`` (``Lax`` by
  default).

A cookie the browser sends on its own is a CSRF target, so every endpoint
that reads or sets it — login, refresh, logout — checks Django's CSRF token.
The SPA fetches it from ``GET /api/accounts/csrf/`` and sends it back in the
``X-CSRFToken`` header. Login is covered too: without it an attacker could
plant their own session in the victim's browser (login CSRF).

Rotation and blacklisting are SimpleJWT's (``ROTATE_REFRESH_TOKENS``,
``BLACKLIST_AFTER_ROTATION``): every refresh issues a new cookie and retires
the old token, and logout blacklists the current one.
"""

from __future__ import annotations

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck


def cookie_settings() -> dict:
    return settings.JWT_REFRESH_COOKIE


def set_refresh_cookie(response, token: str) -> None:
    """Attach the refresh token as an httpOnly cookie on ``response``."""
    options = cookie_settings()
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    response.set_cookie(
        options["name"],
        token,
        max_age=int(lifetime.total_seconds()),
        path=options["path"],
        domain=options["domain"],
        secure=options["secure"],
        httponly=True,
        samesite=options["samesite"],
    )


def clear_refresh_cookie(response) -> None:
    options = cookie_settings()
    response.delete_cookie(
        options["name"],
        path=options["path"],
        domain=options["domain"],
        samesite=options["samesite"],
    )


def read_refresh_cookie(request) -> str | None:
    return request.COOKIES.get(cookie_settings()["name"]) or None


def enforce_csrf(request) -> None:
    """
    Django's CSRF check for one request, the way DRF's SessionAuthentication
    runs it. DRF views are CSRF-exempt by default because token auth needs no
    CSRF; these endpoints use a cookie, so they opt back in explicitly.

    ``request`` is the underlying Django ``HttpRequest``.
    """
    def _no_response(_request):  # pragma: no cover - never called
        return None

    check = CSRFCheck(_no_response)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")
