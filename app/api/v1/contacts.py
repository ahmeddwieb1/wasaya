from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.emergency_contact import EmergencyContact
from app.models.user import User
from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate, ContactResponse

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    contact = EmergencyContact(
        user_id=current_user.id,
        name=data.name,
        relation=data.relation,
        email=data.email,
        phone=data.phone,
        priority_order=data.priority_order,
    )
    return await repo.create(contact)


@router.get("", response_model=list[ContactResponse])
async def list_contacts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    return await repo.get_all_by_user(current_user.id)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ContactRepository(db)
    contact = await repo.get_by_id(contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Contact not found"},
        )

    if contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Not allowed"},
        )

    await repo.delete(contact)