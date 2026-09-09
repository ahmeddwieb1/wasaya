from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.user_settings import UserSettings
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.utils.scheduling import calculate_first_checkin

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SettingsRepository(db)
    user_settings = await repo.get_by_user_id(current_user.id)

    if not user_settings:
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
        user_settings = UserSettings(user_id=current_user.id)

    update_data = data.model_dump(exclude_none=True)

    schedule_changed = any(
        field in update_data
        for field in ("check_interval_hours", "checkin_time", "timezone")
    )

    for field, value in update_data.items():
        setattr(
            user_settings,
            field,
            value,
        )

    # Rebuild the schedule when scheduling settings change
    # or when the user has no existing schedule.
    if schedule_changed or user_settings.next_checkin_at is None:
        user_settings.next_checkin_at = calculate_first_checkin(
            checkin_time=user_settings.checkin_time,
            timezone_name=user_settings.timezone,
        )

        # Updating settings means the user wants the
        # check-in cycle to be active again.
        user_settings.checkin_active = True

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
        user_settings = UserSettings(user_id=current_user.id)

    user_settings.checkin_active = False
    await repo.save(user_settings)
    return user_settings