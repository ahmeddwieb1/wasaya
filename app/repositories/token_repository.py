from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification_token import TokenType, VerificationToken


class TokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token: VerificationToken) -> VerificationToken:
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def save(self, token: VerificationToken) -> VerificationToken:
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str, token_type: TokenType) -> VerificationToken | None:
        result = await self.db.execute(
            select(VerificationToken).where(
                VerificationToken.token_hash == token_hash,
                VerificationToken.type == token_type,
            )
        )
        return result.scalar_one_or_none()