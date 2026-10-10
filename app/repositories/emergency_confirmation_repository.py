from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emergency_confirmation import EmergencyConfirmation


class EmergencyConfirmationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        confirmation_id: str,
    ) -> EmergencyConfirmation | None:
        result = await self.db.execute(
            select(EmergencyConfirmation).where(
                EmergencyConfirmation.id == confirmation_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_event_id(
        self,
        event_id: str,
    ) -> EmergencyConfirmation | None:
        result = await self.db.execute(
            select(EmergencyConfirmation).where(
                EmergencyConfirmation.checkin_event_id == event_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_token_hash(
        self,
        token_hash: str,
        *,
        for_update: bool = False,
    ) -> EmergencyConfirmation | None:
        statement = select(EmergencyConfirmation).where(
            EmergencyConfirmation.token_hash == token_hash
        )

        if for_update:
            statement = statement.with_for_update()

        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_unsent(self) -> list[EmergencyConfirmation]:
        result = await self.db.execute(
            select(EmergencyConfirmation).where(
                EmergencyConfirmation.sent_at.is_(None),
                EmergencyConfirmation.confirmed_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        confirmation: EmergencyConfirmation,
    ) -> EmergencyConfirmation:
        self.db.add(confirmation)
        await self.db.commit()
        await self.db.refresh(confirmation)
        return confirmation

    async def save(
        self,
        confirmation: EmergencyConfirmation,
    ) -> EmergencyConfirmation:
        self.db.add(confirmation)
        await self.db.commit()
        await self.db.refresh(confirmation)
        return confirmation