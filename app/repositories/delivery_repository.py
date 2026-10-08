from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import Delivery


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