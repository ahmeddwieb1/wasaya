import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CheckinStatus(str, enum.Enum):
    PENDING = "PENDING"
    RESPONDED = "RESPONDED"
    EXPIRED = "EXPIRED"
    ALERTED = "ALERTED"


class CheckinEvent(Base):
    __tablename__ = "checkin_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(32), default="email", nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[CheckinStatus] = mapped_column(
        Enum(CheckinStatus), default=CheckinStatus.PENDING, nullable=False, index=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="checkin_events")