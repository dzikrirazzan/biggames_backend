"""Payment service."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.payment import Payment, PaymentStatus
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.payment import PaymentResponse, PaymentInstructionsResponse


class PaymentService:
    """Service for payment operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_payment_instructions(self, reservation_id: UUID) -> PaymentInstructionsResponse | None:
        """Get payment instructions for a reservation."""
        query = select(Payment).where(Payment.reservation_id == reservation_id)
        result = await self.db.execute(query)
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        return PaymentInstructionsResponse(
            reservation_id=payment.reservation_id,
            amount=payment.amount,
            method=payment.method,
            qris_image_url=settings.QRIS_IMAGE_URL,
            bank_name=settings.BANK_NAME,
            bank_account_number=settings.BANK_ACCOUNT_NUMBER,
            bank_account_name=settings.BANK_ACCOUNT_NAME,
            reference=payment.reference,
            status=payment.status,
        )
    
    async def upload_payment_proof(
        self,
        reservation_id: UUID,
        proof_url: str,
    ) -> Payment | None:
        """Upload payment proof."""
        query = select(Payment).where(Payment.reservation_id == reservation_id)
        result = await self.db.execute(query)
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        payment.proof_url = proof_url
        await self.db.flush()
        
        # Re-query with eager loading to avoid lazy loading issues
        query = select(Payment).where(Payment.id == payment.id).options(
            selectinload(Payment.reservation)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all_payments(self) -> list[PaymentResponse]:
        """Get all payments (admin)."""
        query = select(Payment).order_by(Payment.created_at.desc())
        result = await self.db.execute(query)
        payments = result.scalars().all()
        
        return [PaymentResponse.model_validate(p) for p in payments]
    
    async def get_payment_by_id(self, payment_id: UUID) -> Payment | None:
        """Get payment by ID."""
        query = select(Payment).where(Payment.id == payment_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def confirm_payment(
        self,
        payment_id: UUID,
        admin_id: UUID,
        reference: str | None = None,
    ) -> Payment | None:
        """Confirm a payment and update reservation status."""
        payment = await self.get_payment_by_id(payment_id)
        if not payment:
            return None
        
        # Update payment
        payment.status = PaymentStatus.PAID
        payment.confirmed_at = datetime.now(timezone.utc)
        payment.confirmed_by_admin_id = admin_id
        if reference:
            payment.reference = reference
        
        # Update reservation status
        reservation_query = select(Reservation).where(
            Reservation.id == payment.reservation_id
        )
        result = await self.db.execute(reservation_query)
        reservation = result.scalar_one_or_none()
        
        if reservation:
            reservation.status = ReservationStatus.CONFIRMED
        
        await self.db.flush()
        
        # Re-query with eager loading to avoid lazy loading issues
        query = select(Payment).where(Payment.id == payment_id).options(
            selectinload(Payment.reservation)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def reject_payment(
        self,
        payment_id: UUID,
        admin_id: UUID,
    ) -> Payment | None:
        """Reject a payment."""
        payment = await self.get_payment_by_id(payment_id)
        if not payment:
            return None
        
        # Update payment
        payment.status = PaymentStatus.REJECTED
        payment.confirmed_at = datetime.now(timezone.utc)
        payment.confirmed_by_admin_id = admin_id
        
        # Update reservation status to cancelled
        reservation_query = select(Reservation).where(
            Reservation.id == payment.reservation_id
        )
        result = await self.db.execute(reservation_query)
        reservation = result.scalar_one_or_none()
        
        if reservation:
            reservation.status = ReservationStatus.CANCELLED
        
        await self.db.flush()
        
        # Re-query with eager loading to avoid lazy loading issues
        query = select(Payment).where(Payment.id == payment_id).options(
            selectinload(Payment.reservation)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
