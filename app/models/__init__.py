# Import all models here so Alembic can detect them for migrations.
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.emergency_contact import EmergencyContact
from app.models.checkin_event import CheckinEvent, CheckinStatus
from app.models.verification_token import VerificationToken, TokenType

__all__ = [
    "User",
    "UserSettings",
    "EmergencyContact",
    "CheckinEvent",
    "CheckinStatus",
    "VerificationToken",
    "TokenType",
]