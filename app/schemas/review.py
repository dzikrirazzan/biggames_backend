"""Review schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    """Schema for creating a review."""
    reservation_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewResponse(BaseModel):
    """Schema for review response."""
    id: UUID
    user_id: UUID
    user_name: str | None = None
    room_id: UUID
    reservation_id: UUID
    rating: int
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True
