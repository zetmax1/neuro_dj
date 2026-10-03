import pytest


@pytest.fixture(autouse=True)
def _isolated_cache(settings):
    """
    Tests never touch the developer's Redis; each test gets an empty LocMem
    cache and a fresh per-thread KB snapshot (the database is reset between
    tests, so KB version numbers repeat).
    """
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "neurolearn-tests",
        }
    }
    from django.core.cache import cache

    from curriculum.services.graph import clear_local_cache

    cache.clear()
    clear_local_cache()
    yield
    cache.clear()
    clear_local_cache()


# Fixtures that give a test database access; the first one present is set up
# before the singleton below is checked.
_DB_FIXTURES = ("transactional_db", "django_db_reset_sequences", "db", "_django_db_helper")


@pytest.fixture(autouse=True)
def _kb_version_singleton(request):
    """
    The knowledge-base version row is an invariant created by migration 0011,
    and the KB service never recreates it (D31) — a counter that restarted at 1
    would make a cached snapshot of the previous KB look current.

    ``transaction=True`` tests truncate every table after each test, which takes
    the row with it, so the harness puts it back. Production code does not.
    """
    present = [name for name in _DB_FIXTURES if name in request.fixturenames]
    if not present:
        return
    request.getfixturevalue(present[0])

    from curriculum.kb_guard import kb_write
    from curriculum.models import KnowledgeBaseVersion

    if not KnowledgeBaseVersion.objects.filter(pk=1).exists():
        with kb_write():
            KnowledgeBaseVersion.objects.create(pk=1, version=1)
