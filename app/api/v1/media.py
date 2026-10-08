from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.media import MediaResponse
from app.services.media_service import MediaService


router = APIRouter(prefix="/media",tags=["Media"])


@router.post("",response_model=MediaResponse,status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MediaService(db)

    return await service.upload_media(user_id=current_user.id, file=file,)


@router.get("/{media_id}",response_model=MediaResponse)
async def get_media(
    media_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MediaService(db)

    return await service.get_media(
        user_id=current_user.id,
        media_id=media_id,
    )

@router.get("/{media_id}/url")
async def get_media_url(
    media_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MediaService(db)

    url = await service.get_media_url(
        user_id=current_user.id,
        media_id=media_id,
    )

    return {"url": url}