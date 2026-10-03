"""
Environment record for the report: database, versions and seed (rule 4).

``test_isolated_database`` is also a guard: it fails if the suite is pointed at
the development database by accident (rule 3).
"""

from __future__ import annotations

import sys

import pytest
from django.conf import settings
from django.db import connection


@pytest.mark.django_db
def test_isolated_database():
    name = connection.settings_dict["NAME"]
    assert name == "neurolearn_verify", f"the suite must run on neurolearn_verify, not {name!r}"
    print(f"\n[env] database = {name}")


def test_record_environment(capsys):
    import django
    import networkx

    with capsys.disabled():
        print()
        print(f"[env] python      = {sys.version.split()[0]}")
        print(f"[env] django      = {django.get_version()}")
        print(f"[env] networkx    = {networkx.__version__}")
        print(f"[env] pytest      = {pytest.__version__}")
        print(f"[env] seed        = {settings.VERIFICATION_SEED}")
        print(f"[env] cache       = {settings.CACHES['default']['BACKEND']}")
