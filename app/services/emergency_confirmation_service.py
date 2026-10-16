from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wish import Wish
from app.models.checkin_event import CheckinEvent
from app.models.delivery import Delivery
from app.models.emergency_confirmation import EmergencyConfirmation
from app.models.user import User
from app.repositories.checkin_repository import CheckinRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.delivery_repository import DeliveryRepository
from app.repositories.emergency_confirmation_repository import (
    EmergencyConfirmationRepository,
)
from app.repositories.user_repository import UserRepository
from app.repositories.wish_repository import WishRepository
from app.services.notification_service import NotificationService
from app.utils.tokens import generate_token, hash_token


class EmergencyConfirmationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.confirmation_repo = EmergencyConfirmationRepository(db)
        self.checkin_repo = CheckinRepository(db)
        self.contact_repo = ContactRepository(db)
        self.delivery_repo = DeliveryRepository(db)
        self.user_repo = UserRepository(db)
        self.wish_repo = WishRepository(db)
        self.notification_service = NotificationService()

    async def send_request_for_event(
        self,
        event: CheckinEvent,
        user: User,
    ) -> bool:
        """
        Send a confirmation request to the highest-priority active
        contact with an email address.

        Returns True if the email was sent or was already sent.
        Returns False if no eligible contact exists.
        """
        contact = await self.contact_repo.get_highest_priority_email_contact(
            user.id
        )
        if not contact:
            return False

        confirmation = await self.confirmation_repo.get_by_event_id(event.id)

        if confirmation and confirmation.confirmed_at is not None:
            return True

        if confirmation and confirmation.sent_at is not None:
            return True

        raw_token = generate_token()
        now = datetime.now(timezone.utc)

        if confirmation is None:
            confirmation = EmergencyConfirmation(
                checkin_event_id=event.id,
                emergency_contact_id=contact.id,
                token_hash=hash_token(raw_token),
                sent_at=None,
                confirmed_at=None,
            )
            confirmation = await self.confirmation_repo.create(confirmation)
        else:
            # If the previously selected contact was removed or changed,
            # retry with the currently highest-priority eligible contact.
            confirmation.emergency_contact_id = contact.id
            confirmation.token_hash = hash_token(raw_token)
            confirmation.sent_at = None
            await self.confirmation_repo.save(confirmation)

        try:
            self.notification_service.send_emergency_confirmation_email(
                user=user,
                contact=contact,
                raw_token=raw_token,
            )
        except Exception:
            # sent_at stays NULL so the scheduler can retry.
            raise

        confirmation.sent_at = now
        await self.confirmation_repo.save(confirmation)
        return True

    async def confirm_and_prepare_deliveries(
        self,
        raw_token: str,
    ) -> int:
        """
        Consume the confirmation token and create PENDING deliveries
        for the user's READY wishes in one database transaction.

        Returns the number of newly created deliveries.
        """
        token_hash = hash_token(raw_token)

        confirmation = await self.confirmation_repo.get_by_token_hash(
            token_hash,
            for_update=True,
        )

        if not confirmation:
            raise HTTPException(
                status_code=400,
                detail={"message": "Invalid confirmation link"},
            )

        if confirmation.confirmed_at is not None:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "This confirmation link has already been used"
                },
            )

        event = await self.checkin_repo.get_by_id(
            confirmation.checkin_event_id
        )
        if not event:
            raise HTTPException(
                status_code=400,
                detail={"message": "The check-in event no longer exists"},
            )

        now = datetime.now(timezone.utc)
        confirmation.confirmed_at = now

        wishes = await self.wish_repo.get_ready_for_user(event.user_id)
        created_count = 0

        try:
            for wish in wishes:
                # V4.1: text-only Email.
                # Media support is deferred to V4.3.
                if (
                    wish.status != Wish.Status.READY
                    or wish.content_type != Wish.ContentType.TEXT
                    or wish.channel != Wish.Channel.EMAIL
                    or not wish.recipient_email
                    or not wish.content_text
                ):
                    continue

                existing = await self.delivery_repo.get_by_wish_id(wish.id)
                if existing:
                    continue

                self.db.add(
                    Delivery(
                        wish_id=wish.id,
                        channel=Delivery.Channel.EMAIL,
                        status=Delivery.Status.PENDING,
                    )
                )
                created_count += 1

            # Commit confirmation consumption and queued deliveries together.
            # UNIQUE(deliveries.wish_id) is the final duplicate guard.
            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise

        return created_count