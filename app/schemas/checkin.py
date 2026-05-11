from datetime import datetime

from pydantic import BaseModel

from app.models.checkin_event import CheckinStatus


class CheckinEventResponse(BaseModel):
    id: str
    user_id: str
    channel: str
    sent_at: datetime
    responded_at: datetime | None
    expires_at: datetime
    status: CheckinStatus

    model_config = {"from_attributes": True}