"""Promo service."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promo import Promo, DiscountType
from app.schemas.promo import PromoCreate, PromoValidateRequest, PromoValidateResponse


class PromoService:
    """Service for promo operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def validate_promo(self, request: PromoValidateRequest) -> PromoValidateResponse:
        """Validate a promo code and calculate discount."""
        now = datetime.now(timezone.utc)
        
        query = select(Promo).where(
            and_(
                Promo.code == request.code.upper(),
                Promo.is_active == True,
                Promo.start_date <= now,
                Promo.end_date >= now,
            )
        )
        result = await self.db.execute(query)
        promo = result.scalar_one_or_none()
        
        if not promo:
            return PromoValidateResponse(
                valid=False,
                code=request.code,
                message="Promo code is invalid or expired",
            )
        
        # Calculate discount
        if promo.discount_type == DiscountType.PERCENT:
            discount_amount = request.subtotal * (promo.discount_value / Decimal("100"))
        else:
            discount_amount = min(promo.discount_value, request.subtotal)
        
        return PromoValidateResponse(
            valid=True,
            code=promo.code,
            discount_type=promo.discount_type,
            discount_value=promo.discount_value,
            discount_amount=discount_amount,
            message=f"Promo applied: {promo.discount_value}{'%' if promo.discount_type == DiscountType.PERCENT else ' IDR'} off",
        )
    
    async def get_promo_by_code(self, code: str) -> Promo | None:
        """Get promo by code."""
        now = datetime.now(timezone.utc)
        
        query = select(Promo).where(
            and_(
                Promo.code == code.upper(),
                Promo.is_active == True,
                Promo.start_date <= now,
                Promo.end_date >= now,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_promo(self, promo_data: PromoCreate) -> Promo:
        """Create a new promo."""
        promo = Promo(
            **promo_data.model_dump(),
            code=promo_data.code.upper(),
        )
        self.db.add(promo)
        await self.db.flush()
        await self.db.refresh(promo)
        return promo
