from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.models.wish import Wish
from app.repositories.media_repository import MediaRepository
from app.repositories.wish_repository import WishRepository
from app.schemas.wish import WishCreate, WishUpdate


class WishService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wish_repo = WishRepository(db)
        self.media_repo = MediaRepository(db)

    async def create_wish(self, user_id: str, data: WishCreate) -> Wish:
        wish = Wish(
            user_id=user_id,
            title=data.title,
            content_type=data.content_type,
            content_text=data.content_text,
            media_id=data.media_id,
            recipient_name=data.recipient_name,
            recipient_email=data.recipient_email,
            recipient_phone=data.recipient_phone,
            trigger_type=data.trigger_type,
            delivery_type=data.delivery_type,
            channel=data.channel,
            status=Wish.Status.DRAFT,
        )

        await self._update_status(wish)

        return await self.wish_repo.create(wish)

    async def get_wish_by_id(self, user_id: str, wish_id: str) -> Wish:
        wish = await self.wish_repo.get_by_id_for_user(wish_id, user_id)

        if not wish:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Wish not found"},
            )

        return wish

    async def get_user_wishes(self, user_id: str) -> list[Wish]:
        return await self.wish_repo.get_all_for_user(user_id)

    async def get_ready_wishes(self, user_id: str) -> list[Wish]:
        return await self.wish_repo.get_ready_for_user(user_id)

    async def update_wish(self, user_id: str, wish_id: str, data: WishUpdate) -> Wish:
        wish = await self.get_wish_by_id(user_id, wish_id)

        if wish.status == Wish.Status.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Delivered wishes cannot be updated"
                },
            )

        updates = data.model_dump(
            exclude_unset=True,
        )

        for field, value in updates.items():
            setattr(wish, field, value)

        await self._update_status(wish)

        return await self.wish_repo.save(wish)

    async def delete_wish(self, user_id: str, wish_id: str) -> None:
        wish = await self.get_wish_by_id(user_id, wish_id)

        if wish.status == Wish.Status.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Delivered wishes cannot be deleted"
                },
            )

        await self.wish_repo.delete(wish)

    async def _update_status(self, wish: Wish) -> None:
        if await self._is_ready(wish):
            wish.status = Wish.Status.READY
        else:
            wish.status = Wish.Status.DRAFT

    async def _is_ready(self, wish: Wish) -> bool:
        try:
            await self._validate_ready(wish)
            return True
        except HTTPException:
            return False

    async def _validate_ready(self, wish: Wish) -> None:
        if wish.content_type == Wish.ContentType.TEXT:
            if (
                wish.content_text is None
                or not wish.content_text.strip()
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Text content is required"},
                )

            if wish.media_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Text wish cannot have media"},
                )

        elif wish.content_type in {
            Wish.ContentType.IMAGE,
            Wish.ContentType.VIDEO,
        }:
            if wish.media_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Media is required"}
                )

            if wish.content_text is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": ("Media wish cannot have text content")}
                )

            media = await self.media_repo.get_by_id_for_user(wish.media_id, wish.user_id)

            if not media:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Media not found"
                    },
                )

            if media.status != Media.Status.READY:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Media is not ready"
                    },
                )

            expected_content_type = {
                Wish.ContentType.IMAGE: {
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                    "image/jpg",
                },
                Wish.ContentType.VIDEO: {
                    "video/mp4",
                    "video/webm",
                },
            }

            if media.content_type not in expected_content_type[
                wish.content_type
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": (
                            "Media type does not match wish content type"
                        )
                    },
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid content type"
                },
            )

        if not wish.recipient_name or not wish.recipient_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Recipient name is required"
                },
            )

        if wish.channel == Wish.Channel.EMAIL:
            if not wish.recipient_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Recipient email is required"
                    },
                )

        if wish.trigger_type != Wish.TriggerType.CONFIRMED_ABSENCE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid trigger type"
                },
            )

        if wish.delivery_type != Wish.DeliveryType.ONE_TIME:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid delivery type"
                },
            )