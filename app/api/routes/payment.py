"""Payment routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import PaymentInstructionsResponse, PaymentProofUpload, PaymentResponse
from app.services.payment import PaymentService
from app.services.reservation import ReservationService
from app.api.deps import get_current_user


router = APIRouter(tags=["Payments"])


@router.get("/reservations/{reservation_id}/payment-instructions", response_model=PaymentInstructionsResponse)
async def get_payment_instructions(
    reservation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment instructions for a reservation."""
    # Verify reservation belongs to user
    reservation_service = ReservationService(db)
    reservation = await reservation_service.get_reservation_by_id(reservation_id)
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )
    
    if reservation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this reservation",
        )
    
    payment_service = PaymentService(db)
    instructions = await payment_service.get_payment_instructions(reservation_id)
    
    if not instructions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    return instructions


@router.post("/reservations/{reservation_id}/payment-proof", response_model=PaymentResponse)
async def upload_payment_proof(
    reservation_id: UUID,
    proof_data: PaymentProofUpload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload payment proof for a reservation."""
    # Verify reservation belongs to user
    reservation_service = ReservationService(db)
    reservation = await reservation_service.get_reservation_by_id(reservation_id)
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )
    
    if reservation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this reservation",
        )
    
    payment_service = PaymentService(db)
    payment = await payment_service.upload_payment_proof(reservation_id, proof_data.proof_url)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    return PaymentResponse.model_validate(payment)
