"""Reservation service."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reservation import Reservation, ReservationStatus, ReservationAddon
from app.models.room import Room, RoomStatus
from app.models.addon import Addon, AddonPriceType
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.promo import Promo, DiscountType
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationResponse, ReservationAddonResponse
from app.services.room import RoomService
from app.services.promo import PromoService


class ReservationService:
    """Service for reservation operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.room_service = RoomService(db)
        self.promo_service = PromoService(db)
    
    async def create_reservation(
        self,
        user_id: UUID,
        reservation_data: ReservationCreate,
    ) -> ReservationResponse:
        """Create a new reservation with payment."""
        # Check room exists and is active
        room = await self.room_service.get_room_entity(reservation_data.room_id)
        if not room:
            raise ValueError("Room not found")
        if room.status != RoomStatus.ACTIVE:
            raise ValueError("Room is not available")
        
        # Check availability
        availability = await self.room_service.check_availability(
            reservation_data.room_id,
            reservation_data.start_time,
            reservation_data.end_time,
        )
        if not availability.is_available:
            raise ValueError("Room is not available for the selected time slot")
        
        # Calculate duration
        duration_delta = reservation_data.end_time - reservation_data.start_time
        duration_hours = Decimal(str(duration_delta.total_seconds() / 3600))
        
        if duration_hours <= 0:
            raise ValueError("End time must be after start time")
        
        # Calculate base subtotal
        subtotal = room.base_price_per_hour * duration_hours
        
        # Process addons
        addon_records = []
        for addon_item in reservation_data.addons:
            addon = await self._get_addon(addon_item.addon_id)
            if not addon or not addon.is_active:
                raise ValueError(f"Addon {addon_item.addon_id} not found or inactive")
            
            if addon.price_type == AddonPriceType.PER_HOUR:
                addon_price = addon.price_amount * duration_hours
            else:
                addon_price = addon.price_amount
            
            addon_subtotal = addon_price * addon_item.qty
            subtotal += addon_subtotal
            
            addon_records.append({
                "addon_id": addon.id,
                "addon_name": addon.name,
                "qty": addon_item.qty,
                "price": addon_price,
                "subtotal": addon_subtotal,
            })
        
        # Apply promo if provided
        discount_amount = Decimal("0")
        if reservation_data.promo_code:
            promo = await self.promo_service.get_promo_by_code(reservation_data.promo_code)
            if promo:
                if promo.discount_type == DiscountType.PERCENT:
                    discount_amount = subtotal * (promo.discount_value / Decimal("100"))
                else:
                    discount_amount = min(promo.discount_value, subtotal)
        
        # Calculate total
        total_amount = subtotal - discount_amount
        
        # Create reservation
        reservation = Reservation(
            user_id=user_id,
            room_id=reservation_data.room_id,
            start_time=reservation_data.start_time,
            end_time=reservation_data.end_time,
            duration_hours=duration_hours,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
            status=ReservationStatus.PENDING_PAYMENT,
            notes=reservation_data.notes,
        )
        self.db.add(reservation)
        await self.db.flush()
        
        # Create reservation addons
        for addon_data in addon_records:
            reservation_addon = ReservationAddon(
                reservation_id=reservation.id,
                addon_id=addon_data["addon_id"],
                qty=addon_data["qty"],
                price=addon_data["price"],
                subtotal=addon_data["subtotal"],
            )
            self.db.add(reservation_addon)
        
        # Create payment record
        payment = Payment(
            reservation_id=reservation.id,
            method=reservation_data.payment_method,
            status=PaymentStatus.WAITING_CONFIRMATION,
            amount=total_amount,
            reference=f"BG-{reservation.id.hex[:8].upper()}",
        )
        self.db.add(payment)
        
        await self.db.flush()
        await self.db.refresh(reservation)
        
        # Build response
        addon_responses = [
            ReservationAddonResponse(
                id=reservation.addons[i].id if i < len(reservation.addons) else None,
                addon_id=addon_data["addon_id"],
                addon_name=addon_data["addon_name"],
                qty=addon_data["qty"],
                price=addon_data["price"],
                subtotal=addon_data["subtotal"],
            )
            for i, addon_data in enumerate(addon_records)
        ]
        
        return ReservationResponse(
            id=reservation.id,
            user_id=reservation.user_id,
            room_id=reservation.room_id,
            room_name=room.name,
            start_time=reservation.start_time,
            end_time=reservation.end_time,
            duration_hours=reservation.duration_hours,
            subtotal=reservation.subtotal,
            discount_amount=reservation.discount_amount,
            total_amount=reservation.total_amount,
            status=reservation.status,
            notes=reservation.notes,
            created_at=reservation.created_at,
            addons=addon_responses,
            payment_status=payment.status.value,
            payment_method=payment.method.value,
        )
    
    async def get_user_reservations(self, user_id: UUID) -> list[ReservationResponse]:
        """Get reservations for a user."""
        query = select(Reservation).where(
            Reservation.user_id == user_id
        ).options(
            selectinload(Reservation.room),
            selectinload(Reservation.user),
            selectinload(Reservation.addons).selectinload(ReservationAddon.addon),
            selectinload(Reservation.payment),
        ).order_by(Reservation.created_at.desc())
        
        result = await self.db.execute(query)
        reservations = result.scalars().all()
        
        return [await self._reservation_to_response(r) for r in reservations]
    
    async def get_all_reservations(self) -> list[ReservationResponse]:
        """Get all reservations (admin)."""
        query = select(Reservation).options(
            selectinload(Reservation.room),
            selectinload(Reservation.user),
            selectinload(Reservation.addons).selectinload(ReservationAddon.addon),
            selectinload(Reservation.payment),
        ).order_by(Reservation.created_at.desc())
        
        result = await self.db.execute(query)
        reservations = result.scalars().all()
        
        return [await self._reservation_to_response(r) for r in reservations]
    
    async def get_reservation_by_id(self, reservation_id: UUID) -> Reservation | None:
        """Get reservation by ID."""
        query = select(Reservation).where(
            Reservation.id == reservation_id
        ).options(
            selectinload(Reservation.room),
            selectinload(Reservation.user),
            selectinload(Reservation.addons).selectinload(ReservationAddon.addon),
            selectinload(Reservation.payment),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_reservation_status(
        self,
        reservation_id: UUID,
        status: ReservationStatus,
    ) -> Reservation | None:
        """Update reservation status."""
        reservation = await self.get_reservation_by_id(reservation_id)
        if not reservation:
            return None
        
        reservation.status = status
        await self.db.flush()
        await self.db.refresh(reservation)
        return reservation
    
    async def _get_addon(self, addon_id: UUID) -> Addon | None:
        """Get addon by ID."""
        query = select(Addon).where(Addon.id == addon_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _reservation_to_response(self, reservation: Reservation) -> ReservationResponse:
        """Convert reservation entity to response."""
        addon_responses = [
            ReservationAddonResponse(
                id=ra.id,
                addon_id=ra.addon_id,
                addon_name=ra.addon.name if ra.addon else None,
                qty=ra.qty,
                price=ra.price,
                subtotal=ra.subtotal,
            )
            for ra in reservation.addons
        ]
        
        return ReservationResponse(
            id=reservation.id,
            user_id=reservation.user_id,
            user_name=reservation.user.name if reservation.user else None,
            user_email=reservation.user.email if reservation.user else None,
            room_id=reservation.room_id,
            room_name=reservation.room.name if reservation.room else None,
            start_time=reservation.start_time,
            end_time=reservation.end_time,
            duration_hours=reservation.duration_hours,
            subtotal=reservation.subtotal,
            discount_amount=reservation.discount_amount,
            total_amount=reservation.total_amount,
            status=reservation.status,
            notes=reservation.notes,
            created_at=reservation.created_at,
            addons=addon_responses,
            payment_status=reservation.payment.status.value if reservation.payment else None,
            payment_method=reservation.payment.method.value if reservation.payment else None,
        )
