from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media


class MediaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, media: Media) -> Media:
        self.db.add(media)
        await self.db.commit()
        await self.db.refresh(media)
        return media

    async def get_by_id(self, media_id: str) -> Media | None:
        result = await self.db.execute(
            select(Media).where(Media.id == media_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self,
        media_id: str,
        user_id: str,
    ) -> Media | None:
        result = await self.db.execute(
            select(Media).where(
                Media.id == media_id,
                Media.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def save(self, media: Media) -> Media:
        self.db.add(media)
        await self.db.commit()
        await self.db.refresh(media)
        return media

    async def delete(self, media: Media) -> None:
        await self.db.delete(media)
        await self.db.commit()