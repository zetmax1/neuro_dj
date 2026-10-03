"""
Helpers shared by the demo/seed management commands.

Demo passwords are never stored in the repository: they come from the
DEMO_PASSWORD environment variable or are generated once per command run.
"""

from __future__ import annotations

import os
import secrets

from django.contrib.auth import get_user_model
from django.db.models import Q

DEMO_EMAILS: tuple[str, ...] = (
    "hybrid_demo@test.com",
    "yuta@gmail.com",
    "alex@neuro.learn",
)


class DemoPassword:
    """Resolves the demo password lazily and reports a generated one only once."""

    def __init__(self, stdout=None) -> None:
        self._stdout = stdout
        self._value: str | None = None
        self.from_env = bool(os.environ.get("DEMO_PASSWORD"))

    @property
    def value(self) -> str:
        if self._value is None:
            env_value = os.environ.get("DEMO_PASSWORD")
            if env_value:
                self._value = env_value
            else:
                self._value = secrets.token_urlsafe(12)
                if self._stdout is not None:
                    self._stdout.write(
                        "Generated demo password (shown once, set DEMO_PASSWORD to choose your own): "
                        f"{self._value}"
                    )
        return self._value


def non_demo_users():
    """Accounts that may belong to real people: not staff, not simulated, not demo."""
    User = get_user_model()
    return User.all_objects.exclude(
        Q(is_staff=True) | Q(is_superuser=True) | Q(is_simulated=True) | Q(email__in=DEMO_EMAILS)
    )
