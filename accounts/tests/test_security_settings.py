"""Stage 0 security settings: env-driven config, Redis resilience, JWT blacklist, media framing."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory
from rest_framework.test import APIClient

User = get_user_model()
BASE_DIR = Path(settings.BASE_DIR)


def _run_settings(env_overrides):
    env = {k: v for k, v in os.environ.items() if k not in {"SECRET_KEY", "DEBUG"}}
    env.update({"DJANGO_ENV_FILE": "", "DATABASE_URL": "postgres://u:p@127.0.0.1:1/db"})
    env.update(env_overrides)
    code = "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup()"
    return subprocess.run([sys.executable, "-c", code], cwd=BASE_DIR, env=env, capture_output=True, text=True)


def test_secret_key_is_required_when_debug_is_off():
    result = _run_settings({"DEBUG": "False"})
    assert result.returncode != 0
    assert "SECRET_KEY must be set" in result.stderr


def test_debug_defaults_to_false_and_hardening_is_on():
    assert settings.X_FRAME_OPTIONS == "DENY"
    assert not getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False)
    assert "rest_framework_simplejwt.token_blacklist" in settings.INSTALLED_APPS
    assert settings.DJANGO_REDIS_IGNORE_EXCEPTIONS is True
    result = _run_settings({"SECRET_KEY": "x" * 50})
    assert result.returncode == 0, result.stderr


def test_thesis_constants_match_decision_d6():
    expected = {
        "TAU": 0.95, "DELTA": 0.10, "G_MAX": 0.30, "S_MAX": 0.10, "A_Q": 1.0,
        "ELO_ALPHA": 0.8, "ELO_BETA": 0.05, "LAMBDA": 0.5, "C_OFFSET": 0.05,
        "THETA_CLAMP": 4.0, "DEFAULT_P0": 0.15, "DEFAULT_PT": 0.20,
        "DEFAULT_G0": 0.20, "DEFAULT_S0": 0.05,
    }
    for name, value in expected.items():
        assert settings.THESIS_MODEL[name] == pytest.approx(value), name


@pytest.mark.django_db
@pytest.mark.parametrize(
    "cache_backend",
    [
        {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        {
            # Nothing listens on port 1: simulates a Redis outage.
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://127.0.0.1:1/0",
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient", "SOCKET_CONNECT_TIMEOUT": 0.2},
        },
    ],
    ids=["locmem", "redis-down"],
)
def test_topic_writes_survive_cache_backend(settings, cache_backend):
    settings.CACHES = {"default": cache_backend}
    teacher = User.objects.create_user(email="t@example.org", password=None)
    teacher.groups.add(Group.objects.get_or_create(name="Instructor")[0])
    client = APIClient()
    client.force_authenticate(user=teacher)

    created = client.post("/api/curriculum/instructor/topics/", {"name": "A", "slug": "a"}, format="json")
    assert created.status_code == 201
    topic_id = created.json()["id"]
    assert client.patch(f"/api/curriculum/instructor/topics/{topic_id}/", {"name": "B"}, format="json").status_code == 200
    assert client.delete(f"/api/curriculum/instructor/topics/{topic_id}/").status_code == 204


@pytest.mark.django_db
def test_rotated_refresh_token_is_blacklisted():
    password = secrets.token_urlsafe(16)
    User.objects.create_user(email="jwt@example.org", password=password)
    client = APIClient()
    tokens = client.post("/api/accounts/token/", {"email": "jwt@example.org", "password": password}, format="json").json()

    first = client.post("/api/accounts/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert first.status_code == 200
    reused = client.post("/api/accounts/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert reused.status_code == 401


def test_media_can_be_framed_only_by_frontend_origins(settings, tmp_path):
    from config.media import serve_media

    settings.MEDIA_ROOT = tmp_path
    settings.FRONTEND_ORIGINS = ["http://localhost:8080"]
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")

    response = serve_media(RequestFactory().get("/media/doc.pdf"), "doc.pdf")
    assert response.status_code == 200
    assert response["Content-Security-Policy"] == "frame-ancestors 'self' http://localhost:8080"
    assert getattr(response, "xframe_options_exempt", False) is True
