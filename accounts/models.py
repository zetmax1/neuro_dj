from __future__ import annotations

import secrets
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

# Length of ``research_pseudonym``: secrets.token_hex(8) is 16 hex characters.
PSEUDONYM_BYTES = 8
PSEUDONYM_LENGTH = PSEUDONYM_BYTES * 2

# Where an anonymised account's email is parked. ``.invalid`` is reserved by
# RFC 2606, so the address can never be routed anywhere.
ANONYMISED_EMAIL_DOMAIN = "removed.invalid"


def new_pseudonym() -> str:
    """
    A random, irreversible research identifier (D43).

    Not derived from the id, the email or the name: a pseudonym computed from
    any of them could be recomputed from a leaked user list, which is the one
    thing a pseudonym has to prevent. It is assigned when the row is created,
    so every account has one whether or not consent is ever given — the
    pseudonym is not itself a disclosure.
    """
    return secrets.token_hex(PSEUDONYM_BYTES)


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

    # --- Research consent (D42, D43) --------------------------------------
    # Off by default. It is given only by an explicit act of the learner, and
    # a learner who does not give it uses the platform in full.
    research_consent = models.BooleanField(
        default=False,
        db_index=True,
        help_text="The learner agreed that their answers may be used in the thesis.",
    )
    research_consent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the consent flag last changed, in either direction.",
    )
    research_pseudonym = models.CharField(
        max_length=PSEUDONYM_LENGTH,
        unique=True,
        default=new_pseudonym,
        editable=False,
        help_text="Random and irreversible; the only identifier an export carries (D43).",
    )

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

    def anonymise(self) -> None:
        """
        Strip every identifying field but keep the row (D11).

        A learner who consented and then asked to be removed is not simply
        deleted: ``AssessmentAttempt.user`` cascades, so deleting the row would
        take their answers with it, and those answers are research data they
        agreed to. Instead the identity goes and the pseudonym stays, which is
        all an export ever carried. The email is replaced rather than cleared
        because it is unique and not nullable; the replacement is built from
        the pseudonym, so it reveals nothing about the original.

        Unusable password, inactive and still flagged deleted: the account can
        neither be signed into nor re-used.
        """
        self.email = f"anon-{self.research_pseudonym}@{ANONYMISED_EMAIL_DOMAIN}"
        self.first_name = ""
        self.last_name = ""
        self.set_unusable_password()
        self.is_active = False
        self.is_deleted = True
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
        self.save(update_fields=[
            "email", "first_name", "last_name", "password",
            "is_active", "is_deleted", "deleted_at",
        ])

    @property
    def is_anonymised(self) -> bool:
        """True once ``anonymise`` has run: there is no identity left to strip."""
        return self.email.endswith(f"@{ANONYMISED_EMAIL_DOMAIN}")

    def __str__(self) -> str:
        return str(self.email)
