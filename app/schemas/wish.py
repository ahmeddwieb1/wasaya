from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.models.wish import Wish


class WishCreate(BaseModel):
    title: str | None = None

    content_type: Wish.ContentType = Wish.ContentType.TEXT
    content_text: str | None = Field(default=None, max_length=5000)
    media_id: str | None = None

    recipient_name: str | None = None
    recipient_email: EmailStr | None = None
    recipient_phone: str | None = None

    trigger_type: Wish.TriggerType = Wish.TriggerType.CONFIRMED_ABSENCE
    delivery_type: Wish.DeliveryType = Wish.DeliveryType.ONE_TIME
    channel: Wish.Channel = Wish.Channel.EMAIL


class WishUpdate(BaseModel):
    title: str | None = None

    content_type: Wish.ContentType | None = None
    content_text: str | None = Field(default=None, max_length=5000)
    media_id: str | None = None

    recipient_name: str | None = None
    recipient_email: EmailStr | None = None
    recipient_phone: str | None = None

    trigger_type: Wish.TriggerType | None = None
    delivery_type: Wish.DeliveryType | None = None
    channel: Wish.Channel | None = None


class WishResponse(BaseModel):
    id: str
    user_id: str
    title: str | None

    content_type: Wish.ContentType
    content_text: str | None
    media_id: str | None

    recipient_name: str | None
    recipient_email: str | None
    recipient_phone: str | None

    trigger_type: Wish.TriggerType
    delivery_type: Wish.DeliveryType
    channel: Wish.Channel
    status: Wish.Status

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}