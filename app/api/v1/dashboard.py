from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.checkin_repository import CheckinRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.settings_repository import SettingsRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=dict)
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Basic dashboard response for the frontend MVP
    settings_repo = SettingsRepository(db)
    checkin_repo = CheckinRepository(db)
    contact_repo = ContactRepository(db)

    settings = await settings_repo.get_by_user_id(current_user.id)
    contacts = await contact_repo.get_all_by_user(current_user.id)

    last_event = None
    next_checkin = None

    # try to get last responded event
    try:
        # use checkin_repo directly if method available
        last = await db.execute("select * from checkin_events where user_id = :uid order by sent_at desc limit 1", {"uid": current_user.id})
        last_row = last.first()
        if last_row:
            last_event = str(last_row.sent_at)
    except Exception:
        last_event = None

    if settings:
        next_checkin = settings.checkin_time

    primary_contact = contacts[0] if contacts else None

    return {
        "status": "Active",
        "last_checkin": last_event,
        "next_checkin": next_checkin,
        "emergency_contact": {
            "name": primary_contact.name,
            "email": primary_contact.email,
        } if primary_contact else None,
    }
