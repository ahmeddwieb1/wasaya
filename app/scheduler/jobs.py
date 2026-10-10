import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.session import AsyncSessionLocal
from app.models.checkin_event import CheckinStatus
from app.repositories.user_repository import UserRepository
from app.services.checkin_service import CheckinService
from app.services.emergency_confirmation_service import EmergencyConfirmationService
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
    async with AsyncSessionLocal() as db:
        checkin_service = CheckinService(db)
        user_repo = UserRepository(db)
        settings_repo = SettingsRepository(db)
        confirmation_service = EmergencyConfirmationService(db)

        try:
            newly_expired = await checkin_service.expire_checkins()

            # Include events from previous runs where email delivery failed.
            previously_expired = (
                await checkin_service.checkin_repo.get_expired_unalerted()
            )

            events_by_id = {
                event.id: event
                for event in newly_expired + previously_expired
            }

            for event in events_by_id.values():
                try:
                    user = await user_repo.get_by_id(event.user_id)
                    if not user:
                        logger.error(
                            "Cannot process expired check-in %s: user not found",
                            event.id,
                        )
                        continue

                    settings = await settings_repo.get_by_user_id(user.id)

                    if settings:
                        settings.checkin_active = False
                        await settings_repo.save(settings)

                    auto_alert_enabled = (
                        settings is None or settings.auto_alert_enabled
                    )

                    if auto_alert_enabled:
                        sent_or_already_sent = (
                            await confirmation_service.send_request_for_event(
                                event=event,
                                user=user,
                            )
                        )

                        if not sent_or_already_sent:
                            logger.warning(
                                "No active emergency contact with email "
                                "for user=%s event=%s",
                                user.id,
                                event.id,
                            )
                            continue
                    # ALERTED means this event has been processed by the
                    # alert workflow. Failed email sends raise an exception
                    # before this point, leaving the event retryable.
                    event.status = CheckinStatus.ALERTED
                    await checkin_service.checkin_repo.save(event)

                    logger.info(
                        "Expired check-in processed for user=%s event=%s",
                        user.id,
                        event.id,
                    )

                except Exception:
                    logger.exception(
                        "Error processing expired check-in event=%s",
                        event.id,
                    )

        except Exception:
            logger.exception("Error running expired check-ins job")

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