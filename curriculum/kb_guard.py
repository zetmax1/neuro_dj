"""
curriculum/kb_guard.py — keeps knowledge-base writes inside the KB service.

The tree structure (parent, kind, position, archiving) and the prerequisite
relations may only change inside ``curriculum.services.kb``, which holds the
KB advisory lock, validates Y1–Y3 and bumps the KB version. Model and queryset
methods call ``require_kb_write`` and raise ``KBWriteError`` everywhere else,
so ``save()``, ``QuerySet.update()``, ``bulk_create()`` or the admin cannot
bypass the checks.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_KB_WRITE: ContextVar[bool] = ContextVar("kb_write", default=False)


class KBWriteError(RuntimeError):
    """A knowledge-base write was attempted outside curriculum.services.kb."""


@contextmanager
def kb_write() -> Iterator[None]:
    """Mark the current context as a KB service write (used by the service only)."""
    token = _KB_WRITE.set(True)
    try:
        yield
    finally:
        _KB_WRITE.reset(token)


def kb_write_allowed() -> bool:
    return _KB_WRITE.get()


def require_kb_write(what: str) -> None:
    if not _KB_WRITE.get():
        raise KBWriteError(f"{what} must go through curriculum.services.kb.")
