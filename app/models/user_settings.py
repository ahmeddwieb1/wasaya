from sqlalchemy import Boolean, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    check_interval_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    grace_period_hours: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    preferred_channel: Mapped[str] = mapped_column(String(32), default="email", nullable=False)
    # Time of day to send check-in (HH:MM stored as string, e.g. "09:00")
    checkin_time: Mapped[str] = mapped_column(String(5), default="09:00", nullable=False)
    legacy_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="settings")