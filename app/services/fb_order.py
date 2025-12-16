"""F&B order service."""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fb_order import FbOrder, FbOrderStatus, FbOrderItem
from app.models.menu import MenuItem
from app.models.reservation import Reservation
from app.schemas.fb_order import (
    FbOrderCreate, FbOrderResponse, FbOrderItemResponse, FbOrderStatusUpdate
)


class FbOrderService:
    """Service for F&B order operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_order(
        self,
        user_id: UUID,
        order_data: FbOrderCreate,
    ) -> FbOrderResponse:
        """Create a new F&B order."""
        room_id = order_data.room_id
        
        # If reservation_id provided, derive room_id from it
        if order_data.reservation_id:
            reservation_query = select(Reservation).where(
                Reservation.id == order_data.reservation_id
            )
            result = await self.db.execute(reservation_query)
            reservation = result.scalar_one_or_none()
            
            if reservation:
                room_id = reservation.room_id
        
        # Calculate totals
        subtotal = Decimal("0")
        item_records = []
        
        for item_data in order_data.items:
            menu_item = await self._get_menu_item(item_data.menu_item_id)
            if not menu_item:
                raise ValueError(f"Menu item {item_data.menu_item_id} not found")
            if not menu_item.is_active:
                raise ValueError(f"Menu item {menu_item.name} is not available")
            if menu_item.stock < item_data.qty:
                raise ValueError(f"Insufficient stock for {menu_item.name}")
            
            item_subtotal = menu_item.price * item_data.qty
            subtotal += item_subtotal
            
            item_records.append({
                "menu_item_id": menu_item.id,
                "menu_item_name": menu_item.name,
                "qty": item_data.qty,
                "price": menu_item.price,
                "subtotal": item_subtotal,
            })
            
            # Reduce stock
            menu_item.stock -= item_data.qty
        
        # Calculate delivery fee (could be based on room distance, etc.)
        delivery_fee = Decimal("0")
        if room_id:
            delivery_fee = Decimal("2000")  # Flat delivery fee for room orders
        
        total_amount = subtotal + delivery_fee
        
        # Create order
        order = FbOrder(
            user_id=user_id,
            reservation_id=order_data.reservation_id,
            room_id=room_id,
            status=FbOrderStatus.PENDING,
            notes=order_data.notes,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
        )
        self.db.add(order)
        await self.db.flush()
        
        # Create order items
        for item_data in item_records:
            order_item = FbOrderItem(
                order_id=order.id,
                menu_item_id=item_data["menu_item_id"],
                qty=item_data["qty"],
                price=item_data["price"],
                subtotal=item_data["subtotal"],
            )
            self.db.add(order_item)
        
        await self.db.flush()
        await self.db.refresh(order)
        
        # Build response
        item_responses = [
            FbOrderItemResponse(
                id=order.items[i].id if i < len(order.items) else None,
                menu_item_id=item_data["menu_item_id"],
                menu_item_name=item_data["menu_item_name"],
                qty=item_data["qty"],
                price=item_data["price"],
                subtotal=item_data["subtotal"],
            )
            for i, item_data in enumerate(item_records)
        ]
        
        return FbOrderResponse(
            id=order.id,
            user_id=order.user_id,
            reservation_id=order.reservation_id,
            room_id=order.room_id,
            room_name=None,
            status=order.status,
            notes=order.notes,
            subtotal=order.subtotal,
            delivery_fee=order.delivery_fee,
            total_amount=order.total_amount,
            created_at=order.created_at,
            items=item_responses,
        )
    
    async def get_user_orders(self, user_id: UUID) -> list[FbOrderResponse]:
        """Get orders for a user."""
        query = select(FbOrder).where(
            FbOrder.user_id == user_id
        ).options(
            selectinload(FbOrder.items).selectinload(FbOrderItem.menu_item),
            selectinload(FbOrder.room),
        ).order_by(FbOrder.created_at.desc())
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        return [self._order_to_response(o) for o in orders]
    
    async def get_all_orders(self) -> list[FbOrderResponse]:
        """Get all orders (admin)."""
        query = select(FbOrder).options(
            selectinload(FbOrder.items).selectinload(FbOrderItem.menu_item),
            selectinload(FbOrder.room),
        ).order_by(FbOrder.created_at.desc())
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        return [self._order_to_response(o) for o in orders]
    
    async def get_order_by_id(self, order_id: UUID) -> FbOrder | None:
        """Get order by ID."""
        query = select(FbOrder).where(
            FbOrder.id == order_id
        ).options(
            selectinload(FbOrder.items).selectinload(FbOrderItem.menu_item),
            selectinload(FbOrder.room),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_order_status(
        self,
        order_id: UUID,
        status: FbOrderStatus,
    ) -> FbOrder | None:
        """Update order status."""
        order = await self.get_order_by_id(order_id)
        if not order:
            return None
        
        order.status = status
        await self.db.flush()
        await self.db.refresh(order)
        return order
    
    async def _get_menu_item(self, item_id: UUID) -> MenuItem | None:
        """Get menu item by ID."""
        query = select(MenuItem).where(MenuItem.id == item_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    def _order_to_response(self, order: FbOrder) -> FbOrderResponse:
        """Convert order entity to response."""
        item_responses = [
            FbOrderItemResponse(
                id=item.id,
                menu_item_id=item.menu_item_id,
                menu_item_name=item.menu_item.name if item.menu_item else None,
                qty=item.qty,
                price=item.price,
                subtotal=item.subtotal,
            )
            for item in order.items
        ]
        
        return FbOrderResponse(
            id=order.id,
            user_id=order.user_id,
            reservation_id=order.reservation_id,
            room_id=order.room_id,
            room_name=order.room.name if order.room else None,
            status=order.status,
            notes=order.notes,
            subtotal=order.subtotal,
            delivery_fee=order.delivery_fee,
            total_amount=order.total_amount,
            created_at=order.created_at,
            items=item_responses,
        )
