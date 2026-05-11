from pydantic import BaseModel, EmailStr


class ContactCreate(BaseModel):
    name: str
    relation: str
    email: EmailStr | None = None
    phone: str | None = None
    priority_order: int = 1


class ContactResponse(BaseModel):
    id: str
    user_id: str
    name: str
    relation: str
    email: str | None
    phone: str | None
    priority_order: int
    is_active: bool

    model_config = {"from_attributes": True}