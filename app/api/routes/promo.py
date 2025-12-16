"""Promo routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.promo import PromoValidateRequest, PromoValidateResponse
from app.services.promo import PromoService


router = APIRouter(prefix="/promos", tags=["Promos"])


@router.post("/validate", response_model=PromoValidateResponse)
async def validate_promo(
    request: PromoValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate a promo code and calculate discount."""
    promo_service = PromoService(db)
    return await promo_service.validate_promo(request)
