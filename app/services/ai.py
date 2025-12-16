"""AI recommendation service for rooms."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import numpy as np
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai import UserEvent, EventType, RoomEmbedding
from app.models.room import Room, RoomStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.review import Review
from app.schemas.ai import UserEventCreate, RecommendationResponse, RecommendedRoom
from app.services.embedding import HuggingFaceEmbeddingProvider, get_embedding_provider


# Event weights for user vector calculation
EVENT_WEIGHTS = {
    EventType.VIEW_ROOM: 1.0,
    EventType.CLICK_ROOM: 2.0,
    EventType.BOOK_ROOM: 5.0,
    EventType.RATE_ROOM: 4.0,  # Base, adjusted by rating
}

# Re-ranking weights
WEIGHT_SIMILARITY = 0.65
WEIGHT_RATING = 0.10
WEIGHT_POPULARITY = 0.10
WEIGHT_PRICE_MATCH = 0.10
WEIGHT_FRESHNESS = 0.05

# Cold start threshold
COLD_START_THRESHOLD = 3


class AIService:
    """Service for AI room recommendations."""
    
    def __init__(self, db: AsyncSession, embedding_provider: HuggingFaceEmbeddingProvider | None = None):
        self.db = db
        self.embedding_provider = embedding_provider or get_embedding_provider()
    
    async def log_event(self, user_id: UUID, event_data: UserEventCreate) -> UserEvent:
        """Log a user event."""
        event = UserEvent(
            user_id=user_id,
            room_id=event_data.room_id,
            event_type=event_data.event_type,
            rating_value=event_data.rating_value,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event
    
    async def generate_room_embedding(self, room_id: UUID) -> RoomEmbedding:
        """Generate and store embedding for a room."""
        # Get room with units
        query = select(Room).where(Room.id == room_id).options(
            selectinload(Room.units),
        )
        result = await self.db.execute(query)
        room = result.scalar_one_or_none()
        
        if not room:
            raise ValueError("Room not found")
        
        # Build room profile text
        profile_text = self._build_room_profile(room)
        
        # Get embedding
        embedding_vector = await self.embedding_provider.get_embedding(profile_text)
        
        # Check if embedding exists
        existing_query = select(RoomEmbedding).where(RoomEmbedding.room_id == room_id)
        existing_result = await self.db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            existing.embedding = embedding_vector
            existing.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            room_embedding = RoomEmbedding(
                room_id=room_id,
                embedding=embedding_vector,
            )
            self.db.add(room_embedding)
            await self.db.flush()
            await self.db.refresh(room_embedding)
            return room_embedding
    
    async def get_recommendations(
        self,
        user_id: UUID | None = None,
        limit: int = 8,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> RecommendationResponse:
        """Get room recommendations for a user."""
        # Get user event count
        event_count = 0
        if user_id:
            count_query = select(func.count(UserEvent.id)).where(
                UserEvent.user_id == user_id
            )
            count_result = await self.db.execute(count_query)
            event_count = count_result.scalar() or 0
        
        # Cold start handling
        if not user_id or event_count < COLD_START_THRESHOLD:
            recommendations = await self._get_trending_rooms(limit, start, end)
            return RecommendationResponse(
                recommendations=recommendations,
                is_cold_start=True,
                user_event_count=event_count,
            )
        
        # Get user vector
        user_vector = await self._compute_user_vector(user_id)
        
        if user_vector is None:
            recommendations = await self._get_trending_rooms(limit, start, end)
            return RecommendationResponse(
                recommendations=recommendations,
                is_cold_start=True,
                user_event_count=event_count,
            )
        
        # Get user's recent interactions for explainability
        user_rooms = await self._get_user_interacted_rooms(user_id)
        user_avg_price = await self._get_user_avg_price(user_id)
        
        # Retrieve top-k by similarity
        top_k = 50
        candidate_rooms = await self._get_similar_rooms(user_vector, top_k)
        
        # Filter by availability if time range provided
        if start and end:
            candidate_rooms = await self._filter_available_rooms(candidate_rooms, start, end)
        
        # Get room stats
        room_stats = await self._get_room_stats()
        
        # Re-rank candidates
        scored_rooms = []
        for room, similarity in candidate_rooms:
            final_score = self._compute_final_score(
                room, similarity, room_stats, user_avg_price
            )
            reason = self._generate_explanation(room, user_rooms, similarity)
            
            avg_rating = room_stats.get(room.id, {}).get("avg_rating")
            review_count = room_stats.get(room.id, {}).get("review_count", 0)
            
            scored_rooms.append(RecommendedRoom(
                room_id=room.id,
                name=room.name,
                category=room.category,
                capacity=room.capacity,
                base_price_per_hour=room.base_price_per_hour,
                avg_rating=avg_rating,
                review_count=review_count,
                similarity_score=similarity,
                final_score=final_score,
                reason=reason,
            ))
        
        # Sort by final score and take top limit
        scored_rooms.sort(key=lambda x: x.final_score, reverse=True)
        recommendations = scored_rooms[:limit]
        
        return RecommendationResponse(
            recommendations=recommendations,
            is_cold_start=False,
            user_event_count=event_count,
        )
    
    def _build_room_profile(self, room: Room) -> str:
        """Build text profile for room embedding."""
        parts = [
            f"Room: {room.name}",
            f"Category: {room.category.value}",
            f"Capacity: {room.capacity} people",
            f"Price: {room.base_price_per_hour} IDR per hour",
        ]
        
        if room.description:
            parts.append(f"Description: {room.description}")
        
        if room.units:
            console_types = [u.console_type.value for u in room.units]
            stick_counts = [u.jumlah_stick for u in room.units]
            parts.append(f"Consoles: {', '.join(console_types)}")
            parts.append(f"Controllers: {sum(stick_counts)} total")
        
        return " | ".join(parts)
    
    async def _compute_user_vector(self, user_id: UUID) -> np.ndarray | None:
        """Compute weighted average of room embeddings based on user events."""
        # Get last 50 events
        query = select(UserEvent).where(
            UserEvent.user_id == user_id
        ).order_by(UserEvent.created_at.desc()).limit(50)
        
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        if not events:
            return None
        
        # Get room embeddings for events
        room_ids = list(set(e.room_id for e in events))
        embedding_query = select(RoomEmbedding).where(
            RoomEmbedding.room_id.in_(room_ids)
        )
        embedding_result = await self.db.execute(embedding_query)
        embeddings = {e.room_id: np.array(e.embedding) for e in embedding_result.scalars().all()}
        
        if not embeddings:
            return None
        
        # Compute weighted average
        weighted_sum = np.zeros(self.embedding_provider.dimension)
        total_weight = 0.0
        
        for event in events:
            if event.room_id not in embeddings:
                continue
            
            weight = EVENT_WEIGHTS.get(event.event_type, 1.0)
            
            # Adjust RATE_ROOM weight based on rating
            if event.event_type == EventType.RATE_ROOM and event.rating_value:
                weight = 4.0 + (event.rating_value - 3)  # 2-6 based on 1-5 rating
            
            weighted_sum += weight * embeddings[event.room_id]
            total_weight += weight
        
        if total_weight == 0:
            return None
        
        user_vector = weighted_sum / total_weight
        
        # Normalize
        norm = np.linalg.norm(user_vector)
        if norm > 0:
            user_vector = user_vector / norm
        
        return user_vector
    
    async def _get_similar_rooms(
        self,
        user_vector: np.ndarray,
        top_k: int = 50,
    ) -> list[tuple[Room, float]]:
        """Get top-k similar rooms using pgvector cosine similarity."""
        # Convert user vector to list for query
        vector_list = user_vector.tolist()
        
        # Query using pgvector cosine distance
        # Note: pgvector uses <=> for cosine distance, so similarity = 1 - distance
        query = (
            select(Room, RoomEmbedding)
            .join(RoomEmbedding, Room.id == RoomEmbedding.room_id)
            .where(Room.status == RoomStatus.ACTIVE)
            .order_by(RoomEmbedding.embedding.cosine_distance(vector_list))
            .limit(top_k)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        similar_rooms = []
        for room, embedding in rows:
            # Compute similarity (1 - cosine distance)
            room_vec = np.array(embedding.embedding)
            similarity = float(np.dot(user_vector, room_vec))
            similar_rooms.append((room, similarity))
        
        return similar_rooms
    
    async def _filter_available_rooms(
        self,
        rooms: list[tuple[Room, float]],
        start: datetime,
        end: datetime,
    ) -> list[tuple[Room, float]]:
        """Filter rooms by availability."""
        if not rooms:
            return []
        
        room_ids = [r[0].id for r in rooms]
        
        # Get rooms with conflicting reservations
        conflict_query = select(Reservation.room_id).where(
            and_(
                Reservation.room_id.in_(room_ids),
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.start_time < end,
                Reservation.end_time > start,
            )
        ).distinct()
        
        result = await self.db.execute(conflict_query)
        unavailable_ids = set(result.scalars().all())
        
        return [(room, sim) for room, sim in rooms if room.id not in unavailable_ids]
    
    async def _get_trending_rooms(
        self,
        limit: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[RecommendedRoom]:
        """Get trending rooms for cold start."""
        # Trending = most reserved in last 30 days + highest rating
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Get reservation counts
        reservation_count_query = (
            select(
                Reservation.room_id,
                func.count(Reservation.id).label("reservation_count"),
            )
            .where(
                Reservation.created_at >= thirty_days_ago,
                Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED]),
            )
            .group_by(Reservation.room_id)
        )
        
        res_result = await self.db.execute(reservation_count_query)
        reservation_counts = {row.room_id: row.reservation_count for row in res_result}
        
        # Get room stats
        room_stats = await self._get_room_stats()
        
        # Get active rooms
        room_query = select(Room).where(Room.status == RoomStatus.ACTIVE)
        room_result = await self.db.execute(room_query)
        rooms = list(room_result.scalars().all())
        
        # Filter by availability if needed
        if start and end:
            available_rooms = []
            for room in rooms:
                conflict_query = select(Reservation.id).where(
                    and_(
                        Reservation.room_id == room.id,
                        Reservation.status == ReservationStatus.CONFIRMED,
                        Reservation.start_time < end,
                        Reservation.end_time > start,
                    )
                ).limit(1)
                conflict_result = await self.db.execute(conflict_query)
                if not conflict_result.scalar_one_or_none():
                    available_rooms.append(room)
            rooms = available_rooms
        
        # Score rooms
        max_reservations = max(reservation_counts.values()) if reservation_counts else 1
        max_rating = 5.0
        
        scored_rooms = []
        for room in rooms:
            res_count = reservation_counts.get(room.id, 0)
            stats = room_stats.get(room.id, {})
            avg_rating = stats.get("avg_rating", 0) or 0
            review_count = stats.get("review_count", 0)
            
            # Trending score: 50% popularity + 50% rating
            popularity_score = res_count / max_reservations if max_reservations > 0 else 0
            rating_score = avg_rating / max_rating if avg_rating else 0
            trending_score = 0.5 * popularity_score + 0.5 * rating_score
            
            scored_rooms.append(RecommendedRoom(
                room_id=room.id,
                name=room.name,
                category=room.category,
                capacity=room.capacity,
                base_price_per_hour=room.base_price_per_hour,
                avg_rating=avg_rating if avg_rating else None,
                review_count=review_count,
                similarity_score=0.0,
                final_score=trending_score,
                reason="Trending room: Popular choice with high ratings",
            ))
        
        # Sort and return top
        scored_rooms.sort(key=lambda x: x.final_score, reverse=True)
        return scored_rooms[:limit]
    
    async def _get_room_stats(self) -> dict[UUID, dict]:
        """Get rating and popularity stats for all rooms."""
        query = select(
            Review.room_id,
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        ).group_by(Review.room_id)
        
        result = await self.db.execute(query)
        
        stats = {}
        for row in result:
            stats[row.room_id] = {
                "avg_rating": float(row.avg_rating) if row.avg_rating else None,
                "review_count": row.review_count,
            }
        
        # Get reservation counts for popularity
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        pop_query = (
            select(
                Reservation.room_id,
                func.count(Reservation.id).label("reservation_count"),
            )
            .where(Reservation.created_at >= thirty_days_ago)
            .group_by(Reservation.room_id)
        )
        
        pop_result = await self.db.execute(pop_query)
        for row in pop_result:
            if row.room_id not in stats:
                stats[row.room_id] = {}
            stats[row.room_id]["reservation_count"] = row.reservation_count
        
        return stats
    
    async def _get_user_interacted_rooms(self, user_id: UUID) -> list[Room]:
        """Get rooms the user has interacted with."""
        query = (
            select(Room)
            .join(UserEvent, Room.id == UserEvent.room_id)
            .where(UserEvent.user_id == user_id)
            .distinct()
            .limit(10)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _get_user_avg_price(self, user_id: UUID) -> Decimal | None:
        """Get average price of rooms the user has booked."""
        query = (
            select(func.avg(Room.base_price_per_hour))
            .join(Reservation, Room.id == Reservation.room_id)
            .where(Reservation.user_id == user_id)
        )
        result = await self.db.execute(query)
        avg = result.scalar()
        return Decimal(str(avg)) if avg else None
    
    def _compute_final_score(
        self,
        room: Room,
        similarity: float,
        room_stats: dict[UUID, dict],
        user_avg_price: Decimal | None,
    ) -> float:
        """Compute final re-ranking score."""
        stats = room_stats.get(room.id, {})
        
        # Rating normalized (0-1)
        avg_rating = stats.get("avg_rating", 0) or 0
        rating_norm = avg_rating / 5.0
        
        # Popularity normalized
        all_counts = [s.get("reservation_count", 0) for s in room_stats.values()]
        max_count = max(all_counts) if all_counts else 1
        room_count = stats.get("reservation_count", 0)
        popularity_norm = room_count / max_count if max_count > 0 else 0
        
        # Price match (how close to user's average price preference)
        price_match = 1.0
        if user_avg_price:
            price_diff = abs(float(room.base_price_per_hour) - float(user_avg_price))
            max_price_diff = float(user_avg_price) * 0.5  # 50% tolerance
            price_match = max(0, 1 - price_diff / max_price_diff) if max_price_diff > 0 else 1.0
        
        # Freshness (newer rooms get slight boost)
        days_since_creation = (datetime.now(timezone.utc) - room.created_at.replace(tzinfo=timezone.utc)).days
        freshness = max(0, 1 - days_since_creation / 365)  # Decay over 1 year
        
        # Compute final score
        final_score = (
            WEIGHT_SIMILARITY * similarity +
            WEIGHT_RATING * rating_norm +
            WEIGHT_POPULARITY * popularity_norm +
            WEIGHT_PRICE_MATCH * price_match +
            WEIGHT_FRESHNESS * freshness
        )
        
        return final_score
    
    def _generate_explanation(
        self,
        room: Room,
        user_rooms: list[Room],
        similarity: float,
    ) -> str:
        """Generate human-readable explanation for recommendation."""
        if not user_rooms:
            return f"Recommended based on popularity in {room.category.value} category"
        
        # Find most similar past room
        similar_past_room = None
        shared_attribute = None
        
        for past_room in user_rooms:
            if past_room.id == room.id:
                continue
            
            # Check shared attributes
            if past_room.category == room.category:
                similar_past_room = past_room
                shared_attribute = f"same category ({room.category.value})"
                break
            
            # Price tier match
            price_diff = abs(float(past_room.base_price_per_hour) - float(room.base_price_per_hour))
            if price_diff <= 5000:  # Within 5000 IDR
                similar_past_room = past_room
                shared_attribute = "similar price range"
                break
            
            # Capacity match
            if past_room.capacity == room.capacity:
                similar_past_room = past_room
                shared_attribute = f"same capacity ({room.capacity} people)"
                break
        
        if similar_past_room and shared_attribute:
            return f"Similar to {similar_past_room.name} you viewed - {shared_attribute}"
        
        # Default explanation based on category
        return f"Recommended for you based on your interest in {room.category.value} rooms"
