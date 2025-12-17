#!/usr/bin/env python3
"""Seed demo data for BIG GAMES Online Booking."""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import Base
from app.models.user import User, UserRole
from app.models.room import Room, RoomCategory, RoomStatus, Unit, ConsoleType, UnitStatus
from app.models.addon import Addon, AddonPriceType
from app.models.promo import Promo, DiscountType
from app.models.menu import MenuItem, MenuCategory
from app.models.reservation import Reservation, ReservationStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.review import Review
from app.models.ai import UserEvent, EventType, RoomEmbedding
from app.services.embedding import get_embedding_provider


async def clear_data(db: AsyncSession):
    """Clear existing data."""
    print("Clearing existing data...")
    
    await db.execute(text("DELETE FROM room_embeddings"))
    await db.execute(text("DELETE FROM user_events"))
    await db.execute(text("DELETE FROM reviews"))
    await db.execute(text("DELETE FROM fb_order_items"))
    await db.execute(text("DELETE FROM fb_orders"))
    await db.execute(text("DELETE FROM payments"))
    await db.execute(text("DELETE FROM reservation_addons"))
    await db.execute(text("DELETE FROM reservations"))
    await db.execute(text("DELETE FROM menu_items"))
    await db.execute(text("DELETE FROM promos"))
    await db.execute(text("DELETE FROM addons"))
    await db.execute(text("DELETE FROM units"))
    await db.execute(text("DELETE FROM room_images"))
    await db.execute(text("DELETE FROM rooms"))
    await db.execute(text("DELETE FROM users"))
    
    await db.commit()
    print("  Data cleared")


async def seed_users(db: AsyncSession) -> dict:
    """Seed users."""
    print("Seeding users...")
    
    users = {
        "admin": User(
            email="admin@biggames.com",
            name="Admin BIG GAMES",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
        ),
        "finance": User(
            email="finance@biggames.com",
            name="Finance Team",
            password_hash=get_password_hash("finance123"),
            role=UserRole.FINANCE,
        ),
        "demo": User(
            email="demo@example.com",
            name="Demo User",
            password_hash=get_password_hash("demo123"),
            role=UserRole.USER,
        ),
        "user1": User(
            email="user1@example.com",
            name="John Gamer",
            password_hash=get_password_hash("user123"),
            role=UserRole.USER,
        ),
        "user2": User(
            email="user2@example.com",
            name="Jane Player",
            password_hash=get_password_hash("user123"),
            role=UserRole.USER,
        ),
    }
    
    for user in users.values():
        db.add(user)
    
    await db.flush()
    for user in users.values():
        await db.refresh(user)
    
    print(f"  Created {len(users)} users")
    return users


async def seed_rooms(db: AsyncSession) -> dict:
    """Seed 6 rooms."""
    print("Seeding rooms...")
    
    rooms_data = [
        {
            "name": "VIP ROOM 1",
            "description": "Premium VIP room dengan PS5 Pro, TV 65 inch 4K, soundbar premium, sofa nyaman, AC, WiFi cepat. Pengalaman gaming terbaik!",
            "category": RoomCategory.VIP,
            "capacity": 6,
            "base_price_per_hour": Decimal("50000"),
            "console_type": ConsoleType.PS5_PRO,
            "jumlah_stick": 4,
        },
        {
            "name": "VIP ROOM 2",
            "description": "VIP room nyaman dengan PS5 Slim, TV 55 inch 4K, sound system berkualitas, sofa empuk, AC, WiFi. Cocok untuk grup!",
            "category": RoomCategory.VIP,
            "capacity": 4,
            "base_price_per_hour": Decimal("40000"),
            "console_type": ConsoleType.PS5_SLIM,
            "jumlah_stick": 2,
        },
        {
            "name": "VIP ROOM 3",
            "description": "VIP room seru dengan Nintendo Switch, TV 50 inch, cocok untuk party games seperti Mario Kart, Smash Bros, dan lainnya!",
            "category": RoomCategory.VIP,
            "capacity": 4,
            "base_price_per_hour": Decimal("35000"),
            "console_type": ConsoleType.NINTENDO_SWITCH,
            "jumlah_stick": 4,
        },
        {
            "name": "REGULER 1",
            "description": "Room reguler dengan PS4 Pro, TV 50 inch 4K, audio bagus, tempat duduk nyaman. Value terbaik untuk gaming kompetitif.",
            "category": RoomCategory.REGULAR,
            "capacity": 4,
            "base_price_per_hour": Decimal("25000"),
            "console_type": ConsoleType.PS4_PRO,
            "jumlah_stick": 2,
        },
        {
            "name": "REGULER 2",
            "description": "Room budget-friendly dengan PS4 Slim, TV 42 inch, audio standar. Cocok untuk gaming casual.",
            "category": RoomCategory.REGULAR,
            "capacity": 3,
            "base_price_per_hour": Decimal("20000"),
            "console_type": ConsoleType.PS4_SLIM,
            "jumlah_stick": 2,
        },
        {
            "name": "SIMULATOR",
            "description": "Room racing simulator dengan steering wheel profesional, pedal, shifter, kursi racing, triple monitor. Rasakan sensasi balapan nyata!",
            "category": RoomCategory.SIMULATOR,
            "capacity": 2,
            "base_price_per_hour": Decimal("45000"),
            "console_type": ConsoleType.PS5_PRO,
            "jumlah_stick": 1,
        },
    ]
    
    rooms = {}
    for room_data in rooms_data:
        console_type = room_data.pop("console_type")
        jumlah_stick = room_data.pop("jumlah_stick")
        
        room = Room(**room_data)
        db.add(room)
        await db.flush()
        await db.refresh(room)
        
        unit = Unit(
            room_id=room.id,
            console_type=console_type,
            jumlah_stick=jumlah_stick,
            status=UnitStatus.ACTIVE,
        )
        db.add(unit)
        
        rooms[room.name] = room
    
    await db.flush()
    print(f"  Created {len(rooms)} rooms")
    return rooms


async def seed_addons(db: AsyncSession) -> dict:
    """Seed addons."""
    print("Seeding addons...")
    
    addons_data = [
        {"name": "Extra Controller", "price_amount": Decimal("10000"), "price_type": AddonPriceType.FLAT},
        {"name": "VR Headset", "price_amount": Decimal("25000"), "price_type": AddonPriceType.PER_HOUR},
        {"name": "Snack Package", "price_amount": Decimal("30000"), "price_type": AddonPriceType.FLAT},
    ]
    
    addons = {}
    for addon_data in addons_data:
        addon = Addon(**addon_data)
        db.add(addon)
        addons[addon.name] = addon
    
    await db.flush()
    print(f"  Created {len(addons)} addons")
    return addons


async def seed_promos(db: AsyncSession) -> dict:
    """Seed promos."""
    print("Seeding promos...")
    
    now = datetime.now(timezone.utc)
    
    promos_data = [
        {"code": "NEWUSER", "discount_type": DiscountType.PERCENT, "discount_value": Decimal("10"), "start_date": now - timedelta(days=30), "end_date": now + timedelta(days=365), "is_active": True},
        {"code": "WEEKEND20", "discount_type": DiscountType.PERCENT, "discount_value": Decimal("20"), "start_date": now - timedelta(days=30), "end_date": now + timedelta(days=365), "is_active": True},
        {"code": "FLAT10K", "discount_type": DiscountType.FIXED, "discount_value": Decimal("10000"), "start_date": now - timedelta(days=30), "end_date": now + timedelta(days=365), "is_active": True},
    ]
    
    promos = {}
    for promo_data in promos_data:
        promo = Promo(**promo_data)
        db.add(promo)
        promos[promo.code] = promo
    
    await db.flush()
    print(f"  Created {len(promos)} promos")
    return promos


async def seed_menu_items(db: AsyncSession) -> dict:
    """Seed menu items."""
    print("Seeding menu items...")
    
    menu_data = [
        {"name": "Nasi Goreng Spesial", "description": "Nasi goreng dengan telur, ayam, sayuran", "category": MenuCategory.FOOD, "price": Decimal("25000"), "stock": 50},
        {"name": "Mie Goreng", "description": "Mie goreng dengan telur dan sayuran", "category": MenuCategory.FOOD, "price": Decimal("20000"), "stock": 50},
        {"name": "Ayam Geprek", "description": "Ayam geprek dengan sambal dan nasi", "category": MenuCategory.FOOD, "price": Decimal("28000"), "stock": 30},
        {"name": "Burger Beef", "description": "Beef burger dengan keju dan sayuran", "category": MenuCategory.FOOD, "price": Decimal("35000"), "stock": 25},
        {"name": "French Fries", "description": "Kentang goreng crispy", "category": MenuCategory.SNACK, "price": Decimal("18000"), "stock": 100},
        {"name": "Es Teh Manis", "description": "Teh manis dingin", "category": MenuCategory.BEVERAGE, "price": Decimal("8000"), "stock": 100},
        {"name": "Es Jeruk", "description": "Jeruk peras segar", "category": MenuCategory.BEVERAGE, "price": Decimal("10000"), "stock": 80},
        {"name": "Kopi Susu", "description": "Kopi susu gula aren", "category": MenuCategory.BEVERAGE, "price": Decimal("18000"), "stock": 60},
        {"name": "Coca Cola", "description": "Coca Cola dingin 330ml", "category": MenuCategory.BEVERAGE, "price": Decimal("12000"), "stock": 100},
        {"name": "Mineral Water", "description": "Air mineral 600ml", "category": MenuCategory.BEVERAGE, "price": Decimal("6000"), "stock": 200},
        {"name": "Popcorn", "description": "Popcorn caramel", "category": MenuCategory.SNACK, "price": Decimal("15000"), "stock": 50},
        {"name": "Nachos", "description": "Nachos dengan keju", "category": MenuCategory.SNACK, "price": Decimal("22000"), "stock": 40},
        {"name": "Chicken Wings", "description": "Sayap ayam goreng 6 pcs", "category": MenuCategory.SNACK, "price": Decimal("28000"), "stock": 35},
        {"name": "Potato Wedges", "description": "Potato wedges dengan saus", "category": MenuCategory.SNACK, "price": Decimal("20000"), "stock": 45},
    ]
    
    items = {}
    for item_data in menu_data:
        item = MenuItem(**item_data, is_active=True)
        db.add(item)
        items[item.name] = item
    
    await db.flush()
    print(f"  Created {len(items)} menu items")
    return items


async def seed_reservations(db: AsyncSession, users: dict, rooms: dict) -> list:
    """Seed sample reservations."""
    print("Seeding reservations...")
    
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    reservations_data = [
        # TODAY - VIP ROOM 1
        {"user": "demo", "room": "VIP ROOM 1", "day": 0, "start": 10, "end": 12, "status": ReservationStatus.CONFIRMED},
        {"user": "user1", "room": "VIP ROOM 1", "day": 0, "start": 14, "end": 16, "status": ReservationStatus.CONFIRMED},
        {"user": "user2", "room": "VIP ROOM 1", "day": 0, "start": 18, "end": 20, "status": ReservationStatus.CONFIRMED},
        # TODAY - VIP ROOM 2
        {"user": "user1", "room": "VIP ROOM 2", "day": 0, "start": 11, "end": 13, "status": ReservationStatus.CONFIRMED},
        {"user": "demo", "room": "VIP ROOM 2", "day": 0, "start": 16, "end": 18, "status": ReservationStatus.CONFIRMED},
        # TODAY - VIP ROOM 3
        {"user": "demo", "room": "VIP ROOM 3", "day": 0, "start": 15, "end": 18, "status": ReservationStatus.CONFIRMED},
        # TODAY - REGULER 1
        {"user": "user2", "room": "REGULER 1", "day": 0, "start": 10, "end": 11, "status": ReservationStatus.CONFIRMED},
        {"user": "user1", "room": "REGULER 1", "day": 0, "start": 13, "end": 15, "status": ReservationStatus.CONFIRMED},
        # TODAY - SIMULATOR
        {"user": "user1", "room": "SIMULATOR", "day": 0, "start": 12, "end": 14, "status": ReservationStatus.CONFIRMED},
        {"user": "demo", "room": "SIMULATOR", "day": 0, "start": 17, "end": 19, "status": ReservationStatus.CONFIRMED},
        # TOMORROW
        {"user": "user2", "room": "VIP ROOM 1", "day": 1, "start": 10, "end": 12, "status": ReservationStatus.CONFIRMED},
        {"user": "demo", "room": "REGULER 1", "day": 1, "start": 13, "end": 15, "status": ReservationStatus.CONFIRMED},
        {"user": "user1", "room": "SIMULATOR", "day": 1, "start": 14, "end": 16, "status": ReservationStatus.CONFIRMED},
        # PENDING PAYMENT
        {"user": "user2", "room": "VIP ROOM 2", "day": 1, "start": 15, "end": 17, "status": ReservationStatus.PENDING_PAYMENT},
        # YESTERDAY (COMPLETED)
        {"user": "demo", "room": "VIP ROOM 1", "day": -1, "start": 14, "end": 16, "status": ReservationStatus.COMPLETED},
        {"user": "user1", "room": "SIMULATOR", "day": -2, "start": 10, "end": 12, "status": ReservationStatus.COMPLETED},
    ]
    
    reservations = []
    for data in reservations_data:
        target_date = today + timedelta(days=data["day"])
        start_time = target_date.replace(hour=data["start"])
        end_time = target_date.replace(hour=data["end"])
        
        room = rooms[data["room"]]
        user = users[data["user"]]
        duration = data["end"] - data["start"]
        subtotal = room.base_price_per_hour * duration
        
        reservation = Reservation(
            user_id=user.id,
            room_id=room.id,
            start_time=start_time,
            end_time=end_time,
            duration_hours=Decimal(str(duration)),
            subtotal=subtotal,
            discount_amount=Decimal("0"),
            total_amount=subtotal,
            status=data["status"],
        )
        db.add(reservation)
        await db.flush()
        await db.refresh(reservation)
        
        payment_status = PaymentStatus.PAID if data["status"] in [ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED] else PaymentStatus.WAITING_CONFIRMATION
        payment = Payment(
            reservation_id=reservation.id,
            method=PaymentMethod.QRIS,
            status=payment_status,
            amount=subtotal,
        )
        db.add(payment)
        
        reservations.append(reservation)
    
    await db.flush()
    print(f"  Created {len(reservations)} reservations")
    return reservations


async def seed_reviews(db: AsyncSession, users: dict, rooms: dict, reservations: list):
    """Seed reviews."""
    print("Seeding reviews...")
    
    completed = [r for r in reservations if r.status == ReservationStatus.COMPLETED]
    
    reviews_data = [
        {"rating": 5, "comment": "Room nya bagus banget! PS5 Pro lancar, TV gede. Pasti balik lagi!"},
        {"rating": 5, "comment": "Simulator racing keren! Steering wheel responsif. Recommended!"},
    ]
    
    for i, data in enumerate(reviews_data):
        if i < len(completed):
            review = Review(
                user_id=completed[i].user_id,
                room_id=completed[i].room_id,
                reservation_id=completed[i].id,
                rating=data["rating"],
                comment=data["comment"],
            )
            db.add(review)
    
    await db.flush()
    print(f"  Created {len(reviews_data)} reviews")


async def seed_user_events(db: AsyncSession, users: dict, rooms: dict):
    """Seed user events for AI."""
    print("Seeding user events...")
    
    events = []
    
    # Demo user - prefers VIP
    for room_name in ["VIP ROOM 1", "VIP ROOM 2", "VIP ROOM 3"]:
        for event_type in [EventType.VIEW_ROOM, EventType.CLICK_ROOM]:
            event = UserEvent(user_id=users["demo"].id, room_id=rooms[room_name].id, event_type=event_type)
            db.add(event)
            events.append(event)
    
    event = UserEvent(user_id=users["demo"].id, room_id=rooms["VIP ROOM 1"].id, event_type=EventType.BOOK_ROOM)
    db.add(event)
    events.append(event)
    
    # User1 - likes simulator
    for event_type in [EventType.VIEW_ROOM, EventType.CLICK_ROOM, EventType.BOOK_ROOM]:
        event = UserEvent(user_id=users["user1"].id, room_id=rooms["SIMULATOR"].id, event_type=event_type)
        db.add(event)
        events.append(event)
    
    await db.flush()
    print(f"  Created {len(events)} user events")


async def seed_room_embeddings(db: AsyncSession, rooms: dict):
    """Seed room embeddings."""
    print("Generating room embeddings...")
    
    provider = get_embedding_provider()
    
    for room in rooms.values():
        text = f"{room.name} {room.category.value} {room.description}"
        embedding = await provider.get_embedding(text)
        room_embedding = RoomEmbedding(room_id=room.id, embedding=embedding)
        db.add(room_embedding)
    
    await db.flush()
    print(f"  Created {len(rooms)} room embeddings")


async def main():
    print("\n" + "=" * 60)
    print("BIG GAMES Online Booking - Database Seeder")
    print("=" * 60 + "\n")
    
    # Fix DATABASE_URL untuk async driver (same as app/db/session.py)
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={
            "statement_cache_size": 0,  # Required for pgbouncer/Supabase pooler
        },
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            await clear_data(db)
            
            users = await seed_users(db)
            rooms = await seed_rooms(db)
            await seed_addons(db)
            await seed_promos(db)
            await seed_menu_items(db)
            reservations = await seed_reservations(db, users, rooms)
            await seed_reviews(db, users, rooms, reservations)
            await seed_user_events(db, users, rooms)
            await seed_room_embeddings(db, rooms)
            
            await db.commit()
            
            print("\n" + "=" * 60)
            print("✅ Seed completed successfully!")
            print("=" * 60)
            
            print("\n👤 Demo Accounts:")
            print("   Admin:   admin@biggames.com / admin123")
            print("   Finance: finance@biggames.com / finance123")
            print("   User:    demo@example.com / demo123")
            print("   User:    user1@example.com / user123")
            print("   User:    user2@example.com / user123")
            
            print("\n🎫 Promo Codes: NEWUSER, WEEKEND20, FLAT10K")
            
            print("\n🎮 6 Rooms:")
            for room in rooms.values():
                print(f"   - {room.name} ({room.category.value}) - Rp {room.base_price_per_hour:,.0f}/jam")
            
            print("\n📅 Sample Bookings (Today):")
            print("   VIP ROOM 1: 10:00-12:00, 14:00-16:00, 18:00-20:00")
            print("   VIP ROOM 2: 11:00-13:00, 16:00-18:00")
            print("   VIP ROOM 3: 15:00-18:00")
            print("   REGULER 1:  10:00-11:00, 13:00-15:00")
            print("   SIMULATOR:  12:00-14:00, 17:00-19:00")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
