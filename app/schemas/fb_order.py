"""F&B order schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.fb_order import FbOrderStatus


class FbOrderItemCreate(BaseModel):
    """Schema for creating an F&B order item."""
    menu_item_id: UUID
    qty: int = Field(..., ge=1)


class FbOrderItemResponse(BaseModel):
    """Schema for F&B order item response."""
    id: UUID
    menu_item_id: UUID
    menu_item_name: str | None = None
    qty: int
    price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class FbOrderCreate(BaseModel):
    """Schema for creating an F&B order."""
    reservation_id: UUID | None = None
    room_id: UUID | None = None
    notes: str | None = None
    items: list[FbOrderItemCreate] = Field(..., min_length=1)


class FbOrderResponse(BaseModel):
    """Schema for F&B order response."""
    id: UUID
    user_id: UUID
    reservation_id: UUID | None
    room_id: UUID | None
    room_name: str | None = None
    status: FbOrderStatus
    notes: str | None
    subtotal: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    created_at: datetime
    items: list[FbOrderItemResponse] = []

    class Config:
        from_attributes = True


class FbOrderStatusUpdate(BaseModel):
    """Schema for updating F&B order status."""
    status: FbOrderStatus
