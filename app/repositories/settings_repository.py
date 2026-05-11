from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_settings import UserSettings


class SettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: str) -> UserSettings | None:
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def save(self, settings: UserSettings) -> UserSettings:
        self.db.add(settings)
        await self.db.commit()
        await self.db.refresh(settings)
        return settings