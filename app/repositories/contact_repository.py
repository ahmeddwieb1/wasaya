from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emergency_contact import EmergencyContact


class ContactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, contact_id: str) -> EmergencyContact | None:
        result = await self.db.execute(
            select(EmergencyContact).where(EmergencyContact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: str) -> list[EmergencyContact]:
        result = await self.db.execute(
            select(EmergencyContact)
            .where(EmergencyContact.user_id == user_id, EmergencyContact.is_active == True)
            .order_by(EmergencyContact.priority_order)
        )
        return list(result.scalars().all())

    async def create(self, contact: EmergencyContact) -> EmergencyContact:
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete(self, contact: EmergencyContact) -> None:
        await self.db.delete(contact)
        await self.db.commit()