"""Tests for manual payment confirmation flow."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.room import Room, RoomCategory, RoomStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.core.security import get_password_hash
from app.services.payment import PaymentService


@pytest_asyncio.fixture
async def pending_reservation_with_payment(db_session: AsyncSession):
    """Create a pending reservation with payment awaiting confirmation."""
    # Create user
    user = User(
        id=uuid4(),
        email="payer@example.com",
        name="Payer User",
        password_hash=get_password_hash("pass123"),
        role=UserRole.USER,
    )
    db_session.add(user)
    
    # Create admin
    admin = User(
        id=uuid4(),
        email="admin@example.com",
        name="Admin User",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    
    # Create room
    room = Room(
        id=uuid4(),
        name="Payment Test Room",
        category=RoomCategory.VIP,
        capacity=4,
        base_price_per_hour=Decimal("30000"),
        status=RoomStatus.ACTIVE,
    )
    db_session.add(room)
    await db_session.flush()
    
    # Create reservation
    now = datetime.now(timezone.utc)
    reservation = Reservation(
        id=uuid4(),
        user_id=user.id,
        room_id=room.id,
        start_time=now + timedelta(hours=2),
        end_time=now + timedelta(hours=4),
        duration_hours=Decimal("2"),
        subtotal=Decimal("60000"),
        discount_amount=Decimal("0"),
        total_amount=Decimal("60000"),
        status=ReservationStatus.PENDING_PAYMENT,
    )
    db_session.add(reservation)
    await db_session.flush()
    
    # Create payment
    payment = Payment(
        id=uuid4(),
        reservation_id=reservation.id,
        method=PaymentMethod.QRIS,
        status=PaymentStatus.WAITING_CONFIRMATION,
        amount=Decimal("60000"),
        reference=f"BG-{reservation.id.hex[:8].upper()}",
    )
    db_session.add(payment)
    await db_session.commit()
    
    await db_session.refresh(user)
    await db_session.refresh(admin)
    await db_session.refresh(room)
    await db_session.refresh(reservation)
    await db_session.refresh(payment)
    
    return user, admin, room, reservation, payment


class TestPaymentConfirmation:
    """Tests for payment confirmation flow."""
    
    @pytest.mark.asyncio
    async def test_confirm_payment_updates_payment_status(
        self,
        db_session: AsyncSession,
        pending_reservation_with_payment,
    ):
        """Test that confirming payment updates payment status to PAID."""
        _, admin, _, _, payment = pending_reservation_with_payment
        
        payment_service = PaymentService(db_session)
        confirmed_payment = await payment_service.confirm_payment(
            payment.id, admin.id, reference="CONFIRMED-REF"
        )
        
        assert confirmed_payment is not None
        assert confirmed_payment.status == PaymentStatus.PAID
        assert confirmed_payment.confirmed_at is not None
        assert confirmed_payment.confirmed_by_admin_id == admin.id
        assert confirmed_payment.reference == "CONFIRMED-REF"
    
    @pytest.mark.asyncio
    async def test_confirm_payment_updates_reservation_status(
        self,
        db_session: AsyncSession,
        pending_reservation_with_payment,
    ):
        """Test that confirming payment updates reservation status to CONFIRMED."""
        _, admin, _, reservation, payment = pending_reservation_with_payment
        
        payment_service = PaymentService(db_session)
        await payment_service.confirm_payment(payment.id, admin.id)
        
        # Refresh reservation to get updated status
        await db_session.refresh(reservation)
        
        assert reservation.status == ReservationStatus.CONFIRMED
    
    @pytest.mark.asyncio
    async def test_reject_payment_updates_payment_status(
        self,
        db_session: AsyncSession,
        pending_reservation_with_payment,
    ):
        """Test that rejecting payment updates payment status to REJECTED."""
        _, admin, _, _, payment = pending_reservation_with_payment
        
        payment_service = PaymentService(db_session)
        rejected_payment = await payment_service.reject_payment(payment.id, admin.id)
        
        assert rejected_payment is not None
        assert rejected_payment.status == PaymentStatus.REJECTED
        assert rejected_payment.confirmed_at is not None
        assert rejected_payment.confirmed_by_admin_id == admin.id
    
    @pytest.mark.asyncio
    async def test_reject_payment_cancels_reservation(
        self,
        db_session: AsyncSession,
        pending_reservation_with_payment,
    ):
        """Test that rejecting payment cancels the reservation."""
        _, admin, _, reservation, payment = pending_reservation_with_payment
        
        payment_service = PaymentService(db_session)
        await payment_service.reject_payment(payment.id, admin.id)
        
        # Refresh reservation to get updated status
        await db_session.refresh(reservation)
        
        assert reservation.status == ReservationStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_confirm_nonexistent_payment_returns_none(
        self,
        db_session: AsyncSession,
        pending_reservation_with_payment,
    ):
        """Test that confirming a non-existent payment returns None."""
        _, admin, _, _, _ = pending_reservation_with_payment
        
        payment_service = PaymentService(db_session)
        result = await payment_service.confirm_payment(uuid4(), admin.id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_upload_payment_proof(
        self,
        db_session: AsyncSession,
        pending_reservation_with_payment,
    ):
        """Test uploading payment proof."""
        _, _, _, reservation, payment = pending_reservation_with_payment
        
        proof_url = "https://example.com/proof/12345.jpg"
        
        payment_service = PaymentService(db_session)
        updated_payment = await payment_service.upload_payment_proof(
            reservation.id, proof_url
        )
        
        assert updated_payment is not None
        assert updated_payment.proof_url == proof_url
        # Status should still be waiting
        assert updated_payment.status == PaymentStatus.WAITING_CONFIRMATION
    
    @pytest.mark.asyncio
    async def test_get_payment_instructions(
        self,
        db_session: AsyncSession,
        pending_reservation_with_payment,
    ):
        """Test getting payment instructions."""
        _, _, _, reservation, _ = pending_reservation_with_payment
        
        payment_service = PaymentService(db_session)
        instructions = await payment_service.get_payment_instructions(reservation.id)
        
        assert instructions is not None
        assert instructions.reservation_id == reservation.id
        assert instructions.amount == Decimal("60000")
        assert instructions.method == PaymentMethod.QRIS
        assert instructions.status == PaymentStatus.WAITING_CONFIRMATION
        assert instructions.qris_image_url is not None
        assert instructions.bank_name is not None
        assert instructions.bank_account_number is not None
