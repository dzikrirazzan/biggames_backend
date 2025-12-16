"""Reservation schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.reservation import ReservationStatus
from app.models.payment import PaymentMethod


class ReservationAddonCreate(BaseModel):
    """Schema for creating a reservation addon."""
    addon_id: UUID
    qty: int = Field(default=1, ge=1)


class ReservationAddonResponse(BaseModel):
    """Schema for reservation addon response."""
    id: UUID
    addon_id: UUID
    addon_name: str | None = None
    qty: int
    price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class ReservationCreate(BaseModel):
    """Schema for creating a reservation."""
    room_id: UUID
    start_time: datetime
    end_time: datetime
    promo_code: str | None = None
    payment_method: PaymentMethod = PaymentMethod.QRIS
    notes: str | None = None
    addons: list[ReservationAddonCreate] = []


class ReservationResponse(BaseModel):
    """Schema for reservation response."""
    id: UUID
    user_id: UUID
    user_name: str | None = None
    user_email: str | None = None
    room_id: UUID
    room_name: str | None = None
    start_time: datetime
    end_time: datetime
    duration_hours: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    status: ReservationStatus
    notes: str | None
    created_at: datetime
    addons: list[ReservationAddonResponse] = []
    payment_status: str | None = None
    payment_method: str | None = None

    class Config:
        from_attributes = True


class ReservationStatusUpdate(BaseModel):
    """Schema for updating reservation status."""
    status: ReservationStatus
