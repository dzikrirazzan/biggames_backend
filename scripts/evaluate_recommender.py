#!/usr/bin/env python3
"""Evaluate the room recommender system using HitRate@K and MRR@K metrics."""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.reservation import Reservation, ReservationStatus
from app.services.ai import AIService
from app.services.embedding import FakeEmbeddingProvider


async def get_users_with_events(db) -> list[User]:
    """Get users who have events."""
    from app.models.ai import UserEvent
    
    query = (
        select(User)
        .join(UserEvent, User.id == UserEvent.user_id)
        .distinct()
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_actual_bookings(db, user_id: UUID) -> set[UUID]:
    """Get rooms the user has actually booked."""
    query = select(Reservation.room_id).where(
        Reservation.user_id == user_id,
        Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED]),
    )
    result = await db.execute(query)
    return set(result.scalars().all())


def compute_hit_rate_at_k(recommended_ids: list[UUID], actual_ids: set[UUID], k: int) -> float:
    """Compute Hit Rate @ K.
    
    Hit Rate @ K = 1 if at least one of top-K recommendations is in actual set, else 0.
    """
    top_k = set(recommended_ids[:k])
    return 1.0 if len(top_k.intersection(actual_ids)) > 0 else 0.0


def compute_mrr_at_k(recommended_ids: list[UUID], actual_ids: set[UUID], k: int) -> float:
    """Compute Mean Reciprocal Rank @ K.
    
    MRR @ K = 1/rank of first relevant item in top-K, or 0 if none found.
    """
    for i, rec_id in enumerate(recommended_ids[:k]):
        if rec_id in actual_ids:
            return 1.0 / (i + 1)
    return 0.0


async def evaluate_recommender(k: int = 8):
    """Evaluate the recommender system."""
    print("\n" + "=" * 60)
    print(f"BIG GAMES Recommender Evaluation (K={k})")
    print("=" * 60 + "\n")
    
    # Create engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # Use FakeEmbeddingProvider for deterministic evaluation
    embedding_provider = FakeEmbeddingProvider()
    
    async with async_session() as db:
        try:
            # Get users with events
            users = await get_users_with_events(db)
            
            if not users:
                print("No users with events found. Run seed_demo_data.py first.")
                return
            
            print(f"Found {len(users)} users with events")
            print("-" * 40)
            
            hit_rates = []
            mrrs = []
            
            for user in users:
                # Get actual bookings
                actual_bookings = await get_user_actual_bookings(db, user.id)
                
                if not actual_bookings:
                    print(f"  {user.name}: No bookings (skipped)")
                    continue
                
                # Get recommendations
                ai_service = AIService(db, embedding_provider)
                recommendations = await ai_service.get_recommendations(
                    user_id=user.id,
                    limit=k,
                )
                
                recommended_ids = [r.room_id for r in recommendations.recommendations]
                
                # Compute metrics
                hit_rate = compute_hit_rate_at_k(recommended_ids, actual_bookings, k)
                mrr = compute_mrr_at_k(recommended_ids, actual_bookings, k)
                
                hit_rates.append(hit_rate)
                mrrs.append(mrr)
                
                print(f"  {user.name}:")
                print(f"    - Actual bookings: {len(actual_bookings)}")
                print(f"    - Recommendations: {len(recommended_ids)}")
                print(f"    - Cold start: {recommendations.is_cold_start}")
                print(f"    - Hit Rate @{k}: {hit_rate:.4f}")
                print(f"    - MRR @{k}: {mrr:.4f}")
            
            if hit_rates:
                print("\n" + "=" * 40)
                print("AGGREGATE METRICS")
                print("=" * 40)
                print(f"  Hit Rate @{k}: {np.mean(hit_rates):.4f} (±{np.std(hit_rates):.4f})")
                print(f"  MRR @{k}: {np.mean(mrrs):.4f} (±{np.std(mrrs):.4f})")
                print(f"  Users evaluated: {len(hit_rates)}")
            else:
                print("\nNo users with bookings to evaluate.")
            
        except Exception as e:
            print(f"\nError during evaluation: {e}")
            raise
        finally:
            await engine.dispose()


async def test_cold_start():
    """Test cold start recommendations."""
    print("\n" + "=" * 60)
    print("Cold Start Test")
    print("=" * 60 + "\n")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    embedding_provider = FakeEmbeddingProvider()
    
    async with async_session() as db:
        try:
            ai_service = AIService(db, embedding_provider)
            
            # Test with no user (anonymous)
            recommendations = await ai_service.get_recommendations(
                user_id=None,
                limit=8,
            )
            
            print("Anonymous user (cold start):")
            print(f"  Is cold start: {recommendations.is_cold_start}")
            print(f"  Recommendations: {len(recommendations.recommendations)}")
            
            for i, rec in enumerate(recommendations.recommendations[:5], 1):
                print(f"  {i}. {rec.name} - Score: {rec.final_score:.4f}")
                print(f"     Reason: {rec.reason}")
            
        except Exception as e:
            print(f"\nError during cold start test: {e}")
            raise
        finally:
            await engine.dispose()


async def test_determinism():
    """Test that FakeEmbeddingProvider is deterministic."""
    print("\n" + "=" * 60)
    print("Determinism Test (FakeEmbeddingProvider)")
    print("=" * 60 + "\n")
    
    provider = FakeEmbeddingProvider()
    
    text1 = "VIP ROOM 1 - Premium gaming experience"
    text2 = "VIP ROOM 1 - Premium gaming experience"
    text3 = "Regular Room - Budget gaming"
    
    emb1 = await provider.get_embedding(text1)
    emb2 = await provider.get_embedding(text2)
    emb3 = await provider.get_embedding(text3)
    
    # Check determinism
    is_deterministic = np.allclose(emb1, emb2)
    
    # Check different texts produce different embeddings
    are_different = not np.allclose(emb1, emb3)
    
    print(f"Same text produces same embedding: {is_deterministic}")
    print(f"Different texts produce different embeddings: {are_different}")
    print(f"Embedding dimension: {len(emb1)}")
    print(f"Embedding is normalized: {np.allclose(np.linalg.norm(emb1), 1.0)}")
    
    if is_deterministic and are_different:
        print("\n✓ FakeEmbeddingProvider is working correctly!")
    else:
        print("\n✗ FakeEmbeddingProvider has issues!")


async def main():
    """Run all evaluations."""
    # Test determinism first
    await test_determinism()
    
    # Test cold start
    await test_cold_start()
    
    # Run full evaluation
    await evaluate_recommender(k=8)
    
    print("\n" + "=" * 60)
    print("Evaluation Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
