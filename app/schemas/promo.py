"""Promo schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.promo import DiscountType


class PromoCreate(BaseModel):
    """Schema for creating a promo."""
    code: str = Field(..., min_length=1, max_length=50)
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    is_active: bool = True


class PromoResponse(BaseModel):
    """Schema for promo response."""
    id: UUID
    code: str
    discount_type: DiscountType
    discount_value: Decimal
    start_date: datetime
    end_date: datetime
    is_active: bool

    class Config:
        from_attributes = True


class PromoValidateRequest(BaseModel):
    """Schema for validating a promo code."""
    code: str
    subtotal: Decimal = Field(..., gt=0)


class PromoValidateResponse(BaseModel):
    """Schema for promo validation response."""
    valid: bool
    code: str
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = None
    discount_amount: Decimal | None = None
    message: str
