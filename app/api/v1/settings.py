from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.put("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SettingsRepository(db)
    user_settings = await repo.get_by_user_id(current_user.id)

    if not user_settings:
        from app.models.user_settings import UserSettings
        user_settings = UserSettings(user_id=current_user.id)

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user_settings, field, value)

    await repo.save(user_settings)
    return user_settings