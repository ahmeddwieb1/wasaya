from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin_event import CheckinEvent, CheckinStatus
from app.models.user import User
from app.models.verification_token import TokenType, VerificationToken
from app.repositories.checkin_repository import CheckinRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.utils.tokens import generate_token, hash_token


class CheckinService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.checkin_repo = CheckinRepository(db)
        self.token_repo = TokenRepository(db)
        self.user_repo = UserRepository(db)

    async def create_checkin_event(self, user: User) -> tuple[CheckinEvent, str]:
        """
        Creates a PENDING check-in event and a confirmation token.
        Returns (event, raw_token).
        """
        grace_hours = 2  # fallback default
        if user.settings:
            grace_hours = user.settings.grace_period_hours

        now = datetime.now(timezone.utc)
        event = CheckinEvent(
            user_id=user.id,
            channel=user.settings.preferred_channel if user.settings else "email",
            sent_at=now,
            expires_at=now + timedelta(hours=grace_hours),
            status=CheckinStatus.PENDING,
        )
        await self.checkin_repo.create(event)

        raw_token = generate_token()
        print ("raw_tokenfor checkin", raw_token)
        token_record = VerificationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            type=TokenType.CHECKIN_CONFIRM,
            expires_at=now + timedelta(hours=grace_hours),
        )
        await self.token_repo.create(token_record)

        return event, raw_token

    async def confirm_checkin(self, raw_token: str) -> CheckinEvent:
        """Called when a user clicks their confirmation link."""
        token_hash = hash_token(raw_token)
        token_record = await self.token_repo.get_by_hash(
            token_hash, TokenType.CHECKIN_CONFIRM
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid confirmation link"},
            )

        if token_record.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "This confirmation link has already been used"},
            )

        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Confirmation link has expired"},
            )

        # Mark token as used
        now = datetime.now(timezone.utc)
        token_record.used_at = now
        await self.token_repo.save(token_record)

        # Find the most recent PENDING event for this user
        event = await self.checkin_repo.get_latest_pending_for_user(token_record.user_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "No pending check-in event found"},
            )

        event.status = CheckinStatus.RESPONDED
        event.responded_at = now
        await self.checkin_repo.save(event)

        # Update last_seen_at on the user
        user = await self.user_repo.get_by_id(token_record.user_id)
        if user:
            user.last_seen_at = now
            await self.user_repo.save(user)

        return event

    async def expire_checkins(self) -> list[CheckinEvent]:
        """
        Marks overdue PENDING events as EXPIRED.
        Returns the list of newly expired events for the caller to alert on.
        """
        expired_events = await self.checkin_repo.get_pending_expired()
        for event in expired_events:
            event.status = CheckinStatus.EXPIRED
            await self.checkin_repo.save(event)
        return expired_events