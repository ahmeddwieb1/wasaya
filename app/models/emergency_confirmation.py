import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmergencyConfirmation(Base):
    __tablename__ = "emergency_confirmations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    checkin_event_id: Mapped[str] = mapped_column(String(36), ForeignKey("checkin_events.id", ondelete="CASCADE"), nullable=False, unique=True)

    emergency_contact_id: Mapped[str] = mapped_column(String(36), ForeignKey("emergency_contacts.id", ondelete="CASCADE"), nullable=False, index=True)

    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    checkin_event: Mapped["CheckinEvent"] = relationship()
    emergency_contact: Mapped["EmergencyContact"] = relationship()