"""AI schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.ai import EventType
from app.models.room import RoomCategory


class UserEventCreate(BaseModel):
    """Schema for creating a user event."""
    room_id: UUID
    event_type: EventType
    rating_value: int | None = Field(default=None, ge=1, le=5)


class RecommendedRoom(BaseModel):
    """Schema for a recommended room."""
    room_id: UUID
    name: str
    category: RoomCategory
    capacity: int
    base_price_per_hour: Decimal
    avg_rating: float | None = None
    review_count: int = 0
    similarity_score: float
    final_score: float
    reason: str

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    recommendations: list[RecommendedRoom]
    is_cold_start: bool = False
    user_event_count: int = 0
