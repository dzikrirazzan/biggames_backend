"""F&B order routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.fb_order import FbOrderStatus
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


@router.post("/orders/{order_id}/cancel", response_model=FbOrderResponse)
async def cancel_fb_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an F&B order (user can cancel their own order)."""
    fb_order_service = FbOrderService(db)
    
    # Get the order
    order = await fb_order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    
    # Check ownership
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own orders",
        )
    
    # Check if order can be cancelled
    if order.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status {order.status}",
        )
    
    # Cancel the order
    try:
        cancelled_order = await fb_order_service.cancel_order(order_id)
        return fb_order_service._order_to_response(cancelled_order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fb_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an F&B order (user can delete their own order)."""
    fb_order_service = FbOrderService(db)
    
    # Get the order
    order = await fb_order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    
    # Check ownership
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own orders",
        )
    
    # Delete the order
    try:
        await fb_order_service.delete_order(order_id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
