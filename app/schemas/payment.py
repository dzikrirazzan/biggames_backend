"""Payment schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: UUID
    reservation_id: UUID
    method: PaymentMethod
    status: PaymentStatus
    amount: Decimal
    proof_url: str | None
    reference: str | None
    created_at: datetime
    confirmed_at: datetime | None
    confirmed_by_admin_id: UUID | None

    class Config:
        from_attributes = True


class PaymentInstructionsResponse(BaseModel):
    """Schema for payment instructions response."""
    reservation_id: UUID
    amount: Decimal
    method: PaymentMethod
    qris_image_url: str | None = None
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_account_name: str | None = None
    reference: str | None = None
    status: PaymentStatus


class PaymentProofUpload(BaseModel):
    """Schema for uploading payment proof."""
    proof_url: str


class PaymentConfirmRequest(BaseModel):
    """Schema for confirming/rejecting payment."""
    reference: str | None = None
