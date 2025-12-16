"""Test fixtures and configuration."""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.room import Room, RoomCategory, RoomStatus, Unit, ConsoleType, UnitStatus
from app.models.addon import Addon, AddonPriceType
from app.models.reservation import Reservation, ReservationStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.ai import RoomEmbedding


# Test database URL - use in-memory SQLite for tests
# For pgvector tests, use a test PostgreSQL database
TEST_DATABASE_URL = "postgresql+asyncpg://biggames:biggames123@localhost:5432/biggames_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        name="Admin User",
        password_hash=get_password_hash("adminpass123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_room(db_session: AsyncSession) -> Room:
    """Create a test room."""
    room = Room(
        id=uuid4(),
        name="Test VIP Room",
        description="A test VIP room",
        category=RoomCategory.VIP,
        capacity=4,
        base_price_per_hour=Decimal("30000"),
        status=RoomStatus.ACTIVE,
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)
    
    # Add unit
    unit = Unit(
        id=uuid4(),
        room_id=room.id,
        console_type=ConsoleType.PS5_PRO,
        jumlah_stick=2,
        status=UnitStatus.ACTIVE,
    )
    db_session.add(unit)
    await db_session.commit()
    
    return room


@pytest_asyncio.fixture
async def test_rooms(db_session: AsyncSession) -> list[Room]:
    """Create multiple test rooms."""
    rooms_data = [
        {"name": "VIP Room 1", "category": RoomCategory.VIP, "capacity": 6, "price": Decimal("40000")},
        {"name": "VIP Room 2", "category": RoomCategory.VIP, "capacity": 4, "price": Decimal("30000")},
        {"name": "PS5 Room", "category": RoomCategory.PS_SERIES, "capacity": 4, "price": Decimal("25000")},
        {"name": "Regular Room", "category": RoomCategory.REGULER, "capacity": 3, "price": Decimal("15000")},
    ]
    
    rooms = []
    for data in rooms_data:
        room = Room(
            id=uuid4(),
            name=data["name"],
            description=f"Test {data['name']}",
            category=data["category"],
            capacity=data["capacity"],
            base_price_per_hour=data["price"],
            status=RoomStatus.ACTIVE,
        )
        db_session.add(room)
        rooms.append(room)
    
    await db_session.commit()
    
    for room in rooms:
        await db_session.refresh(room)
    
    return rooms


@pytest_asyncio.fixture
async def test_addon(db_session: AsyncSession) -> Addon:
    """Create a test addon."""
    addon = Addon(
        id=uuid4(),
        name="Extra Controller",
        price_type=AddonPriceType.FLAT,
        price_amount=Decimal("5000"),
        is_active=True,
    )
    db_session.add(addon)
    await db_session.commit()
    await db_session.refresh(addon)
    return addon
