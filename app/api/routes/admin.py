"""Admin routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.reservation import ReservationResponse, ReservationStatusUpdate
from app.schemas.payment import PaymentResponse, PaymentConfirmRequest
from app.schemas.fb_order import FbOrderResponse, FbOrderStatusUpdate
from app.services.reservation import ReservationService
from app.services.payment import PaymentService
from app.services.fb_order import FbOrderService
from app.services.ai import AIService
from app.api.deps import get_admin_user, get_finance_user


router = APIRouter(prefix="/admin", tags=["Admin"])


# ============== Reservations ==============

@router.get("/reservations", response_model=list[ReservationResponse])
async def get_all_reservations(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all reservations (admin only)."""
    reservation_service = ReservationService(db)
    return await reservation_service.get_all_reservations()


@router.put("/reservations/{reservation_id}/status", response_model=ReservationResponse)
async def update_reservation_status(
    reservation_id: UUID,
    status_update: ReservationStatusUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update reservation status (admin only)."""
    reservation_service = ReservationService(db)
    reservation = await reservation_service.update_reservation_status(
        reservation_id, status_update.status
    )
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )
    
    return await reservation_service._reservation_to_response(reservation)


# ============== Payments ==============

@router.get("/payments", response_model=list[PaymentResponse])
async def get_all_payments(
    admin_user: User = Depends(get_finance_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all payments (admin/finance only)."""
    payment_service = PaymentService(db)
    return await payment_service.get_all_payments()


@router.put("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: UUID,
    request: PaymentConfirmRequest | None = None,
    admin_user: User = Depends(get_finance_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a payment (admin/finance only)."""
    payment_service = PaymentService(db)
    payment = await payment_service.confirm_payment(
        payment_id,
        admin_user.id,
        reference=request.reference if request else None,
    )
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    return PaymentResponse.model_validate(payment)


@router.put("/payments/{payment_id}/reject", response_model=PaymentResponse)
async def reject_payment(
    payment_id: UUID,
    admin_user: User = Depends(get_finance_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a payment (admin/finance only)."""
    payment_service = PaymentService(db)
    payment = await payment_service.reject_payment(payment_id, admin_user.id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    return PaymentResponse.model_validate(payment)


# ============== F&B Orders ==============

@router.get("/fb/orders", response_model=list[FbOrderResponse])
async def get_all_fb_orders(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all F&B orders (admin only)."""
    fb_order_service = FbOrderService(db)
    return await fb_order_service.get_all_orders()


@router.put("/fb/orders/{order_id}/status", response_model=FbOrderResponse)
async def update_fb_order_status(
    order_id: UUID,
    status_update: FbOrderStatusUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update F&B order status (admin only)."""
    fb_order_service = FbOrderService(db)
    order = await fb_order_service.update_order_status(order_id, status_update.status)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    
    return fb_order_service._order_to_response(order)


# ============== AI Embeddings ==============

@router.post("/rooms/{room_id}/embedding")
async def generate_room_embedding(
    room_id: UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate embedding for a room (admin only)."""
    ai_service = AIService(db)
    try:
        embedding = await ai_service.generate_room_embedding(room_id)
        return {
            "room_id": str(embedding.room_id),
            "updated_at": embedding.updated_at.isoformat(),
            "dimension": len(embedding.embedding),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
