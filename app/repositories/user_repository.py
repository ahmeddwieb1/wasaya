from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.user_settings import UserSettings


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def save(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_with_settings(self, user_id: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.settings))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_active_verified(self) -> list[User]:
        """Used by scheduler to find users eligible for check-in."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.settings))
            .where(User.is_active == True, User.is_verified == True)
        )
        return list(result.scalars().all())