"""Room routes."""
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.room import RoomCategory
from app.schemas.room import (
    RoomResponse, 
    RoomListResponse, 
    RoomAvailabilityResponse,
    DailySlotResponse,
    AllRoomsSlotsResponse,
)
from app.services.room import RoomService


router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("/all/slots", response_model=AllRoomsSlotsResponse)
async def get_all_rooms_daily_slots(
    target_date: date = Query(..., alias="date", description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get hourly time slots for ALL rooms on a specific date.
    Frontend can display this as a schedule grid showing which rooms/slots are booked.
    """
    room_service = RoomService(db)
    return await room_service.get_all_rooms_daily_slots(target_date)


@router.get("", response_model=RoomListResponse)
async def get_rooms(
    category: RoomCategory | None = None,
    min_price: Decimal | None = Query(None, alias="minPrice"),
    max_price: Decimal | None = Query(None, alias="maxPrice"),
    capacity: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
):
    """Get rooms with optional filters."""
    room_service = RoomService(db)
    rooms, total = await room_service.get_rooms(
        category=category,
        min_price=min_price,
        max_price=max_price,
        capacity=capacity,
        page=page,
        page_size=page_size,
    )
    
    return RoomListResponse(
        rooms=rooms,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get room by ID."""
    room_service = RoomService(db)
    room = await room_service.get_room_by_id(room_id)
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    
    return room


@router.get("/{room_id}/availability", response_model=RoomAvailabilityResponse)
async def check_room_availability(
    room_id: UUID,
    start: datetime = Query(..., description="Start time in ISO format"),
    end: datetime = Query(..., description="End time in ISO format"),
    db: AsyncSession = Depends(get_db),
):
    """Check room availability for a time range."""
    if start >= end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )
    
    room_service = RoomService(db)
    
    # Verify room exists
    room = await room_service.get_room_by_id(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    
    return await room_service.check_availability(room_id, start, end)


@router.get("/{room_id}/slots", response_model=DailySlotResponse)
async def get_room_daily_slots(
    room_id: UUID,
    target_date: date = Query(..., alias="date", description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get hourly time slots for a room on a specific date.
    Returns availability status for each hour slot.
    """
    room_service = RoomService(db)
    
    room = await room_service.get_room_by_id(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )
    
    return await room_service.get_daily_slots(room_id, target_date)
