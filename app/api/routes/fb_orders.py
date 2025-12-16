"""F&B order routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.fb_order import FbOrderCreate, FbOrderResponse
from app.services.fb_order import FbOrderService
from app.api.deps import get_current_user


router = APIRouter(prefix="/fb", tags=["F&B Orders"])


@router.post("/orders", response_model=FbOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_fb_order(
    order_data: FbOrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new F&B order."""
    fb_order_service = FbOrderService(db)
    try:
        return await fb_order_service.create_order(
            user_id=current_user.id,
            order_data=order_data,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/orders/me", response_model=list[FbOrderResponse])
async def get_my_fb_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's F&B orders."""
    fb_order_service = FbOrderService(db)
    return await fb_order_service.get_user_orders(current_user.id)
