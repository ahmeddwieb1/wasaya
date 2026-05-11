from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.checkin import CheckinEventResponse
from app.services.checkin_service import CheckinService

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.get("/confirm", response_model=CheckinEventResponse)
async def confirm_checkin(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Called when the user clicks the confirmation link in their check-in email.
    No authentication required — the token itself is the proof of identity.
    """
    service = CheckinService(db)
    event = await service.confirm_checkin(token)
    return event