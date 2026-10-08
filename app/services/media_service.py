from pathlib import Path
from uuid import uuid4

import boto3
from fastapi import HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.media import Media
from app.repositories.media_repository import MediaRepository
from app.utils.media import (
    ALLOWED_TYPES,
    MAX_MEDIA_SIZE,
    detect_media_type,
    validate_image_content,
    validate_media_type,
)


settings = get_settings()


class MediaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.media_repo = MediaRepository(db)

        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

    async def get_media(
        self,
        user_id: str,
        media_id: str,
    ) -> Media:
        media = await self.media_repo.get_by_id_for_user(
            media_id,
            user_id,
        )

        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Media not found"},
            )

        return media

    async def upload_media(
        self,
        user_id: str,
        file: UploadFile,
    ) -> Media:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Filename is required"},
            )

        filename = Path(file.filename).name
        extension = Path(filename).suffix.lower()

        if not extension:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "File extension is required"},
            )

        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Unsupported media type"},
            )

        data = await file.read(MAX_MEDIA_SIZE + 1)

        if len(data) > MAX_MEDIA_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"message": "File size must not exceed 5 MB"},
            )

        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Empty files are not allowed"},
            )

        detected_type = detect_media_type(data)

        validate_media_type(
            detected_type,
            extension,
        )

        if detected_type.startswith("image/"):
            validate_image_content(data)

        media_id = str(uuid4())

        storage_key = (
            f"users/{user_id}/media/{media_id}{extension}"
        )

        try:
            await run_in_threadpool(
                self.s3.put_object,
                Bucket=settings.s3_bucket_name,
                Key=storage_key,
                Body=data,
                ContentLength=len(data),
                ContentType=detected_type,
            )

            media = Media(
                id=media_id,
                user_id=user_id,
                storage_key=storage_key,
                original_filename=filename[:255],
                content_type=detected_type,
                size_bytes=len(data),
                status=Media.Status.READY,
            )

            return await self.media_repo.create(media)

        except Exception:
            try:
                await run_in_threadpool(
                    self.s3.delete_object,
                    Bucket=settings.s3_bucket_name,
                    Key=storage_key,
                )
            except Exception:
                pass

            raise
    async def get_media_url(
        self,
        user_id: str,
        media_id: str,
    ) -> str:
        media = await self.get_media(
            user_id=user_id,
            media_id=media_id,
        )

        if media.status != Media.Status.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Media is not ready"},
            )

        try:
            url = await run_in_threadpool(
                self.s3.generate_presigned_url,
                "get_object",
                Params={
                    "Bucket": settings.s3_bucket_name,
                    "Key": media.storage_key,
                },
                ExpiresIn=settings.s3_url_expire_seconds,
            )

            return url

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Could not generate media URL"},
            )