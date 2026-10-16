from datetime import datetime, timedelta, timezone
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery import Delivery
from app.models.wish import Wish

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DeliveryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, delivery: Delivery) -> Delivery:
        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery

    async def get_by_id(
        self,
        delivery_id: str,
    ) -> Delivery | None:
        result = await self.db.execute(
            select(Delivery).where(Delivery.id == delivery_id)
        )
        return result.scalar_one_or_none()

    async def get_by_wish_id(
        self,
        wish_id: str,
    ) -> list[Delivery]:
        result = await self.db.execute(
            select(Delivery)
            .where(Delivery.wish_id == wish_id)
            .order_by(Delivery.created_at.desc())
        )
        return list(result.scalars().all())

    async def save(self, delivery: Delivery) -> Delivery:
        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery

    async def claim_next_due(self) -> Delivery | None:
        """Claim one row atomically. MySQL 8+ is required for SKIP LOCKED."""
        now = _utcnow()
        stmt = (
            select(Delivery)
            .options(selectinload(Delivery.wish).selectinload(Wish.user))
            .where(
                Delivery.status == Delivery.Status.PENDING,
                or_(Delivery.next_attempt_at.is_(None), Delivery.next_attempt_at <= now),
            )
            .order_by(Delivery.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        delivery = result.scalar_one_or_none()
        if delivery is None:
            await self.db.rollback()
            return None
        delivery.status = Delivery.Status.SENDING
        delivery.attempt_count += 1
        delivery.last_attempt_at = now
        delivery.next_attempt_at = None
        delivery.error_message = None
        delivery_id = delivery.id
        await self.db.commit()
        result = await self.db.execute(
            select(Delivery)
            .options(selectinload(Delivery.wish).selectinload(Wish.user))
            .where(Delivery.id == delivery_id)
        )
        return result.scalar_one()

    async def mark_sent(self, delivery_id: str) -> None:
        result = await self.db.execute(
            select(Delivery).options(selectinload(Delivery.wish)).where(Delivery.id == delivery_id).with_for_update()
        )
        delivery = result.scalar_one_or_none()
        if delivery is None:
            await self.db.rollback()
            return
        delivery.status = Delivery.Status.SENT
        delivery.sent_at = _utcnow()
        delivery.error_message = None
        delivery.next_attempt_at = None
        if delivery.wish.status == Wish.Status.READY:
            delivery.wish.status = Wish.Status.DELIVERED
        await self.db.commit()

    async def mark_failed_attempt(self, delivery_id: str, error_message: str) -> None:
        result = await self.db.execute(
            select(Delivery).where(Delivery.id == delivery_id).with_for_update()
        )
        delivery = result.scalar_one_or_none()
        if delivery is None:
            await self.db.rollback()
            return
        # Four attempts total: after attempts 1, 2, 3 wait 1, 5, 15 minutes.
        retry_delays = {1: 1, 2: 5, 3: 15}
        delay = retry_delays.get(delivery.attempt_count)
        delivery.error_message = error_message[:4000]
        if delay is None:
            delivery.status = Delivery.Status.FAILED
            delivery.next_attempt_at = None
        else:
            delivery.status = Delivery.Status.PENDING
            delivery.next_attempt_at = _utcnow() + timedelta(minutes=delay)
        await self.db.commit()

    async def reset_stale_sending(self, stale_after_minutes: int = 10) -> int:
        """Recover abandoned claims; a previous SMTP outcome may be unknown."""
        cutoff = _utcnow() - timedelta(minutes=stale_after_minutes)
        result = await self.db.execute(
            select(Delivery).where(
                Delivery.status == Delivery.Status.SENDING,
                Delivery.last_attempt_at.is_not(None),
                Delivery.last_attempt_at <= cutoff,
            ).with_for_update(skip_locked=True)
        )
        rows = list(result.scalars().all())
        for delivery in rows:
            delivery.status = Delivery.Status.PENDING
            delivery.next_attempt_at = _utcnow()
            delivery.error_message = "Recovered stale SENDING state; prior SMTP outcome may be unknown."
        await self.db.commit()
        return len(rows)
