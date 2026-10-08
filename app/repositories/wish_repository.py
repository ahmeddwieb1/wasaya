from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wish import Wish


class WishRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, wish: Wish) -> Wish:
        self.db.add(wish)
        await self.db.commit()
        await self.db.refresh(wish)
        return wish

    async def get_by_id(self, wish_id: str) -> Wish | None:
        result = await self.db.execute(
            select(Wish).where(Wish.id == wish_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self,
        wish_id: str,
        user_id: str,
    ) -> Wish | None:
        result = await self.db.execute(
            select(Wish).where(
                Wish.id == wish_id,
                Wish.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_for_user(
        self,
        user_id: str,
    ) -> list[Wish]:
        result = await self.db.execute(
            select(Wish)
            .where(Wish.user_id == user_id)
            .order_by(Wish.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_ready_for_user(
        self,
        user_id: str,
    ) -> list[Wish]:
        result = await self.db.execute(
            select(Wish).where(
                Wish.user_id == user_id,
                Wish.status == Wish.Status.READY,
            )
        )
        return list(result.scalars().all())

    async def save(self, wish: Wish) -> Wish:
        self.db.add(wish)
        await self.db.commit()
        await self.db.refresh(wish)
        return wish

    async def delete(self, wish: Wish) -> None:
        await self.db.delete(wish)
        await self.db.commit()