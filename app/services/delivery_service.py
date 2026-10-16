import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import Delivery
from app.models.wish import Wish
from app.repositories.delivery_repository import DeliveryRepository
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class DeliveryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.delivery_repo = DeliveryRepository(db)
        self.notification_service = NotificationService()

    async def create_delivery(self, wish: Wish) -> Delivery:
        if wish.status != Wish.Status.READY:
            raise ValueError("Only READY wishes can have a delivery prepared.")
        if wish.content_type != Wish.ContentType.TEXT:
            raise ValueError("V4.1 supports text-only wishes; media is deferred to V4.3.")
        if wish.channel != Wish.Channel.EMAIL or not wish.recipient_email:
            raise ValueError("V4.1 requires EMAIL channel and recipient_email.")
        return await self.delivery_repo.create(Delivery(
            wish_id=wish.id, channel=Delivery.Channel.EMAIL, status=Delivery.Status.PENDING
        ))

    async def process_due_deliveries(self, batch_size: int = 20) -> int:
        await self.delivery_repo.reset_stale_sending()
        processed = 0
        for _ in range(batch_size):
            delivery = await self.delivery_repo.claim_next_due()
            if delivery is None:
                break
            wish = delivery.wish
            try:
                if (wish.status != Wish.Status.READY or wish.content_type != Wish.ContentType.TEXT
                    or delivery.channel != Delivery.Channel.EMAIL or not wish.recipient_email
                    or wish.content_text is None):
                    # This is a permanent eligibility problem, not an SMTP retry.
                    delivery.status = Delivery.Status.FAILED
                    delivery.error_message = "Wish is not eligible for V4.1 text email delivery."
                    await self.db.commit()
                    processed += 1
                    continue
                await asyncio.to_thread(
                    self.notification_service.send_wish_email,
                    recipient_email=wish.recipient_email,
                    recipient_name=wish.recipient_name or "there",
                    sender_name=wish.user.full_name or wish.user.email,
                    wish_title=wish.title or "A message for you",
                    wish_text=wish.content_text,
                )
                await self.delivery_repo.mark_sent(delivery.id)
                logger.info("Delivery sent: delivery_id=%s wish_id=%s", delivery.id, wish.id)
            except Exception as exc:
                logger.exception("Delivery attempt failed: delivery_id=%s", delivery.id)
                try:
                    await self.delivery_repo.mark_failed_attempt(delivery.id, f"{type(exc).__name__}: {exc}")
                except Exception:
                    await self.db.rollback()
                    logger.exception("Could not persist delivery failure: delivery_id=%s", delivery.id)
            processed += 1
        return processed
