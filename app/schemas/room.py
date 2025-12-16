"""Room schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.room import RoomCategory, RoomStatus, ConsoleType, UnitStatus


class UnitCreate(BaseModel):
    """Schema for creating a unit."""
    console_type: ConsoleType
    jumlah_stick: int = Field(default=2, ge=1, le=8)
    status: UnitStatus = UnitStatus.ACTIVE


class UnitResponse(BaseModel):
    """Schema for unit response."""
    id: UUID
    console_type: ConsoleType
    jumlah_stick: int
    status: UnitStatus

    class Config:
        from_attributes = True


class RoomImageResponse(BaseModel):
    """Schema for room image response."""
    id: UUID
    url: str

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    """Schema for creating a room."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: RoomCategory
    capacity: int = Field(..., ge=1, le=20)
    base_price_per_hour: Decimal = Field(..., gt=0)
    status: RoomStatus = RoomStatus.ACTIVE


class RoomUpdate(BaseModel):
    """Schema for updating a room."""
    name: str | None = None
    description: str | None = None
    category: RoomCategory | None = None
    capacity: int | None = Field(default=None, ge=1, le=20)
    base_price_per_hour: Decimal | None = Field(default=None, gt=0)
    status: RoomStatus | None = None


class RoomResponse(BaseModel):
    """Schema for room response."""
    id: UUID
    name: str
    description: str | None
    category: RoomCategory
    capacity: int
    base_price_per_hour: Decimal
    status: RoomStatus
    created_at: datetime
    images: list[RoomImageResponse] = []
    units: list[UnitResponse] = []
    avg_rating: float | None = None
    review_count: int = 0

    class Config:
        from_attributes = True


class RoomListResponse(BaseModel):
    """Schema for room list response."""
    rooms: list[RoomResponse]
    total: int
    page: int
    page_size: int


class RoomAvailabilityResponse(BaseModel):
    """Schema for room availability response."""
    room_id: UUID
    start: datetime
    end: datetime
    is_available: bool
    conflicting_reservations: list[dict] = []


class TimeSlot(BaseModel):
    """Schema for a time slot."""
    start_hour: int = Field(..., ge=0, le=23)
    end_hour: int = Field(..., ge=1, le=24)
    start_time: datetime
    end_time: datetime
    is_available: bool
    status: str  # "available", "booked", "partial"


class DailySlotResponse(BaseModel):
    """Schema for daily time slots response."""
    room_id: UUID
    room_name: str
    date: str  # YYYY-MM-DD
    slots: list[TimeSlot]
    opening_hour: int = 10  # Jam buka
    closing_hour: int = 22  # Jam tutup


class AllRoomsSlotsResponse(BaseModel):
    """Schema for all rooms daily slots."""
    date: str  # YYYY-MM-DD
    rooms: list[DailySlotResponse]
