from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import SettingsResponse, SettingsUpdate
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SettingsRepository(db)
    user_settings = await repo.get_by_user_id(current_user.id)

    if not user_settings:
        # create default settings for the user
        from app.models.user_settings import UserSettings

        user_settings = UserSettings(user_id=current_user.id)
        await repo.save(user_settings)

    return user_settings


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
    print("---------------------------------------")
    print("data from settin ",data )
    print ("time now ",datetime.now(timezone.utc))
    print("---------------------------------------")
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user_settings, field, value)

    await repo.save(user_settings)
    return user_settings


@router.post("/pause", response_model=SettingsResponse)
async def pause_checkins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SettingsRepository(db)
    user_settings = await repo.get_by_user_id(current_user.id)

    if not user_settings:
        from app.models.user_settings import UserSettings
        user_settings = UserSettings(user_id=current_user.id)

    # Pause check-ins by disabling auto alerts
    user_settings.auto_alert_enabled = False
    await repo.save(user_settings)
    return user_settings