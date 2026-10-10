# Import all models here so Alembic can detect them for migrations.
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.emergency_contact import EmergencyContact
from app.models.checkin_event import CheckinEvent, CheckinStatus
from app.models.verification_token import VerificationToken, TokenType
from app.models.delivery import Delivery
from app.models.media import Media
from app.models.wish import Wish
from app.models.emergency_confirmation import EmergencyConfirmation
__all__ = [
    "User",
    "UserSettings",
    "EmergencyContact",
    "CheckinEvent",
    "CheckinStatus",
    "VerificationToken",
    "TokenType",
    "Delivery",
    "Wish",
    "Media",
    "EmergencyConfirmation"
]