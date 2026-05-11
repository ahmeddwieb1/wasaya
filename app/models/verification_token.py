import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TokenType(str, enum.Enum):
    EMAIL_VERIFY = "EMAIL_VERIFY"
    CHECKIN_CONFIRM = "CHECKIN_CONFIRM"


class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[TokenType] = mapped_column(Enum(TokenType), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="verification_tokens")