"""Addon schemas."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.addon import AddonPriceType


class AddonCreate(BaseModel):
    """Schema for creating an addon."""
    name: str = Field(..., min_length=1, max_length=255)
    price_type: AddonPriceType
    price_amount: Decimal = Field(..., gt=0)
    is_active: bool = True


class AddonResponse(BaseModel):
    """Schema for addon response."""
    id: UUID
    name: str
    price_type: AddonPriceType
    price_amount: Decimal
    is_active: bool

    class Config:
        from_attributes = True
