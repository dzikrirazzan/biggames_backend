"""Reservation models."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Enum, DateTime, func, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ReservationStatus(str, enum.Enum):
    """Reservation status."""
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Reservation(Base):
    """Reservation model."""
    
    __tablename__ = "reservations"
    
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
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus),
        default=ReservationStatus.PENDING_PAYMENT,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="reservations",
    )
    room: Mapped["Room"] = relationship(  # noqa: F821
        "Room",
        back_populates="reservations",
    )
    addons: Mapped[list["ReservationAddon"]] = relationship(
        "ReservationAddon",
        back_populates="reservation",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    payment: Mapped["Payment | None"] = relationship(  # noqa: F821
        "Payment",
        back_populates="reservation",
        uselist=False,
        lazy="selectin",
    )
    review: Mapped["Review | None"] = relationship(  # noqa: F821
        "Review",
        back_populates="reservation",
        uselist=False,
        lazy="selectin",
    )
    fb_orders: Mapped[list["FbOrder"]] = relationship(  # noqa: F821
        "FbOrder",
        back_populates="reservation",
        lazy="selectin",
    )


class ReservationAddon(Base):
    """Reservation addon model."""
    
    __tablename__ = "reservation_addons"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    reservation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reservations.id", ondelete="CASCADE"),
        nullable=False,
    )
    addon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("addons.id", ondelete="CASCADE"),
        nullable=False,
    )
    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Relationships
    reservation: Mapped["Reservation"] = relationship(
        "Reservation",
        back_populates="addons",
    )
    addon: Mapped["Addon"] = relationship(  # noqa: F821
        "Addon",
        back_populates="reservation_addons",
    )
