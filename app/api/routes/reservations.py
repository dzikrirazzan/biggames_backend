"""Reservation routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.services.reservation import ReservationService
from app.api.deps import get_current_user


router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    reservation_data: ReservationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new reservation."""
    reservation_service = ReservationService(db)
    try:
        return await reservation_service.create_reservation(
            user_id=current_user.id,
            reservation_data=reservation_data,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=list[ReservationResponse])
async def get_my_reservations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's reservations."""
    reservation_service = ReservationService(db)
    return await reservation_service.get_user_reservations(current_user.id)


@router.post("/{reservation_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_reservation(
    reservation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a reservation."""
    reservation_service = ReservationService(db)
    try:
        await reservation_service.cancel_reservation(reservation_id, current_user.id)
        return {"message": "Reservation cancelled successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
