"""
curriculum/kb_guard.py — the knowledge base's error types and its write guard.

The tree structure (parent, kind, position, archiving) and the prerequisite
relations may only change inside ``curriculum.services.kb``, which holds the
KB advisory lock, validates Y1–Y3 and bumps the KB version. Model and queryset
methods call ``require_kb_write`` and raise ``KBWriteError`` everywhere else,
so ``save()``, ``QuerySet.update()``, ``bulk_create()`` or the admin cannot
bypass the checks.

``KBError`` (a rejected change) lives here rather than in the service because
``curriculum.models`` raises it too — ``KnowledgeBaseVersion.current()`` refuses
a missing counter row (D31) — and models may not import the service. The
service re-exports it, so ``kb.KBError`` stays the public name (D32).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_KB_WRITE: ContextVar[bool] = ContextVar("kb_write", default=False)


class KBWriteError(RuntimeError):
    """A knowledge-base write was attempted outside curriculum.services.kb."""


class KBError(Exception):
    """A rejected KB change. ``reason`` is a stable code for the API (400)."""

    def __init__(
        self,
        reason: str,
        detail: str,
        *,
        chain: list[int] | None = None,
        edge: tuple[int, int] | None = None,
    ) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail
        self.chain = chain
        self.edge = edge

    def payload(self) -> dict[str, Any]:
        data: dict[str, Any] = {"reason": self.reason, "detail": self.detail}
        if self.chain is not None:
            # Imported here: curriculum.models imports this module.
            from curriculum.models import Topic

            data["chain"] = self.chain
            names = dict(Topic.objects.filter(pk__in=self.chain).values_list("pk", "name"))
            data["chain_names"] = [names.get(pk, str(pk)) for pk in self.chain]
        if self.edge is not None:
            data["edge"] = list(self.edge)
        return data


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
