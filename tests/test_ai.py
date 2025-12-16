"""Tests for AI recommendation system."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.room import Room, RoomCategory, RoomStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.review import Review
from app.models.ai import UserEvent, EventType, RoomEmbedding
from app.core.security import get_password_hash
from app.services.ai import AIService
from app.services.embedding import HuggingFaceEmbeddingProvider


class TestHuggingFaceEmbeddingProvider:
    """Tests for HuggingFaceEmbeddingProvider."""
    
    @pytest.mark.asyncio
    async def test_embedding_same_text(self):
        """Test that same text produces same embedding."""
        provider = HuggingFaceEmbeddingProvider()
        
        text = "VIP Room with PS5 Pro"
        emb1 = await provider.get_embedding(text)
        emb2 = await provider.get_embedding(text)
        
        assert np.allclose(emb1, emb2)
    
    @pytest.mark.asyncio
    async def test_different_text_different_embedding(self):
        """Test that different texts produce different embeddings."""
        provider = HuggingFaceEmbeddingProvider()
        
        emb1 = await provider.get_embedding("VIP Room premium")
        emb2 = await provider.get_embedding("Regular Room budget")
        
        # Should be different
        assert not np.allclose(emb1, emb2)
    
    @pytest.mark.asyncio
    async def test_embedding_dimension(self):
        """Test that embedding has correct dimension."""
        provider = HuggingFaceEmbeddingProvider()
        
        emb = await provider.get_embedding("Test room")
        
        assert len(emb) == 384
        assert provider.dimension == 384
    
    @pytest.mark.asyncio
    async def test_embedding_normalized(self):
        """Test that embedding is normalized to unit length."""
        provider = HuggingFaceEmbeddingProvider()
        
        emb = await provider.get_embedding("Any text here")
        
        norm = np.linalg.norm(emb)
        assert np.isclose(norm, 1.0)
    
    @pytest.mark.asyncio
    async def test_indonesian_language_support(self):
        """Test that provider handles Indonesian text."""
        provider = HuggingFaceEmbeddingProvider()
        
        text_id = "Ruangan VIP dengan PS5 dan 4 controller"
        emb = await provider.get_embedding(text_id)
        
        assert len(emb) == 384
        assert np.isclose(np.linalg.norm(emb), 1.0)


@pytest_asyncio.fixture
async def cold_start_setup(db_session: AsyncSession):
    """Set up rooms for cold start testing (no user events)."""
    # Create rooms with different booking counts
    now = datetime.now(timezone.utc)
    
    # Create user for bookings
    booker = User(
        id=uuid4(),
        email="booker@example.com",
        name="Booker",
        password_hash=get_password_hash("pass123"),
        role=UserRole.USER,
    )
    db_session.add(booker)
    
    # Create rooms
    rooms = []
    for i, (name, category, bookings, rating) in enumerate([
        ("Popular VIP", RoomCategory.VIP, 10, 4.8),
        ("Average PS5", RoomCategory.PS_SERIES, 5, 4.0),
        ("Unpopular Regular", RoomCategory.REGULER, 1, 3.5),
        ("New Simulator", RoomCategory.SIMULATOR, 0, None),
    ]):
        room = Room(
            id=uuid4(),
            name=name,
            description=f"Test room {i}",
            category=category,
            capacity=4,
            base_price_per_hour=Decimal("25000"),
            status=RoomStatus.ACTIVE,
        )
        db_session.add(room)
        await db_session.flush()
        
        # Create embeddings
        provider = FakeEmbeddingProvider()
        emb = await provider.get_embedding(f"{name} {category.value}")
        room_emb = RoomEmbedding(
            room_id=room.id,
            embedding=emb,
        )
        db_session.add(room_emb)
        
        # Create bookings
        for j in range(bookings):
            res_time = now - timedelta(days=j + 1)
            reservation = Reservation(
                id=uuid4(),
                user_id=booker.id,
                room_id=room.id,
                start_time=res_time,
                end_time=res_time + timedelta(hours=2),
                duration_hours=Decimal("2"),
                subtotal=Decimal("50000"),
                discount_amount=Decimal("0"),
                total_amount=Decimal("50000"),
                status=ReservationStatus.COMPLETED,
            )
            db_session.add(reservation)
            
            # Create payment
            payment = Payment(
                id=uuid4(),
                reservation_id=reservation.id,
                method=PaymentMethod.QRIS,
                status=PaymentStatus.PAID,
                amount=Decimal("50000"),
            )
            db_session.add(payment)
        
        # Create review if rating specified
        if rating is not None and bookings > 0:
            # Need a reservation for the review
            res_query = select(Reservation).where(Reservation.room_id == room.id).limit(1)
            res_result = await db_session.execute(res_query)
            res = res_result.scalar_one_or_none()
            
            if res:
                review = Review(
                    id=uuid4(),
                    user_id=booker.id,
                    room_id=room.id,
                    reservation_id=res.id,
                    rating=int(rating),
                    comment=f"Test review for {name}",
                )
                db_session.add(review)
        
        rooms.append(room)
    
    await db_session.commit()
    
    # Create a new user with no events (cold start user)
    cold_user = User(
        id=uuid4(),
        email="cold@example.com",
        name="Cold Start User",
        password_hash=get_password_hash("pass123"),
        role=UserRole.USER,
    )
    db_session.add(cold_user)
    await db_session.commit()
    await db_session.refresh(cold_user)
    
    return rooms, cold_user


class TestColdStartRecommendations:
    """Tests for cold start (new user) recommendations."""
    
    @pytest.mark.asyncio
    async def test_cold_start_no_user(self, db_session: AsyncSession, cold_start_setup):
        """Test recommendations with no user (anonymous)."""
        rooms, _ = cold_start_setup
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        result = await ai_service.get_recommendations(user_id=None, limit=8)
        
        assert result.is_cold_start is True
        assert result.user_event_count == 0
        assert len(result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_cold_start_new_user(self, db_session: AsyncSession, cold_start_setup):
        """Test recommendations for new user with no events."""
        rooms, cold_user = cold_start_setup
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        result = await ai_service.get_recommendations(user_id=cold_user.id, limit=8)
        
        assert result.is_cold_start is True
        assert result.user_event_count == 0
        assert len(result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_cold_start_returns_trending(self, db_session: AsyncSession, cold_start_setup):
        """Test that cold start returns trending rooms (popular + high rated)."""
        rooms, cold_user = cold_start_setup
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        result = await ai_service.get_recommendations(user_id=cold_user.id, limit=8)
        
        # Popular VIP should be near top (most bookings + high rating)
        room_names = [r.name for r in result.recommendations]
        
        # The most popular room should be in the recommendations
        assert "Popular VIP" in room_names
        
        # All recommendations should have "Trending" in reason
        for rec in result.recommendations:
            assert "Trending" in rec.reason or "trending" in rec.reason.lower()
    
    @pytest.mark.asyncio
    async def test_cold_start_user_with_few_events(self, db_session: AsyncSession, cold_start_setup):
        """Test that users with < 3 events get cold start recommendations."""
        rooms, cold_user = cold_start_setup
        
        # Add only 2 events (below threshold of 3)
        for i, room in enumerate(rooms[:2]):
            event = UserEvent(
                id=uuid4(),
                user_id=cold_user.id,
                room_id=room.id,
                event_type=EventType.VIEW_ROOM,
            )
            db_session.add(event)
        
        await db_session.commit()
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        result = await ai_service.get_recommendations(user_id=cold_user.id, limit=8)
        
        assert result.is_cold_start is True
        assert result.user_event_count == 2


@pytest_asyncio.fixture
async def personalized_setup(db_session: AsyncSession):
    """Set up data for personalized recommendations testing."""
    provider = FakeEmbeddingProvider()
    
    # Create user with events
    user = User(
        id=uuid4(),
        email="active@example.com",
        name="Active User",
        password_hash=get_password_hash("pass123"),
        role=UserRole.USER,
    )
    db_session.add(user)
    
    # Create diverse rooms
    rooms = []
    for name, category, price in [
        ("VIP Elite", RoomCategory.VIP, Decimal("40000")),
        ("VIP Standard", RoomCategory.VIP, Decimal("30000")),
        ("PS5 Premium", RoomCategory.PS_SERIES, Decimal("25000")),
        ("PS4 Budget", RoomCategory.PS_SERIES, Decimal("15000")),
        ("Regular Basic", RoomCategory.REGULER, Decimal("12000")),
        ("Racing Sim", RoomCategory.SIMULATOR, Decimal("35000")),
    ]:
        room = Room(
            id=uuid4(),
            name=name,
            description=f"Description for {name}",
            category=category,
            capacity=4,
            base_price_per_hour=price,
            status=RoomStatus.ACTIVE,
        )
        db_session.add(room)
        await db_session.flush()
        
        # Add embedding
        emb = await provider.get_embedding(f"{name} {category.value} {price}")
        room_emb = RoomEmbedding(
            room_id=room.id,
            embedding=emb,
        )
        db_session.add(room_emb)
        
        rooms.append(room)
    
    await db_session.commit()
    
    # Add user events - user prefers VIP rooms
    vip_rooms = [r for r in rooms if r.category == RoomCategory.VIP]
    now = datetime.now(timezone.utc)
    
    for i, room in enumerate(vip_rooms):
        # Multiple events per VIP room
        for event_type in [EventType.VIEW_ROOM, EventType.CLICK_ROOM, EventType.BOOK_ROOM]:
            event = UserEvent(
                id=uuid4(),
                user_id=user.id,
                room_id=room.id,
                event_type=event_type,
                created_at=now - timedelta(hours=i * 10),
            )
            db_session.add(event)
    
    # Add a rating event
    rate_event = UserEvent(
        id=uuid4(),
        user_id=user.id,
        room_id=vip_rooms[0].id,
        event_type=EventType.RATE_ROOM,
        rating_value=5,
        created_at=now - timedelta(hours=1),
    )
    db_session.add(rate_event)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    return rooms, user


class TestPersonalizedRecommendations:
    """Tests for personalized recommendations."""
    
    @pytest.mark.asyncio
    async def test_personalized_not_cold_start(
        self, db_session: AsyncSession, personalized_setup
    ):
        """Test that users with enough events get personalized recommendations."""
        rooms, user = personalized_setup
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        result = await ai_service.get_recommendations(user_id=user.id, limit=8)
        
        assert result.is_cold_start is False
        assert result.user_event_count >= 3
    
    @pytest.mark.asyncio
    async def test_recommendations_have_scores(
        self, db_session: AsyncSession, personalized_setup
    ):
        """Test that recommendations have similarity and final scores."""
        rooms, user = personalized_setup
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        result = await ai_service.get_recommendations(user_id=user.id, limit=8)
        
        for rec in result.recommendations:
            assert rec.similarity_score is not None
            assert rec.final_score is not None
            assert rec.reason is not None
            assert len(rec.reason) > 0
    
    @pytest.mark.asyncio
    async def test_recommendations_sorted_by_final_score(
        self, db_session: AsyncSession, personalized_setup
    ):
        """Test that recommendations are sorted by final score descending."""
        rooms, user = personalized_setup
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        result = await ai_service.get_recommendations(user_id=user.id, limit=8)
        
        scores = [r.final_score for r in result.recommendations]
        assert scores == sorted(scores, reverse=True)


class TestEventLogging:
    """Tests for user event logging."""
    
    @pytest.mark.asyncio
    async def test_log_view_event(self, db_session: AsyncSession):
        """Test logging a VIEW_ROOM event."""
        # Create user and room
        user = User(
            id=uuid4(),
            email="logger@example.com",
            name="Logger",
            password_hash=get_password_hash("pass123"),
            role=UserRole.USER,
        )
        room = Room(
            id=uuid4(),
            name="Event Test Room",
            category=RoomCategory.VIP,
            capacity=4,
            base_price_per_hour=Decimal("30000"),
            status=RoomStatus.ACTIVE,
        )
        db_session.add(user)
        db_session.add(room)
        await db_session.commit()
        
        from app.schemas.ai import UserEventCreate
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        event_data = UserEventCreate(
            room_id=room.id,
            event_type=EventType.VIEW_ROOM,
        )
        
        event = await ai_service.log_event(user.id, event_data)
        
        assert event.id is not None
        assert event.user_id == user.id
        assert event.room_id == room.id
        assert event.event_type == EventType.VIEW_ROOM
        assert event.rating_value is None
    
    @pytest.mark.asyncio
    async def test_log_rate_event_with_value(self, db_session: AsyncSession):
        """Test logging a RATE_ROOM event with rating value."""
        user = User(
            id=uuid4(),
            email="rater@example.com",
            name="Rater",
            password_hash=get_password_hash("pass123"),
            role=UserRole.USER,
        )
        room = Room(
            id=uuid4(),
            name="Rate Test Room",
            category=RoomCategory.VIP,
            capacity=4,
            base_price_per_hour=Decimal("30000"),
            status=RoomStatus.ACTIVE,
        )
        db_session.add(user)
        db_session.add(room)
        await db_session.commit()
        
        from app.schemas.ai import UserEventCreate
        
        ai_service = AIService(db_session, FakeEmbeddingProvider())
        event_data = UserEventCreate(
            room_id=room.id,
            event_type=EventType.RATE_ROOM,
            rating_value=5,
        )
        
        event = await ai_service.log_event(user.id, event_data)
        
        assert event.event_type == EventType.RATE_ROOM
        assert event.rating_value == 5
