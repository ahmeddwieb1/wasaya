from pydantic import BaseModel, Field
from datetime import datetime

class SettingsUpdate(BaseModel):
    check_interval_hours: int | None = Field(default=None, ge=1, le=168)
    grace_period_hours: int | None = Field(default=None, ge=1, le=48)
    preferred_channel: str | None = None
    checkin_time: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    timezone: str | None = None
    legacy_enabled: bool | None = None
    auto_alert_enabled: bool | None = None


class SettingsResponse(BaseModel):
    user_id: str
    check_interval_hours: int
    grace_period_hours: int
    preferred_channel: str
    checkin_time: str
    checkin_active: bool
    timezone: str
    next_checkin_at: datetime | None
    legacy_enabled: bool
    auto_alert_enabled: bool

    model_config = {"from_attributes": True}