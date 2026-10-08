from datetime import datetime

from pydantic import BaseModel

from app.models.delivery import Delivery
from app.models.wish import Wish


class DeliveryResponse(BaseModel):
    id: str
    wish_id: str
    channel: Wish.Channel
    status: Delivery.Status
    sent_at: datetime | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}