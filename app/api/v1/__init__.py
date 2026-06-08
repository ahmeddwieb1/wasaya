from fastapi import APIRouter

from app.api.v1 import auth, checkin, contacts, settings
from app.api.v1 import dashboard

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(settings.router)
api_router.include_router(contacts.router)
api_router.include_router(checkin.router)
api_router.include_router(dashboard.router)