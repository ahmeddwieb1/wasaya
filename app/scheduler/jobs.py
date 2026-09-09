import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.session import AsyncSessionLocal
from app.models.checkin_event import CheckinStatus
from app.repositories.contact_repository import ContactRepository
from app.repositories.user_repository import UserRepository
from app.services.checkin_service import CheckinService
from app.services.notification_service import NotificationService
from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _send_checkins_job() -> None:
    """
    Sends check-in emails when next_checkin_at is reached.

    The schedule is independent from last_seen_at.

    A pending check-in blocks another check-in from being created.

    If the pending check-in expires, the expiration job stops
    the check-in cycle.
    """
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        checkin_service = CheckinService(db)
        notification_service = NotificationService()

        users = await user_repo.get_all_active_verified()
        now = datetime.now(timezone.utc)

        for user in users:
            try:
                if not user.settings:
                    continue

                settings = user.settings

                # Check-in cycle is stopped.
                if not settings.checkin_active:
                    continue

                next_checkin_at = settings.next_checkin_at

                if not next_checkin_at:
                    continue

                if next_checkin_at.tzinfo is None:
                    next_checkin_at = next_checkin_at.replace(
                        tzinfo=timezone.utc
                    )

                # Not due yet.
                if now < next_checkin_at:
                    continue

                # Don't send another check-in while
                # the previous one is still waiting for response.
                existing = (
                    await checkin_service.checkin_repo
                    .get_latest_pending_for_user(user.id)
                )
                if existing:
                    continue

                # Create check-in event.
                event, raw_token = (await checkin_service.create_checkin_event(user))

                notification_service.send_checkin_email(user, raw_token)

                # Schedule the next occurrence based on
                # the configured interval, NOT last_seen_at.
                settings.next_checkin_at = (
                    next_checkin_at
                    + timedelta(
                        hours=settings.check_interval_hours
                    )
                )

                await user_repo.save(user)

                logger.info(
                    "Check-in sent for user=%s next=%s",
                    user.id,
                    settings.next_checkin_at,
                )

            except Exception:
                logger.exception(
                    "Error sending check-in for user %s",
                    user.id,
                )


async def _expire_checkins_job() -> None:
    """
    Expires unanswered check-ins.

    After expiration:
        1. Send alerts.
        2. Stop the check-in cycle.

    Later this is where we can transition to Media Mode.
    """
    async with AsyncSessionLocal() as db:
        checkin_service = CheckinService(db)
        contact_repo = ContactRepository(db)
        user_repo = UserRepository(db)
        settings_repo = SettingsRepository(db)
        notification_service = NotificationService()

        expired_events = await checkin_service.expire_checkins()

        for event in expired_events:
            try:
                user = await user_repo.get_by_id(event.user_id)
                if not user:
                    continue

                settings = await settings_repo.get_by_user_id(user.id)

                if settings:
                    settings.checkin_active = False
                    await settings_repo.save(settings)

                if not settings or settings.auto_alert_enabled:
                    contacts = await contact_repo.get_all_by_user(user.id)
                    for contact in contacts:
                        notification_service.send_alert_email(user, contact)

                # Mark event as ALERTED
                event.status = CheckinStatus.ALERTED
                await checkin_service.checkin_repo.save(event)

                logger.warning("Check-in expired for user=%s. Check-in cycle stopped.", user.id)

            except Exception:
                logger.exception("Error alerting for event %s", event.id)

def start_scheduler() -> None:
    scheduler.add_job(
        _send_checkins_job,
        trigger="interval",
        minutes=1,
        id="send_checkins",
        replace_existing=True,
    )

    scheduler.add_job(
        _expire_checkins_job,
        trigger="interval",
        minutes=1,
        id="expire_checkins",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started.")


def stop_scheduler() -> None:
    scheduler.shutdown()
    logger.info("Scheduler stopped.")