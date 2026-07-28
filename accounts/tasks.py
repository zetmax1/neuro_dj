import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def gdpr_hard_delete_users() -> int:
    """
    Data retention policy: permanently deletes CustomUser records 
    that were soft-deleted more than 30 days ago.
    Runs nightly via Celery Beat.
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    
    # We use all_objects to bypass the ActiveUserManager filter
    users_to_delete = User.all_objects.filter(
        is_deleted=True, 
        deleted_at__lt=cutoff_date
    )
    
    count = users_to_delete.count()
    
    if count > 0:
        for user in users_to_delete:
            # We call the overridden hard_delete() method defined in the CustomUser model
            user.hard_delete()
        logger.info(f"GDPR task completed: Permanently deleted {count} user(s).")
    else:
        logger.info("GDPR task completed: No users met the 30-day retention threshold.")
        
    return count
