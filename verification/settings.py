"""
verification/settings.py — Django settings for the verification suite.

Identical to ``config.settings`` except that the tests run against their own
database (``neurolearn_verify``) in the same compose Postgres service, so the
development database is never touched (rule 3), and against a private LocMem
cache, so the developer's Redis is never touched.

Run with:  pytest -c verification/pytest.ini
"""

from config.settings import *  # noqa: F401,F403
from config.settings import DATABASES as _DEV_DATABASES

DATABASES = {"default": dict(_DEV_DATABASES["default"])}
DATABASES["default"]["TEST"] = {"NAME": "neurolearn_verify"}

# Stage 9's benchmark app is routed to its own alias (D63). The H4 checks build
# and deliberately corrupt trees there, in a test database of their own: the
# benchmark database itself (``<db>_bench``) is never opened.
DATABASES["benchmark"] = dict(_DEV_DATABASES["benchmark"])
DATABASES["benchmark"]["TEST"] = {"NAME": "neurolearn_verify_bench"}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "neurolearn-verification",
    }
}

# Fixed seed for every random process in the suite (rule 4); also printed by
# verification/tests/test_env.py into the report.
VERIFICATION_SEED = 20261003
