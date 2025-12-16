"""Menu item model."""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import String, Text, Enum, Boolean, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class MenuCategory(str, enum.Enum):
    """Menu category."""
    FOOD = "FOOD"
    BEVERAGE = "BEVERAGE"  # Changed from DRINK for consistency
    SNACK = "SNACK"


class MenuItem(Base):
    """Menu item model for F&B."""
    
    __tablename__ = "menu_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[MenuCategory] = mapped_column(Enum(MenuCategory), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Relationships
    order_items: Mapped[list["FbOrderItem"]] = relationship(  # noqa: F821
        "FbOrderItem",
        back_populates="menu_item",
        lazy="selectin",
    )
