from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.emergency_confirmation_service import (
    EmergencyConfirmationService,
)

router = APIRouter(
    prefix="/emergency-confirmations",
    tags=["emergency-confirmations"],
)


class EmergencyConfirmationRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class EmergencyConfirmationResponse(BaseModel):
    message: str
    deliveries_prepared: int


@router.post(
    "/confirm",
    response_model=EmergencyConfirmationResponse,
)
async def confirm_emergency_contact(
    payload: EmergencyConfirmationRequest,
    db: AsyncSession = Depends(get_db),
) -> EmergencyConfirmationResponse:
    service = EmergencyConfirmationService(db)

    deliveries_prepared = await service.confirm_and_prepare_deliveries(
        payload.token
    )

    return EmergencyConfirmationResponse(
        message="Confirmation accepted. Delivery records have been prepared.",
        deliveries_prepared=deliveries_prepared,
    )