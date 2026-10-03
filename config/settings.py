"""
Django settings for the NeuroLearn backend.

Every deployment-specific value is read from the environment. For local
development the values live in ``config/.env`` (gitignored); see
``config/.env.example`` for the full list. The repository-root ``.env`` is
intentionally not read. When ``config/.env`` exists its values take
precedence over the process environment, so stray shell exports cannot
silently redirect a developer machine to another database.
"""

import os
from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# DJANGO_ENV_FILE="" disables the file (CI, deployment checks).
_ENV_FILE = os.environ.get("DJANGO_ENV_FILE", str(BASE_DIR / "config" / ".env"))
if _ENV_FILE and Path(_ENV_FILE).exists():
    environ.Env.read_env(_ENV_FILE, overwrite=True)


# ---------------------------------------------------------------------------
# Core security
# ---------------------------------------------------------------------------

DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG=False.")
    # Development only: a per-process key; sessions and JWTs do not survive restarts.
    SECRET_KEY = get_random_secret_key()

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"] if DEBUG else [],
)

# Origins of the React frontend: used for CORS, CSRF and for the
# frame-ancestors policy of uploaded media (PDF viewer iframe).
FRONTEND_ORIGINS = env.list("FRONTEND_ORIGINS", default=[])
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=FRONTEND_ORIGINS)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=FRONTEND_ORIGINS)

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
    SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
    if env.bool("USE_X_FORWARDED_PROTO", default=False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'corsheaders',

    # Local apps
    'accounts',
    'curriculum',
    'assessments',
    'analytics',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'login': env("LOGIN_THROTTLE_RATE", default="5/minute"),
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------------------------------------------------------
# Database (PostgreSQL; SQLite is not supported for tests — see D1)
# ---------------------------------------------------------------------------

DATABASES = {
    'default': env.db("DATABASE_URL"),
}
DATABASES['default'].setdefault('CONN_MAX_AGE', env.int("DB_CONN_MAX_AGE", default=0))


# ---------------------------------------------------------------------------
# Cache: Redis when REDIS_URL is set, otherwise in-process LocMem.
# Redis outages are swallowed so that cache problems never turn into 500s.
# ---------------------------------------------------------------------------

REDIS_URL = env("REDIS_URL", default="")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 1,
                "SOCKET_TIMEOUT": 1,
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "neurolearn",
        }
    }
DJANGO_REDIS_IGNORE_EXCEPTIONS = True
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = "accounts.CustomUser"

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}


# ---------------------------------------------------------------------------
# Internationalization, static and media files
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = env("STATIC_ROOT", default=str(BASE_DIR / 'staticfiles'))

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / 'media')))

UNFOLD = {
    "SITE_TITLE": "NeuroLearn Administration",
    "SITE_HEADER": "NeuroLearn Admin",
    "SITE_URL": "/",
    "STYLES": [
        lambda request: "/static/css/admin_custom.css",
    ],
}


# ---------------------------------------------------------------------------
# Background tasks
# ---------------------------------------------------------------------------

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="memory://")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="cache+memory://")
CELERY_TIMEZONE = TIME_ZONE

SPECTACULAR_SETTINGS = {
    'TITLE': 'NeuroLearn API',
    'DESCRIPTION': 'API documentation for the NeuroLearn platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'jwt': []}],
}


# ---------------------------------------------------------------------------
# Adaptive learning engine (legacy, replaced in stages 3–4)
# ---------------------------------------------------------------------------

STUDENT_MODEL_ENGINE = env("STUDENT_MODEL_ENGINE", default="hybrid_bkt_irt")
MASTERY_THRESHOLD = 0.70


# ---------------------------------------------------------------------------
# Thesis model constants (chapter II). Single source of truth; every value
# can be overridden with an environment variable of the form THESIS_<NAME>.
# ---------------------------------------------------------------------------

_THESIS_DEFAULTS = {
    "TAU": 0.95,          # mastery threshold τ
    "DELTA": 0.10,        # hysteresis width δ
    "G_MAX": 0.30,        # upper bound of P(G)
    "S_MAX": 0.10,        # upper bound of P(S)
    "A_Q": 1.0,           # item discrimination a_q (0 => classical BKT)
    "ELO_ALPHA": 0.8,     # K(n) = ELO_ALPHA / (1 + ELO_BETA * n)
    "ELO_BETA": 0.05,
    "LAMBDA": 0.5,        # weight of prerequisites in P(L0)
    "C_OFFSET": 0.05,     # P(L0) cap c = TAU - C_OFFSET
    "THETA_CLAMP": 4.0,   # numerical safeguard, not part of chapter II
    "DEFAULT_P0": 0.15,
    "DEFAULT_PT": 0.20,
    "DEFAULT_G0": 0.20,
    "DEFAULT_S0": 0.05,
    # D25 data policy, not part of chapter II: a question answered again within
    # this many hours is logged as review_repeat and does not update P(L).
    "REVIEW_REPEAT_HOURS": 24.0,
}
THESIS_MODEL = {
    name: env.float(f"THESIS_{name}", default=default)
    for name, default in _THESIS_DEFAULTS.items()
}
