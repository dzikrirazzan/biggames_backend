"""Room models."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Enum, DateTime, func, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RoomCategory(str, enum.Enum):
    """Room categories."""
    VIP = "VIP"
    REGULER = "REGULER"
    PS_SERIES = "PS_SERIES"
    SIMULATOR = "SIMULATOR"


class RoomStatus(str, enum.Enum):
    """Room status."""
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class ConsoleType(str, enum.Enum):
    """Console types."""
    PS4_SLIM = "PS4_SLIM"
    PS4_PRO = "PS4_PRO"
    PS5_SLIM = "PS5_SLIM"
    PS5_PRO = "PS5_PRO"
    NINTENDO_SWITCH = "NINTENDO_SWITCH"


class UnitStatus(str, enum.Enum):
    """Unit status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Room(Base):
    """Room model."""
    
    __tablename__ = "rooms"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[RoomCategory] = mapped_column(Enum(RoomCategory), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    base_price_per_hour: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[RoomStatus] = mapped_column(
        Enum(RoomStatus),
        default=RoomStatus.ACTIVE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    images: Mapped[list["RoomImage"]] = relationship(
        "RoomImage",
        back_populates="room",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    units: Mapped[list["Unit"]] = relationship(
        "Unit",
        back_populates="room",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    reservations: Mapped[list["Reservation"]] = relationship(  # noqa: F821
        "Reservation",
        back_populates="room",
        lazy="selectin",
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review",
        back_populates="room",
        lazy="selectin",
    )
    user_events: Mapped[list["UserEvent"]] = relationship(  # noqa: F821
        "UserEvent",
        back_populates="room",
        lazy="selectin",
    )
    embedding: Mapped["RoomEmbedding | None"] = relationship(  # noqa: F821
        "RoomEmbedding",
        back_populates="room",
        uselist=False,
        lazy="selectin",
    )


class RoomImage(Base):
    """Room image model."""
    
    __tablename__ = "room_images"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="images")


class Unit(Base):
    """Unit model (consoles in a room)."""
    
    __tablename__ = "units"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    console_type: Mapped[ConsoleType] = mapped_column(Enum(ConsoleType), nullable=False)
    jumlah_stick: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus),
        default=UnitStatus.ACTIVE,
        nullable=False,
    )
    
    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="units")
