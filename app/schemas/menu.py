"""Menu item schemas."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.menu import MenuCategory


class MenuItemCreate(BaseModel):
    """Schema for creating a menu item."""
    name: str = Field(..., min_length=1, max_length=255)
    category: MenuCategory
    description: str | None = None
    price: Decimal = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    is_active: bool = True
    image_url: str | None = None


class MenuItemResponse(BaseModel):
    """Schema for menu item response."""
    id: UUID
    name: str
    category: MenuCategory
    description: str | None
    price: Decimal
    stock: int
    is_active: bool
    image_url: str | None

    class Config:
        from_attributes = True
