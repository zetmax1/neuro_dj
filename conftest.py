import pytest


@pytest.fixture(autouse=True)
def _isolated_cache(settings):
    """Tests never touch the developer's Redis; each test gets an empty LocMem cache."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "neurolearn-tests",
        }
    }
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
