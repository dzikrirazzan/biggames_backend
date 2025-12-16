"""User model."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserRole(str, enum.Enum):
    """User roles."""
    USER = "USER"
    ADMIN = "ADMIN"
    FINANCE = "FINANCE"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    reservations: Mapped[list["Reservation"]] = relationship(  # noqa: F821
        "Reservation",
        back_populates="user",
        lazy="selectin",
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review",
        back_populates="user",
        lazy="selectin",
    )
    fb_orders: Mapped[list["FbOrder"]] = relationship(  # noqa: F821
        "FbOrder",
        back_populates="user",
        lazy="selectin",
    )
    user_events: Mapped[list["UserEvent"]] = relationship(  # noqa: F821
        "UserEvent",
        back_populates="user",
        lazy="selectin",
    )
    confirmed_payments: Mapped[list["Payment"]] = relationship(  # noqa: F821
        "Payment",
        back_populates="confirmed_by_admin",
        foreign_keys="Payment.confirmed_by_admin_id",
        lazy="selectin",
    )
