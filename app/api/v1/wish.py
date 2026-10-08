from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.wish import WishCreate, WishResponse, WishUpdate
from app.services.wish_service import WishService


router = APIRouter(prefix="/wishes",tags=["Wishes"])

@router.post("", response_model=WishResponse, status_code=status.HTTP_201_CREATED)
async def create_wish(
    data: WishCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WishService(db)

    return await service.create_wish(
        user_id=current_user.id,
        data=data,
    )


@router.get("",response_model=list[WishResponse])
async def get_my_wishes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WishService(db)

    return await service.get_user_wishes(
        user_id=current_user.id,
    )

@router.get("/{wish_id}",response_model=WishResponse)
async def get_wish(
    wish_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WishService(db)

    return await service.get_wish_by_id(
        user_id=current_user.id,
        wish_id=wish_id,
    )


@router.patch("/{wish_id}",response_model=WishResponse)
async def update_wish(
    wish_id: str,
    data: WishUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WishService(db)

    return await service.update_wish(
        user_id=current_user.id,
        wish_id=wish_id,
        data=data,
    )


@router.delete("/{wish_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_wish(
    wish_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WishService(db)

    await service.delete_wish(
        user_id=current_user.id,
        wish_id=wish_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)