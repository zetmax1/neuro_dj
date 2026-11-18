import pytest


def _django_available() -> bool:
    """
    Whether this interpreter can run the Django suite at all.

    ``experiments/`` is deliberately Django-free and is run from
    ``experiments/.venv``, which has torch and pandas but no Django and no
    pytest-django (see experiments/README.md). The autouse fixtures below are
    for the Django suite, so in that interpreter they must stand aside rather
    than fail at setup for every test in the file.
    """
    try:
        import django  # noqa: F401
        import pytest_django  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


@pytest.fixture(autouse=True)
def _isolated_cache(request):
    """
    Tests never touch the developer's Redis; each test gets an empty LocMem
    cache and a fresh per-thread KB snapshot (the database is reset between
    tests, so KB version numbers repeat).
    """
    if not _django_available():
        yield
        return
    settings = request.getfixturevalue("settings")
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
    if not _django_available():
        return
    present = [name for name in _DB_FIXTURES if name in request.fixturenames]
    if not present:
        return
    request.getfixturevalue(present[0])

    from curriculum.kb_guard import kb_write
    from curriculum.models import KnowledgeBaseVersion

    if not KnowledgeBaseVersion.objects.filter(pk=1).exists():
        with kb_write():
            KnowledgeBaseVersion.objects.create(pk=1, version=1)
