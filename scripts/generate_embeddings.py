"""Quick script to generate room embeddings after deployment."""
import asyncio
from app.db.session import async_session_maker
from app.services.ai import AIService
from app.models.room import Room, RoomStatus
from sqlalchemy import select


async def generate_all_embeddings():
    """Generate embeddings for all active rooms."""
    async with async_session_maker() as db:
        # Get all active rooms
        query = select(Room).where(Room.status == RoomStatus.ACTIVE)
        result = await db.execute(query)
        rooms = result.scalars().all()
        
        print(f'🔍 Found {len(rooms)} active rooms')
        
        if not rooms:
            print('⚠️  No active rooms found. Please seed data first.')
            return
        
        service = AIService(db)
        success = 0
        failed = 0
        
        for i, room in enumerate(rooms, 1):
            try:
                print(f'[{i}/{len(rooms)}] Generating embedding for: {room.name}...')
                await service.generate_room_embedding(room.id)
                success += 1
                print(f'  ✅ Success')
            except Exception as e:
                failed += 1
                print(f'  ❌ Error: {str(e)[:100]}')
        
        await db.commit()
        print(f'\n✅ Completed: {success} success, {failed} failed')


if __name__ == '__main__':
    print('🤖 Starting embedding generation...\n')
    asyncio.run(generate_all_embeddings())
    print('\n🎉 Done!')
