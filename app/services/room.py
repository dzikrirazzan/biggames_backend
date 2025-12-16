"""Room service."""
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.room import Room, RoomCategory, RoomStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.review import Review
from app.schemas.room import (
    RoomCreate, 
    RoomUpdate, 
    RoomResponse, 
    RoomAvailabilityResponse,
    DailySlotResponse,
    AllRoomsSlotsResponse,
    TimeSlot,
)


class RoomService:
    """Service for room operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_rooms(
        self,
        category: RoomCategory | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        capacity: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[RoomResponse], int]:
        """Get rooms with filters."""
        query = select(Room).where(Room.status == RoomStatus.ACTIVE)
        
        if category:
            query = query.where(Room.category == category)
        if min_price is not None:
            query = query.where(Room.base_price_per_hour >= min_price)
        if max_price is not None:
            query = query.where(Room.base_price_per_hour <= max_price)
        if capacity is not None:
            query = query.where(Room.capacity >= capacity)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.options(
            selectinload(Room.images),
            selectinload(Room.units),
        ).offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        rooms = result.scalars().all()
        
        # Get ratings for each room
        room_responses = []
        for room in rooms:
            room_response = await self._room_to_response(room)
            room_responses.append(room_response)
        
        return room_responses, total
    
    async def get_room_by_id(self, room_id: UUID) -> RoomResponse | None:
        """Get room by ID."""
        query = select(Room).where(Room.id == room_id).options(
            selectinload(Room.images),
            selectinload(Room.units),
        )
        result = await self.db.execute(query)
        room = result.scalar_one_or_none()
        
        if not room:
            return None
        
        return await self._room_to_response(room)
    
    async def get_room_entity(self, room_id: UUID) -> Room | None:
        """Get room entity by ID."""
        query = select(Room).where(Room.id == room_id).options(
            selectinload(Room.images),
            selectinload(Room.units),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def check_availability(
        self,
        room_id: UUID,
        start: datetime,
        end: datetime,
    ) -> RoomAvailabilityResponse:
        """Check room availability for a time range."""
        # Get conflicting reservations
        # Overlap condition: startA < endB AND endA > startB
        query = select(Reservation).where(
            and_(
                Reservation.room_id == room_id,
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.start_time < end,
                Reservation.end_time > start,
            )
        )
        result = await self.db.execute(query)
        conflicts = result.scalars().all()
        
        conflicting_data = [
            {
                "reservation_id": str(r.id),
                "start_time": r.start_time.isoformat(),
                "end_time": r.end_time.isoformat(),
            }
            for r in conflicts
        ]
        
        return RoomAvailabilityResponse(
            room_id=room_id,
            start=start,
            end=end,
            is_available=len(conflicts) == 0,
            conflicting_reservations=conflicting_data,
        )
    
    async def create_room(self, room_data: RoomCreate) -> Room:
        """Create a new room."""
        room = Room(**room_data.model_dump())
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)
        return room
    
    async def update_room(self, room_id: UUID, room_data: RoomUpdate) -> Room | None:
        """Update a room."""
        room = await self.get_room_entity(room_id)
        if not room:
            return None
        
        update_data = room_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(room, key, value)
        
        await self.db.flush()
        await self.db.refresh(room)
        return room
    
    async def _room_to_response(self, room: Room) -> RoomResponse:
        """Convert room entity to response with ratings."""
        # Get average rating
        rating_query = select(
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        ).where(Review.room_id == room.id)
        
        rating_result = await self.db.execute(rating_query)
        rating_row = rating_result.one()
        
        avg_rating = float(rating_row.avg_rating) if rating_row.avg_rating else None
        review_count = rating_row.review_count or 0
        
        return RoomResponse(
            id=room.id,
            name=room.name,
            description=room.description,
            category=room.category,
            capacity=room.capacity,
            base_price_per_hour=room.base_price_per_hour,
            status=room.status,
            created_at=room.created_at,
            images=room.images,
            units=room.units,
            avg_rating=avg_rating,
            review_count=review_count,
        )
    
    async def get_all_active_rooms(self) -> list[Room]:
        """Get all active rooms."""
        query = select(Room).where(Room.status == RoomStatus.ACTIVE).options(
            selectinload(Room.images),
            selectinload(Room.units),
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_daily_slots(
        self,
        room_id: UUID,
        target_date: date,
        opening_hour: int = 10,
        closing_hour: int = 22,
    ) -> DailySlotResponse:
        """
        Get hourly time slots for a room on a specific date.
        Returns availability status for each hour.
        """
        room = await self.get_room_entity(room_id)
        if not room:
            raise ValueError("Room not found")
        
        # Build datetime range for the date
        date_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc)
        date_end = date_start + timedelta(days=1)
        
        # Get all reservations for this room on this date (CONFIRMED or PENDING_PAYMENT)
        query = select(Reservation).where(
            and_(
                Reservation.room_id == room_id,
                Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.PENDING_PAYMENT]),
                Reservation.start_time < date_end,
                Reservation.end_time > date_start,
            )
        )
        result = await self.db.execute(query)
        reservations = result.scalars().all()
        
        # Generate time slots
        slots = []
        for hour in range(opening_hour, closing_hour):
            slot_start = datetime(target_date.year, target_date.month, target_date.day, hour, 0, 0, tzinfo=timezone.utc)
            slot_end = datetime(target_date.year, target_date.month, target_date.day, hour + 1, 0, 0, tzinfo=timezone.utc)
            
            # Check if this slot overlaps with any reservation
            is_booked = False
            for res in reservations:
                # Ensure reservation times are timezone-aware for comparison
                res_start = res.start_time
                res_end = res.end_time
                if res_start.tzinfo is None:
                    res_start = res_start.replace(tzinfo=timezone.utc)
                if res_end.tzinfo is None:
                    res_end = res_end.replace(tzinfo=timezone.utc)
                
                # Overlap check: slotStart < resEnd AND slotEnd > resStart
                if slot_start < res_end and slot_end > res_start:
                    is_booked = True
                    break
            
            slots.append(TimeSlot(
                start_hour=hour,
                end_hour=hour + 1,
                start_time=slot_start,
                end_time=slot_end,
                is_available=not is_booked,
                status="booked" if is_booked else "available",
            ))
        
        return DailySlotResponse(
            room_id=room_id,
            room_name=room.name,
            date=target_date.isoformat(),
            slots=slots,
            opening_hour=opening_hour,
            closing_hour=closing_hour,
        )
    
    async def get_all_rooms_daily_slots(
        self,
        target_date: date,
        opening_hour: int = 10,
        closing_hour: int = 22,
    ) -> AllRoomsSlotsResponse:
        """Get hourly time slots for all active rooms on a specific date."""
        rooms = await self.get_all_active_rooms()
        
        room_slots = []
        for room in rooms:
            slot_response = await self.get_daily_slots(room.id, target_date, opening_hour, closing_hour)
            room_slots.append(slot_response)
        
        return AllRoomsSlotsResponse(
            date=target_date.isoformat(),
            rooms=room_slots,
        )
