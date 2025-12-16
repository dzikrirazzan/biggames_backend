"""Addon model."""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import String, Enum, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AddonPriceType(str, enum.Enum):
    """Addon price type."""
    FLAT = "FLAT"
    PER_HOUR = "PER_HOUR"


class Addon(Base):
    """Addon model."""
    
    __tablename__ = "addons"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_type: Mapped[AddonPriceType] = mapped_column(Enum(AddonPriceType), nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    reservation_addons: Mapped[list["ReservationAddon"]] = relationship(  # noqa: F821
        "ReservationAddon",
        back_populates="addon",
        lazy="selectin",
    )
