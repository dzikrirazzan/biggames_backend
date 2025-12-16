# API routes
from app.api.routes.auth import router as auth_router
from app.api.routes.rooms import router as rooms_router
from app.api.routes.reservations import router as reservations_router
from app.api.routes.promo import router as promo_router
from app.api.routes.payment import router as payment_router
from app.api.routes.menu import router as menu_router
from app.api.routes.fb_orders import router as fb_orders_router
from app.api.routes.ai import router as ai_router
from app.api.routes.admin import router as admin_router

__all__ = [
    "auth_router",
    "rooms_router",
    "reservations_router",
    "promo_router",
    "payment_router",
    "menu_router",
    "fb_orders_router",
    "ai_router",
    "admin_router",
]