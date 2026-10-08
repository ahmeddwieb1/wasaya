import magic
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException, status


MAX_MEDIA_SIZE = 5 * 1024 * 1024

ALLOWED_TYPES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "video/mp4": {".mp4"},
    "video/webm": {".webm"},
}


def detect_media_type(data: bytes) -> str:
    try:
        return magic.from_buffer(data, mime=True)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Could not determine file type"},
        )


def validate_media_type(detected_type: str, extension: str) -> None:
    allowed_extensions = ALLOWED_TYPES.get(detected_type)

    if allowed_extensions is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Unsupported media type"},
        )

    if extension.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "File extension does not match file type"},
        )

def validate_image_content(data: bytes) -> None:
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()

    except Image.DecompressionBombError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Image dimensions are too large"},
        )

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid image file"},
        )