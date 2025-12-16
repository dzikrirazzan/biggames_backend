"""Tests for room availability and overlap detection."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room, RoomCategory, RoomStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.services.room import RoomService


@pytest_asyncio.fixture
async def room_with_reservation(db_session: AsyncSession):
    """Create a room with an existing confirmed reservation."""
    # Create user
    user = User(
        id=uuid4(),
        email="booker@example.com",
        name="Booker",
        password_hash=get_password_hash("pass123"),
        role=UserRole.USER,
    )
    db_session.add(user)
    
    # Create room
    room = Room(
        id=uuid4(),
        name="Booking Test Room",
        description="Room for testing availability",
        category=RoomCategory.VIP,
        capacity=4,
        base_price_per_hour=Decimal("30000"),
        status=RoomStatus.ACTIVE,
    )
    db_session.add(room)
    await db_session.flush()
    
    # Create existing reservation from 14:00 to 16:00 today
    now = datetime.now(timezone.utc)
    today_14 = now.replace(hour=14, minute=0, second=0, microsecond=0)
    today_16 = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    reservation = Reservation(
        id=uuid4(),
        user_id=user.id,
        room_id=room.id,
        start_time=today_14,
        end_time=today_16,
        duration_hours=Decimal("2"),
        subtotal=Decimal("60000"),
        discount_amount=Decimal("0"),
        total_amount=Decimal("60000"),
        status=ReservationStatus.CONFIRMED,
    )
    db_session.add(reservation)
    await db_session.commit()
    
    return room, reservation, today_14, today_16


class TestRoomAvailability:
    """Test room availability checks."""
    
    @pytest.mark.asyncio
    async def test_no_overlap_before(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time is completely before existing reservation."""
        room, _, existing_start, _ = room_with_reservation
        
        # Request 10:00 - 12:00 (before 14:00-16:00)
        requested_start = existing_start.replace(hour=10)
        requested_end = existing_start.replace(hour=12)
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, requested_start, requested_end
        )
        
        assert result.is_available is True
        assert len(result.conflicting_reservations) == 0
    
    @pytest.mark.asyncio
    async def test_no_overlap_after(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time is completely after existing reservation."""
        room, _, _, existing_end = room_with_reservation
        
        # Request 18:00 - 20:00 (after 14:00-16:00)
        requested_start = existing_end.replace(hour=18)
        requested_end = existing_end.replace(hour=20)
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, requested_start, requested_end
        )
        
        assert result.is_available is True
        assert len(result.conflicting_reservations) == 0
    
    @pytest.mark.asyncio
    async def test_overlap_complete(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time completely contains existing reservation."""
        room, _, existing_start, existing_end = room_with_reservation
        
        # Request 13:00 - 17:00 (contains 14:00-16:00)
        requested_start = existing_start.replace(hour=13)
        requested_end = existing_end.replace(hour=17)
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, requested_start, requested_end
        )
        
        assert result.is_available is False
        assert len(result.conflicting_reservations) == 1
    
    @pytest.mark.asyncio
    async def test_overlap_start(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time overlaps at start."""
        room, _, existing_start, _ = room_with_reservation
        
        # Request 13:00 - 15:00 (overlaps with 14:00-16:00 at start)
        requested_start = existing_start.replace(hour=13)
        requested_end = existing_start.replace(hour=15)
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, requested_start, requested_end
        )
        
        assert result.is_available is False
        assert len(result.conflicting_reservations) == 1
    
    @pytest.mark.asyncio
    async def test_overlap_end(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time overlaps at end."""
        room, _, _, existing_end = room_with_reservation
        
        # Request 15:00 - 17:00 (overlaps with 14:00-16:00 at end)
        requested_start = existing_end.replace(hour=15)
        requested_end = existing_end.replace(hour=17)
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, requested_start, requested_end
        )
        
        assert result.is_available is False
        assert len(result.conflicting_reservations) == 1
    
    @pytest.mark.asyncio
    async def test_overlap_exact(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time exactly matches existing reservation."""
        room, _, existing_start, existing_end = room_with_reservation
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, existing_start, existing_end
        )
        
        assert result.is_available is False
        assert len(result.conflicting_reservations) == 1
    
    @pytest.mark.asyncio
    async def test_overlap_inside(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time is inside existing reservation."""
        room, _, existing_start, existing_end = room_with_reservation
        
        # Request 14:30 - 15:30 (inside 14:00-16:00)
        requested_start = existing_start + timedelta(minutes=30)
        requested_end = existing_end - timedelta(minutes=30)
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, requested_start, requested_end
        )
        
        assert result.is_available is False
        assert len(result.conflicting_reservations) == 1
    
    @pytest.mark.asyncio
    async def test_no_overlap_adjacent_before(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time ends exactly when existing starts."""
        room, _, existing_start, _ = room_with_reservation
        
        # Request 12:00 - 14:00 (adjacent to 14:00-16:00)
        requested_start = existing_start.replace(hour=12)
        requested_end = existing_start  # Ends at 14:00
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, requested_start, requested_end
        )
        
        # Should be available - no overlap at boundary
        assert result.is_available is True
    
    @pytest.mark.asyncio
    async def test_no_overlap_adjacent_after(self, db_session: AsyncSession, room_with_reservation):
        """Test availability check when requested time starts exactly when existing ends."""
        room, _, _, existing_end = room_with_reservation
        
        # Request 16:00 - 18:00 (adjacent to 14:00-16:00)
        requested_start = existing_end  # Starts at 16:00
        requested_end = existing_end.replace(hour=18)
        
        room_service = RoomService(db_session)
        result = await room_service.check_availability(
            room.id, requested_start, requested_end
        )
        
        # Should be available - no overlap at boundary
        assert result.is_available is True
    
    @pytest.mark.asyncio
    async def test_cancelled_reservation_not_blocking(self, db_session: AsyncSession):
        """Test that cancelled reservations don't block availability."""
        # Create user
        user = User(
            id=uuid4(),
            email="canceller@example.com",
            name="Canceller",
            password_hash=get_password_hash("pass123"),
            role=UserRole.USER,
        )
        db_session.add(user)
        
        # Create room
        room = Room(
            id=uuid4(),
            name="Cancelled Test Room",
            category=RoomCategory.VIP,
            capacity=4,
            base_price_per_hour=Decimal("30000"),
            status=RoomStatus.ACTIVE,
        )
        db_session.add(room)
        await db_session.flush()
        
        # Create CANCELLED reservation
        now = datetime.now(timezone.utc)
        start = now.replace(hour=14, minute=0)
        end = now.replace(hour=16, minute=0)
        
        reservation = Reservation(
            id=uuid4(),
            user_id=user.id,
            room_id=room.id,
            start_time=start,
            end_time=end,
            duration_hours=Decimal("2"),
            subtotal=Decimal("60000"),
            discount_amount=Decimal("0"),
            total_amount=Decimal("60000"),
            status=ReservationStatus.CANCELLED,  # Cancelled!
        )
        db_session.add(reservation)
        await db_session.commit()
        
        # Check availability for same time slot
        room_service = RoomService(db_session)
        result = await room_service.check_availability(room.id, start, end)
        
        assert result.is_available is True
        assert len(result.conflicting_reservations) == 0
