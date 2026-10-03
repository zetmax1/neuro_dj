"""
Single role rule for the whole API (decision D15).

A user is an instructor when they are staff/superuser or belong to the
``Instructor`` (or ``Admin``) group. Every instructor-only endpoint uses
``IsInstructor``; the ``role`` field returned to the frontend is derived
from the same rule.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission

INSTRUCTOR_GROUPS: tuple[str, ...] = ("Instructor", "Admin")


def _in_groups(user, names) -> bool:
    return user.groups.filter(name__in=names).exists()


def is_instructor(user) -> bool:
    if user is None or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return _in_groups(user, INSTRUCTOR_GROUPS)


def get_role(user) -> str:
    if user.is_superuser or _in_groups(user, ("Admin",)):
        return "admin"
    if is_instructor(user):
        return "instructor"
    return "student"


class IsInstructor(BasePermission):
    message = "Instructor role required."

    def has_permission(self, request, view) -> bool:
        return is_instructor(request.user)
