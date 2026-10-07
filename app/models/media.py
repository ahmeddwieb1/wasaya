import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (BigInteger, DateTime, Enum, ForeignKey, String)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Media(Base):
    __tablename__ = "media"

    class Status(str, enum.Enum):
        PENDING = "PENDING"
        READY = "READY"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    index=True)

    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True,)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False, default=Status.PENDING,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="media")

    wish: Mapped["Wish | None"] = relationship("Wish", back_populates="media", uselist=False)
