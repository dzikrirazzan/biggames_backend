"""AI models for room recommendations."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, DateTime, func, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.session import Base


class EventType(str, enum.Enum):
    """User event types."""
    VIEW_ROOM = "VIEW_ROOM"
    CLICK_ROOM = "CLICK_ROOM"
    BOOK_ROOM = "BOOK_ROOM"
    RATE_ROOM = "RATE_ROOM"


class UserEvent(Base):
    """User event model for tracking interactions."""
    
    __tablename__ = "user_events"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    rating_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="user_events",
    )
    room: Mapped["Room"] = relationship(  # noqa: F821
        "Room",
        back_populates="user_events",
    )


class RoomEmbedding(Base):
    """Room embedding model for AI recommendations.
    
    Note: Vector dimension should match the embedding provider:
    - OpenAI text-embedding-3-small: 1536
    - HuggingFace paraphrase-multilingual-MiniLM-L12-v2: 384
    """
    
    __tablename__ = "room_embeddings"
    
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # Using flexible dimension - update via migration if changing provider
    embedding = mapped_column(Vector(384), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    room: Mapped["Room"] = relationship(  # noqa: F821
        "Room",
        back_populates="embedding",
    )
