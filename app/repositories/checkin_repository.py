from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.checkin_event import CheckinEvent, CheckinStatus


class CheckinRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event: CheckinEvent) -> CheckinEvent:
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def save(self, event: CheckinEvent) -> CheckinEvent:
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_by_id(self, event_id: str) -> CheckinEvent | None:
        result = await self.db.execute(
            select(CheckinEvent).where(CheckinEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_expired(self) -> list[CheckinEvent]:
        """Return PENDING events whose grace period has passed."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(CheckinEvent)
            .options(selectinload(CheckinEvent.user))
            .where(
                CheckinEvent.status == CheckinStatus.PENDING,
                CheckinEvent.expires_at <= now,
            )
        )
        return list(result.scalars().all())

    async def get_latest_pending_for_user(self, user_id: str) -> CheckinEvent | None:
        result = await self.db.execute(
            select(CheckinEvent)
            .where(
                CheckinEvent.user_id == user_id,
                CheckinEvent.status == CheckinStatus.PENDING,
            )
            .order_by(CheckinEvent.sent_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()