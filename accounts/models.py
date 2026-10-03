from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> Any:
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any) -> Any:
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class ActiveUserManager(CustomUserManager):
    """Manager that only returns active (non-deleted) users."""
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_deleted=False)


class AllUserManager(CustomUserManager):
    """Manager that returns all users, including soft-deleted ones."""
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset()


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the unique identifier with soft-delete capabilities."""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Accounts created by the data simulator (decision D13); never research data.
    is_simulated = models.BooleanField(default=False, db_index=True)

    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveUserManager()
    all_objects = AllUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS: list[str] = []

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        """Perform a soft delete instead of hard database deletion."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False  # Deactivate the user so they cannot authenticate
        self.save(using=using)
        return (1, {self._meta.label: 1})

    def hard_delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Perform a real database deletion if needed."""
        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.email)
