"""Menu service."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu import MenuItem, MenuCategory
from app.schemas.menu import MenuItemCreate, MenuItemResponse


class MenuService:
    """Service for menu operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_menu_items(
        self,
        category: MenuCategory | None = None,
        active_only: bool = True,
    ) -> list[MenuItemResponse]:
        """Get menu items with optional filters."""
        query = select(MenuItem)
        
        if category:
            query = query.where(MenuItem.category == category)
        if active_only:
            query = query.where(MenuItem.is_active == True)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return [MenuItemResponse.model_validate(item) for item in items]
    
    async def get_menu_item_by_id(self, item_id: UUID) -> MenuItem | None:
        """Get menu item by ID."""
        query = select(MenuItem).where(MenuItem.id == item_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_menu_item(self, item_data: MenuItemCreate) -> MenuItem:
        """Create a new menu item."""
        item = MenuItem(**item_data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item
    
    async def update_stock(self, item_id: UUID, quantity_change: int) -> MenuItem | None:
        """Update menu item stock."""
        item = await self.get_menu_item_by_id(item_id)
        if not item:
            return None
        
        new_stock = item.stock + quantity_change
        if new_stock < 0:
            raise ValueError("Insufficient stock")
        
        item.stock = new_stock
        await self.db.flush()
        await self.db.refresh(item)
        return item
