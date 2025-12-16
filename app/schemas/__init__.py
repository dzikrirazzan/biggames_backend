"""Pydantic schemas."""
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest
)
from app.schemas.room import (
    RoomCreate, RoomUpdate, RoomResponse, RoomListResponse, RoomAvailabilityResponse,
    UnitCreate, UnitResponse, RoomImageResponse
)
from app.schemas.addon import AddonCreate, AddonResponse
from app.schemas.promo import PromoCreate, PromoValidateRequest, PromoValidateResponse
from app.schemas.reservation import (
    ReservationCreate, ReservationResponse, ReservationStatusUpdate,
    ReservationAddonCreate, ReservationAddonResponse
)
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.payment import (
    PaymentResponse, PaymentInstructionsResponse, PaymentProofUpload,
    PaymentConfirmRequest
)
from app.schemas.menu import MenuItemCreate, MenuItemResponse
from app.schemas.fb_order import (
    FbOrderCreate, FbOrderResponse, FbOrderItemCreate, FbOrderItemResponse,
    FbOrderStatusUpdate
)
from app.schemas.ai import (
    UserEventCreate, RecommendationResponse, RecommendedRoom
)

__all__ = [
    # User
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse", "RefreshTokenRequest",
    # Room
    "RoomCreate", "RoomUpdate", "RoomResponse", "RoomListResponse", "RoomAvailabilityResponse",
    "UnitCreate", "UnitResponse", "RoomImageResponse",
    # Addon
    "AddonCreate", "AddonResponse",
    # Promo
    "PromoCreate", "PromoValidateRequest", "PromoValidateResponse",
    # Reservation
    "ReservationCreate", "ReservationResponse", "ReservationStatusUpdate",
    "ReservationAddonCreate", "ReservationAddonResponse",
    # Review
    "ReviewCreate", "ReviewResponse",
    # Payment
    "PaymentResponse", "PaymentInstructionsResponse", "PaymentProofUpload",
    "PaymentConfirmRequest",
    # Menu
    "MenuItemCreate", "MenuItemResponse",
    # F&B Order
    "FbOrderCreate", "FbOrderResponse", "FbOrderItemCreate", "FbOrderItemResponse",
    "FbOrderStatusUpdate",
    # AI
    "UserEventCreate", "RecommendationResponse", "RecommendedRoom",
]
