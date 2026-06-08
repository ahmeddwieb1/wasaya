from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.verification_token import TokenType, VerificationToken
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import SignupRequest
from app.utils.tokens import generate_token, hash_token

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = TokenRepository(db)

    async def signup(self, data: SignupRequest) -> tuple[User, str]:
        """
        Creates a new user + default settings + email verification token.
        Returns (user, raw_token) so the caller can send the verification email.
        """
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "An account with this email already exists"},
            )

        password_hash = bcrypt.hashpw(
            data.password.encode(), bcrypt.gensalt()
        ).decode()

        user = User(
            email=data.email,
            password_hash=password_hash,
            full_name=data.full_name,
            timezone=data.timezone,
        )
        # Create default settings together with the user
        user.settings = UserSettings(user_id=user.id)

        await self.user_repo.create(user)

        raw_token = await self._create_verification_token(
            user.id, TokenType.EMAIL_VERIFY
        )
        return user, raw_token

    async def login(self, email: str, password: str) -> User:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Invalid email or password"},
            )

        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Invalid email or password"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Account is inactive"},
            )

        return user

    async def verify_email(self, raw_token: str) -> User:
        token_hash = hash_token(raw_token)
        token_record = await self.token_repo.get_by_hash(
            token_hash, TokenType.EMAIL_VERIFY
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid verification link"},
            )

        if token_record.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "This verification link has already been used"},
            )

        if token_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Verification link has expired"},
            )

        # Mark token as used
        token_record.used_at = datetime.now(timezone.utc)
        await self.token_repo.save(token_record)

        # Mark user as verified
        user = await self.user_repo.get_by_id(token_record.user_id)
        user.is_verified = True
        await self.user_repo.save(user)

        return user

    async def _create_verification_token(
        self, user_id: str, token_type: TokenType, expires_hours: int = 24
    ) -> str:
        raw_token = generate_token()
        print(f"\n--- DEBUG TOKEN: {raw_token} ---\n")
        token_record = VerificationToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            type=token_type,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        )
        await self.token_repo.create(token_record)
        return raw_token