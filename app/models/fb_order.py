"""F&B order models."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Text, Enum, DateTime, func, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FbOrderStatus(str, enum.Enum):
    """F&B order status."""
    PENDING = "PENDING"
    COOKING = "COOKING"
    DELIVERING = "DELIVERING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class FbOrder(Base):
    """F&B order model."""
    
    __tablename__ = "fb_orders"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reservation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reservations.id", ondelete="SET NULL"),
        nullable=True,
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[FbOrderStatus] = mapped_column(
        Enum(FbOrderStatus),
        default=FbOrderStatus.PENDING,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="fb_orders",
    )
    reservation: Mapped["Reservation | None"] = relationship(  # noqa: F821
        "Reservation",
        back_populates="fb_orders",
    )
    room: Mapped["Room | None"] = relationship(  # noqa: F821
        "Room",
        lazy="selectin",
    )
    items: Mapped[list["FbOrderItem"]] = relationship(
        "FbOrderItem",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class FbOrderItem(Base):
    """F&B order item model."""
    
    __tablename__ = "fb_order_items"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fb_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menu_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Relationships
    order: Mapped["FbOrder"] = relationship(
        "FbOrder",
        back_populates="items",
    )
    menu_item: Mapped["MenuItem"] = relationship(  # noqa: F821
        "MenuItem",
        back_populates="order_items",
    )
