"""Database models."""
from app.models.user import User, UserRole
from app.models.room import Room, RoomCategory, RoomStatus, RoomImage, Unit, ConsoleType, UnitStatus
from app.models.addon import Addon, AddonPriceType
from app.models.promo import Promo, DiscountType
from app.models.reservation import Reservation, ReservationStatus, ReservationAddon
from app.models.review import Review
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.menu import MenuItem, MenuCategory
from app.models.fb_order import FbOrder, FbOrderStatus, FbOrderItem
from app.models.ai import UserEvent, EventType, RoomEmbedding

__all__ = [
    "User", "UserRole",
    "Room", "RoomCategory", "RoomStatus", "RoomImage", "Unit", "ConsoleType", "UnitStatus",
    "Addon", "AddonPriceType",
    "Promo", "DiscountType",
    "Reservation", "ReservationStatus", "ReservationAddon",
    "Review",
    "Payment", "PaymentMethod", "PaymentStatus",
    "MenuItem", "MenuCategory",
    "FbOrder", "FbOrderStatus", "FbOrderItem",
    "UserEvent", "EventType", "RoomEmbedding",
]
