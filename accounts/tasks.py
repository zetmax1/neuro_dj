"""
accounts/tasks.py — the retention task behind the soft delete (D11).

A deleted account is kept for 30 days and then removed for good. What
"removed" means depends on one thing, and D11 fixes it: whether the learner
had agreed that their answers may be used in the thesis.

- **No consent** — the row is deleted outright. ``AssessmentAttempt.user``
  cascades, so the answers go with it. That is the intended outcome: the data
  was never research data.
- **Consent given** — the identity is stripped and the row stays
  (``CustomUser.anonymise``). Deleting it would cascade through answers the
  learner agreed could be used, and the export never carried anything but the
  pseudonym anyway, so what is removed here is exactly what the export already
  left out: the email and the name.

Withdrawing consent therefore has a sharper effect than it may look: a learner
who withdraws and then deletes their account is in the first branch, and their
answers are deleted with them.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import ANONYMISED_EMAIL_DOMAIN

logger = logging.getLogger(__name__)
User = get_user_model()

# How long a soft-deleted account is kept before it is removed for good.
RETENTION_DAYS = 30


@shared_task
def gdpr_hard_delete_users() -> dict[str, int]:
    """
    Remove accounts soft-deleted more than ``RETENTION_DAYS`` ago (D11).

    Returns the two counts separately — anonymised and deleted — because they
    are different events and a single total would hide which one happened.
    Runs nightly via Celery Beat.
    """
    cutoff = timezone.now() - timedelta(days=RETENTION_DAYS)

    # all_objects bypasses the ActiveUserManager filter, which hides these
    # rows. An anonymised account stays soft-deleted forever — its answers are
    # research data — so it is excluded here; otherwise every nightly run would
    # strip it again and report it as newly anonymised.
    due = User.all_objects.filter(is_deleted=True, deleted_at__lt=cutoff).exclude(
        email__endswith=f"@{ANONYMISED_EMAIL_DOMAIN}",
    )

    anonymised = 0
    deleted = 0
    for user in due:
        if user.research_consent:
            user.anonymise()
            anonymised += 1
        else:
            user.hard_delete()
            deleted += 1

    if anonymised or deleted:
        logger.info(
            "Retention task: %d account(s) anonymised (consent kept, D11), %d deleted.",
            anonymised,
            deleted,
        )
    else:
        logger.info("Retention task: no account reached the %d-day threshold.", RETENTION_DAYS)

    return {"anonymised": anonymised, "deleted": deleted}
