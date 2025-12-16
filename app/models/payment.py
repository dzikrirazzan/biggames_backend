"""Payment model."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Enum, DateTime, func, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PaymentMethod(str, enum.Enum):
    """Payment method."""
    QRIS = "QRIS"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatus(str, enum.Enum):
    """Payment status."""
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    PAID = "PAID"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Payment(Base):
    """Payment model for manual verification."""
    
    __tablename__ = "payments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    reservation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reservations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.WAITING_CONFIRMATION,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    proof_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    reservation: Mapped["Reservation"] = relationship(  # noqa: F821
        "Reservation",
        back_populates="payment",
    )
    confirmed_by_admin: Mapped["User | None"] = relationship(  # noqa: F821
        "User",
        back_populates="confirmed_payments",
        foreign_keys=[confirmed_by_admin_id],
    )
