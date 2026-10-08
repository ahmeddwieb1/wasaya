from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import Delivery
from app.models.wish import Wish
from app.repositories.delivery_repository import DeliveryRepository


class DeliveryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.delivery_repo = DeliveryRepository(db)

    async def create_delivery(
        self,
        wish: Wish,
    ) -> Delivery:
        delivery = Delivery(
            wish_id=wish.id,
            channel=wish.channel,
            status=Delivery.Status.PENDING,
        )

        return await self.delivery_repo.create(delivery)