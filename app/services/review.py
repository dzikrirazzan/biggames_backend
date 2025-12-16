"""Review service."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.review import ReviewCreate, ReviewResponse


class ReviewService:
    """Service for review operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_review(
        self,
        user_id: UUID,
        review_data: ReviewCreate,
    ) -> ReviewResponse:
        """Create a new review."""
        # Verify reservation exists and belongs to user
        reservation_query = select(Reservation).where(
            Reservation.id == review_data.reservation_id,
            Reservation.user_id == user_id,
        )
        result = await self.db.execute(reservation_query)
        reservation = result.scalar_one_or_none()
        
        if not reservation:
            raise ValueError("Reservation not found or does not belong to user")
        
        if reservation.status not in [ReservationStatus.COMPLETED, ReservationStatus.CONFIRMED]:
            raise ValueError("Can only review completed or confirmed reservations")
        
        # Check if already reviewed
        existing_query = select(Review).where(
            Review.reservation_id == review_data.reservation_id
        )
        existing_result = await self.db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise ValueError("Reservation already reviewed")
        
        # Create review
        review = Review(
            user_id=user_id,
            room_id=reservation.room_id,
            reservation_id=review_data.reservation_id,
            rating=review_data.rating,
            comment=review_data.comment,
        )
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        
        return ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            room_id=review.room_id,
            reservation_id=review.reservation_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
        )
    
    async def get_room_reviews(self, room_id: UUID) -> list[ReviewResponse]:
        """Get reviews for a room."""
        query = select(Review).where(
            Review.room_id == room_id
        ).options(
            selectinload(Review.user),
        ).order_by(Review.created_at.desc())
        
        result = await self.db.execute(query)
        reviews = result.scalars().all()
        
        return [
            ReviewResponse(
                id=r.id,
                user_id=r.user_id,
                user_name=r.user.name if r.user else None,
                room_id=r.room_id,
                reservation_id=r.reservation_id,
                rating=r.rating,
                comment=r.comment,
                created_at=r.created_at,
            )
            for r in reviews
        ]
