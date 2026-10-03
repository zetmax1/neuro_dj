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
