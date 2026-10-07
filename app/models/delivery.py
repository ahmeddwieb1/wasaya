import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (DateTime, Enum, ForeignKey, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Delivery(Base):
    __tablename__ = "deliveries"

    class Channel(str, enum.Enum):
        EMAIL = "EMAIL"

    class Status(str, enum.Enum):
        PENDING = "PENDING"
        SENT = "SENT"
        FAILED = "FAILED"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    wish_id: Mapped[str] = mapped_column(String(36), ForeignKey("wishes.id", ondelete="RESTRICT"),
    nullable=False, index=True)

    channel: Mapped[Channel] = mapped_column(Enum(Channel), nullable=False)

    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False, default=Status.PENDING)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    wish: Mapped["Wish"] = relationship("Wish", back_populates="deliveries")