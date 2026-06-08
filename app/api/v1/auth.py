from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, UserResponse
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user, raw_token = await service.signup(data)

    try:
        NotificationService().send_verification_email(user, raw_token)
    except Exception:
        # Don't fail signup if email sending fails; log in production
        pass

    return user


@router.post("/login", response_model=UserResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.login(data.email, data.password)
    print ("login_at",datetime.now(timezone.utc))
    token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/verify-email", response_model=UserResponse)
async def verify_email(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.verify_email(token)
    return user