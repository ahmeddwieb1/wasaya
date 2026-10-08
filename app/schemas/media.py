from datetime import datetime

from pydantic import BaseModel

from app.models.media import Media


class MediaResponse(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: Media.Status
    created_at: datetime

    model_config = {"from_attributes": True}