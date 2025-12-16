"""AI recommendation routes."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import UserEventCreate, RecommendationResponse
from app.services.ai import AIService
from app.api.deps import get_current_user, get_optional_user


router = APIRouter(prefix="/ai", tags=["AI Recommendations"])


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def log_event(
    event_data: UserEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log a user event (VIEW/CLICK/BOOK/RATE)."""
    ai_service = AIService(db)
    event = await ai_service.log_event(current_user.id, event_data)
    return {
        "id": str(event.id),
        "event_type": event.event_type.value,
        "room_id": str(event.room_id),
        "created_at": event.created_at.isoformat(),
    }


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    limit: int = Query(8, ge=1, le=50),
    start: datetime | None = Query(None, description="Filter available rooms from this time"),
    end: datetime | None = Query(None, description="Filter available rooms until this time"),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get room recommendations for the user."""
    ai_service = AIService(db)
    return await ai_service.get_recommendations(
        user_id=current_user.id if current_user else None,
        limit=limit,
        start=start,
        end=end,
    )


@router.post("/embeddings/generate/{room_id}", status_code=status.HTTP_200_OK)
async def generate_room_embedding(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate or update embedding for a specific room (Admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can generate embeddings",
        )
    
    ai_service = AIService(db)
    try:
        embedding = await ai_service.generate_room_embedding(room_id)
        return {
            "room_id": str(embedding.room_id),
            "dimension": len(embedding.embedding),
            "updated_at": embedding.updated_at.isoformat(),
            "message": "Embedding generated successfully",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embedding: {str(e)}",
        )


@router.post("/embeddings/generate-all", status_code=status.HTTP_200_OK)
async def generate_all_room_embeddings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate embeddings for all rooms (Admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can generate embeddings",
        )
    
    from app.models.room import Room, RoomStatus
    from sqlalchemy import select
    
    # Get all active rooms
    query = select(Room).where(Room.status == RoomStatus.ACTIVE)
    result = await db.execute(query)
    rooms = result.scalars().all()
    
    ai_service = AIService(db)
    success_count = 0
    error_count = 0
    errors = []
    
    for room in rooms:
        try:
            await ai_service.generate_room_embedding(room.id)
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append({"room_id": str(room.id), "room_name": room.name, "error": str(e)})
    
    await db.commit()
    
    return {
        "total_rooms": len(rooms),
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors[:10],  # Return first 10 errors
        "message": f"Generated embeddings for {success_count}/{len(rooms)} rooms",
    }
