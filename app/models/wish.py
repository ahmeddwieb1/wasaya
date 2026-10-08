import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (CheckConstraint, DateTime, Enum, ForeignKey, String, Text, Index)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Wish(Base):
    __tablename__ = "wishes"

    class ContentType(str, enum.Enum):
        TEXT = "TEXT"
        IMAGE = "IMAGE"
        VIDEO = "VIDEO"

    class TriggerType(str, enum.Enum):
        CONFIRMED_ABSENCE = "CONFIRMED_ABSENCE"

    class DeliveryType(str, enum.Enum):
        ONE_TIME = "ONE_TIME"

    class Channel(str, enum.Enum):
        EMAIL = "EMAIL"

    class Status(str, enum.Enum):
        DRAFT = "DRAFT"
        READY = "READY"
        DELIVERED = "DELIVERED"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False)

    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    media_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("media.id", ondelete="RESTRICT"), nullable=True, unique=True)

    recipient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    recipient_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    trigger_type: Mapped[TriggerType] = mapped_column(Enum(TriggerType), nullable=False)

    delivery_type: Mapped[DeliveryType] = mapped_column(Enum(DeliveryType), nullable=False)

    channel: Mapped[Channel] = mapped_column(Enum(Channel), nullable=False)

    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False, default=Status.DRAFT)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    # Relationships

    user: Mapped["User"] = relationship("User", back_populates="wishes")

    media: Mapped["Media | None"] = relationship("Media", back_populates="wish", uselist=False)

    deliveries: Mapped[list["Delivery"]] = relationship("Delivery", back_populates="wish")

    __table_args__ = (
        CheckConstraint(
            """
            status = 'DRAFT'
            OR (
                (
                    content_type = 'TEXT'
                    AND content_text IS NOT NULL
                    AND media_id IS NULL
                )
                OR
                (
                    content_type IN ('IMAGE', 'VIDEO')
                    AND content_text IS NULL
                    AND media_id IS NOT NULL
                )
            )
            """,
            name="ck_wishes_ready_content",
        ),
        CheckConstraint(
            """
            status = 'DRAFT'
            OR recipient_name IS NOT NULL
            """,
            name="ck_wishes_ready_recipient_name",
        ),
        CheckConstraint(
            """
            status = 'DRAFT'
            OR recipient_email IS NOT NULL
            """,
            name="ck_wishes_ready_recipient_email",
        ),
        CheckConstraint(
            """
            content_text IS NULL
            OR CHAR_LENGTH(content_text) <= 5000
            """,
            name="ck_wishes_content_text_length",
        ),
        Index(
            "ix_wishes_user_id_status",
            "user_id",
            "status",
        ),
    )
