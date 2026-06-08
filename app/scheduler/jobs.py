import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.session import AsyncSessionLocal
from app.models.checkin_event import CheckinStatus
from app.repositories.contact_repository import ContactRepository
from app.repositories.user_repository import UserRepository
from app.services.checkin_service import CheckinService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _send_checkins_job() -> None:
    """
    Runs periodically. For each active+verified user whose check_interval has
    elapsed since last_seen_at (or account creation), creates a PENDING event
    and sends the check-in email.
    """
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        checkin_service = CheckinService(db)
        notification_service = NotificationService()

        users = await user_repo.get_all_active_verified()
        now = datetime.now()

        for user in users:
            try:
                interval_hours = 0.02
                if user.settings:
                    interval_hours = user.settings.check_interval_hours

                # Use last_seen_at or created_at as the reference point
                reference = user.last_seen_at or user.created_at

                if reference.tzinfo is not None:
                    reference = reference.replace(tzinfo=None)

                next_checkin_due = reference + timedelta(hours=interval_hours)

                if now < next_checkin_due:
                    continue  # Not due yet

                # Skip if there's already a pending event
                existing = await checkin_service.checkin_repo.get_latest_pending_for_user(
                    user.id
                )
                if existing:
                    continue

                event, raw_token = await checkin_service.create_checkin_event(user)
                notification_service.send_checkin_email(user, raw_token)

            except Exception as exc:
                logger.exception("Error sending check-in for user %s: %s", user.id, exc)


async def _expire_checkins_job() -> None:
    """
    Runs periodically. Expires overdue PENDING events and alerts emergency contacts.
    """
    async with AsyncSessionLocal() as db:
        checkin_service = CheckinService(db)
        contact_repo = ContactRepository(db)
        user_repo = UserRepository(db)
        notification_service = NotificationService()

        expired_events = await checkin_service.expire_checkins()

        for event in expired_events:
            try:
                user = await user_repo.get_by_id(event.user_id)
                if not user:
                    continue

                # Only alert if auto_alert is enabled
                if user.settings and not user.settings.auto_alert_enabled:
                    continue

                contacts = await contact_repo.get_all_by_user(user.id)
                for contact in contacts:
                    notification_service.send_alert_email(user, contact)

                # Mark event as ALERTED
                event.status = CheckinStatus.ALERTED
                await checkin_service.checkin_repo.save(event)

            except Exception as exc:
                logger.exception("Error alerting for event %s: %s", event.id, exc)


def start_scheduler() -> None:
    # Send check-ins every hour (the per-user interval is evaluated inside the job)
    scheduler.add_job(
        _send_checkins_job,
        trigger="interval",
        seconds=60,
        id="send_checkins",
        replace_existing=True,
    )

    # Check for expired events every 15 minutes
    scheduler.add_job(
        _expire_checkins_job,
        trigger="interval",
        minutes=15,
        id="expire_checkins",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started.")


def stop_scheduler() -> None:
    scheduler.shutdown()
    logger.info("Scheduler stopped.")