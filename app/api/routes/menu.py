"""Menu routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.menu import MenuCategory
from app.schemas.menu import MenuItemResponse
from app.services.menu import MenuService


router = APIRouter(prefix="/menu-items", tags=["Menu"])


@router.get("", response_model=list[MenuItemResponse])
async def get_menu_items(
    category: MenuCategory | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get menu items with optional category filter."""
    menu_service = MenuService(db)
    return await menu_service.get_menu_items(category=category)
