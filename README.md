# BIG GAMES Backend API

Backend system for PlayStation room rental and food ordering platform. Built with FastAPI, PostgreSQL with pgvector, and AI-powered recommendations.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Features

**Core Functionality**

- Room booking system with real-time availability
- Food & beverage ordering linked to reservations
- Payment verification (QRIS/Bank Transfer)
- AI-powered room recommendations
- User reviews and ratings

**Authentication & Authorization**

- JWT-based authentication
- Role-based access control (Admin, Finance, User)
- Secure password hashing

**AI Recommendations**

- Personalized suggestions using pgvector embeddings
- Hybrid scoring algorithm (similarity + popularity + ratings)
- Cold start handling for new users

---

## Tech Stack

| Component        | Technology               |
| ---------------- | ------------------------ |
| Framework        | FastAPI 0.109.0          |
| Database         | PostgreSQL 16 + pgvector |
| ORM              | SQLAlchemy 2.0 (async)   |
| Migrations       | Alembic 1.13.1           |
| Authentication   | JWT (python-jose)        |
| Validation       | Pydantic v2              |
| Containerization | Docker Compose           |

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Installation

**1. Clone and Configure**

```bash
git clone <repository-url>
cd biggames_backend
cp .env.example .env
```

**2. Start Services**

```bash
docker-compose up -d
```

Services:

- API: http://localhost:8000
- PostgreSQL: localhost:5432
- API Docs: http://localhost:8000/docs

**3. Initialize Database**

```bash
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/seed_demo_data.py
```

**4. Verify Installation**

```bash
curl http://localhost:8000/health
```

---

## API Documentation

### Base URL

- Local: `http://localhost:8000`
- Production: `https://2d4ae8dc10a3.ngrok-free.app`

### Interactive Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`

### Authentication

All protected endpoints require Bearer token:

```bash
Authorization: Bearer <access_token>
```

### Demo Accounts

| Email                | Password   | Role    |
| -------------------- | ---------- | ------- |
| admin@biggames.com   | admin123   | ADMIN   |
| finance@biggames.com | finance123 | FINANCE |
| user@example.com     | user123    | USER    |

---

## API Examples

### Authentication

#### Register

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "password123",
    "name": "New User",
    "phone": "081234567890"
  }'
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "name": "New User",
  "phone": "081234567890",
  "role": "USER",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "andi@gmail.com",
    "password": "user123"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Rooms

#### List All Rooms

```bash
curl http://localhost:8000/api/rooms
```

**Response:**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "VIP Room 1",
      "description": "Premium VIP room with PS5 Pro",
      "category": "VIP",
      "capacity": 6,
      "base_price_per_hour": 50000.0,
      "status": "ACTIVE",
      "images": [
        {
          "id": "...",
          "image_url": "https://example.com/vip1.jpg",
          "is_primary": true
        }
      ],
      "units": [
        {
          "id": "...",
          "console_type": "PS5 Pro",
          "controller_count": 4,
          "has_vr": true
        }
      ]
    }
  ],
  "total": 9,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

#### Filter by Category

```bash
curl "http://localhost:8000/api/rooms?category=VIP"
```

#### Check Room Availability

```bash
curl "http://localhost:8000/api/rooms/550e8400-e29b-41d4-a716-446655440001/availability?date=2024-01-20"
```

**Response:**

```json
{
  "room_id": "550e8400-e29b-41d4-a716-446655440001",
  "date": "2024-01-20",
  "operating_hours": {
    "open": "10:00",
    "close": "23:00"
  },
  "available_slots": [
    {
      "start": "2024-01-20T10:00:00",
      "end": "2024-01-20T12:00:00"
    },
    {
      "start": "2024-01-20T14:00:00",
      "end": "2024-01-20T23:00:00"
    }
  ],
  "booked_slots": [
    {
      "start": "2024-01-20T12:00:00",
      "end": "2024-01-20T14:00:00"
    }
  ]
}
```

#### Get Room Details

```bash
curl http://localhost:8000/api/rooms/550e8400-e29b-41d4-a716-446655440001
```

---

### Reservations

#### Create Reservation

```bash
curl -X POST http://localhost:8000/api/reservations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "550e8400-e29b-41d4-a716-446655440001",
    "start_time": "2024-01-20T14:00:00",
    "end_time": "2024-01-20T16:00:00",
    "addon_ids": ["addon-uuid-1", "addon-uuid-2"],
    "promo_code": "NEWUSER20"
  }'
```

**Response:**

```json
{
  "id": "res-550e8400-e29b-41d4-a716-446655440001",
  "user_id": "user-uuid",
  "room_id": "550e8400-e29b-41d4-a716-446655440001",
  "room": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "VIP Room 1",
    "category": "VIP"
  },
  "start_time": "2024-01-20T14:00:00Z",
  "end_time": "2024-01-20T16:00:00Z",
  "duration_hours": 2.0,
  "subtotal": 120000.0,
  "discount_amount": 24000.0,
  "total_amount": 96000.0,
  "status": "PENDING_PAYMENT",
  "promo": {
    "code": "NEWUSER20",
    "discount_percent": 20
  },
  "addons": [
    {
      "addon_id": "addon-uuid-1",
      "addon_name": "Extra Controller",
      "quantity": 1,
      "price": 10000.0
    }
  ],
  "payment": {
    "id": "payment-uuid",
    "method": null,
    "status": "PENDING",
    "amount": 96000.0
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Get User's Reservations

```bash
curl http://localhost:8000/api/reservations \
  -H "Authorization: Bearer $TOKEN"
```

#### Cancel Reservation

```bash
curl -X PUT http://localhost:8000/api/reservations/res-uuid/cancel \
  -H "Authorization: Bearer $TOKEN"
```

---

### Payments

#### Get Payment Info (Bank Account/QRIS)

```bash
curl http://localhost:8000/api/payment/info
```

**Response:**

```json
{
  "bank_account_name": "PT BIG GAMES INDONESIA",
  "bank_account_number": "1234567890",
  "bank_name": "BCA",
  "qris_image_url": "https://example.com/qris.png"
}
```

#### Upload Payment Proof

```bash
curl -X POST http://localhost:8000/api/payment/upload-proof/payment-uuid \
  -H "Authorization: Bearer $TOKEN" \
  -F "method=QRIS" \
  -F "proof=@/path/to/proof.jpg"
```

**Response:**

```json
{
  "id": "payment-uuid",
  "reservation_id": "res-uuid",
  "method": "QRIS",
  "status": "WAITING_VERIFICATION",
  "amount": 96000.0,
  "proof_image_url": "https://storage.example.com/proofs/payment-uuid.jpg",
  "created_at": "2024-01-15T10:35:00Z",
  "updated_at": "2024-01-15T10:36:00Z"
}
```

#### (Admin/Finance) Get Pending Payments

```bash
curl http://localhost:8000/api/payment/pending \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response:**

```json
[
  {
    "id": "payment-uuid",
    "reservation_id": "res-uuid",
    "method": "QRIS",
    "status": "WAITING_VERIFICATION",
    "amount": 96000.0,
    "proof_image_url": "https://storage.example.com/proofs/proof.jpg",
    "reservation": {
      "id": "res-uuid",
      "room": {
        "name": "VIP Room 1"
      },
      "user": {
        "name": "Andi",
        "email": "andi@gmail.com"
      },
      "start_time": "2024-01-20T14:00:00Z"
    }
  }
]
```

#### (Admin/Finance) Confirm Payment

```bash
curl -X PUT http://localhost:8000/api/payment/confirm/payment-uuid \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response:**

```json
{
  "id": "payment-uuid",
  "reservation_id": "res-uuid",
  "method": "QRIS",
  "status": "PAID",
  "amount": 96000.0,
  "verified_by": "admin-uuid",
  "verified_at": "2024-01-15T10:40:00Z"
}
```

#### (Admin/Finance) Reject Payment

```bash
curl -X PUT http://localhost:8000/api/payment/reject/payment-uuid \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Proof image is blurry, please reupload"
  }'
```

---

### Menu (Food & Beverages)

#### Get Menu

```bash
curl http://localhost:8000/api/menu
```

**Response:**

```json
{
  "items": [
    {
      "id": "menu-uuid-1",
      "name": "Nasi Goreng Special",
      "description": "Nasi goreng with chicken, egg, and vegetables",
      "category": "FOOD",
      "price": 25000.0,
      "image_url": "https://example.com/nasigoreng.jpg",
      "is_available": true
    },
    {
      "id": "menu-uuid-2",
      "name": "Es Teh Manis",
      "description": "Sweet iced tea",
      "category": "BEVERAGE",
      "price": 8000.0,
      "image_url": "https://example.com/esteh.jpg",
      "is_available": true
    }
  ],
  "total": 14,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

#### Filter by Category

```bash
curl "http://localhost:8000/api/menu?category=FOOD"
curl "http://localhost:8000/api/menu?category=BEVERAGE"
curl "http://localhost:8000/api/menu?category=SNACK"
```

---

### F&B Orders

#### Create F&B Order

```bash
curl -X POST http://localhost:8000/api/fb-orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_id": "res-uuid",
    "items": [
      {
        "menu_item_id": "menu-uuid-1",
        "quantity": 2,
        "notes": "Extra spicy"
      },
      {
        "menu_item_id": "menu-uuid-2",
        "quantity": 3
      }
    ]
  }'
```

**Response:**

```json
{
  "id": "fb-order-uuid",
  "user_id": "user-uuid",
  "reservation_id": "res-uuid",
  "room_id": "room-uuid",
  "status": "PENDING",
  "total_amount": 74000.0,
  "items": [
    {
      "id": "item-uuid-1",
      "menu_item_id": "menu-uuid-1",
      "menu_item_name": "Nasi Goreng Special",
      "quantity": 2,
      "unit_price": 25000.0,
      "subtotal": 50000.0,
      "notes": "Extra spicy"
    },
    {
      "id": "item-uuid-2",
      "menu_item_id": "menu-uuid-2",
      "menu_item_name": "Es Teh Manis",
      "quantity": 3,
      "unit_price": 8000.0,
      "subtotal": 24000.0,
      "notes": null
    }
  ],
  "created_at": "2024-01-20T14:30:00Z"
}
```

#### Get User's F&B Orders

```bash
curl http://localhost:8000/api/fb-orders \
  -H "Authorization: Bearer $TOKEN"
```

#### (Admin) Update Order Status

```bash
curl -X PUT http://localhost:8000/api/fb-orders/fb-order-uuid/status \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "PREPARING"
  }'
```

---

### Promo Codes

#### Validate Promo Code

```bash
curl -X POST http://localhost:8000/api/promo/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "NEWUSER20",
    "room_id": "room-uuid"
  }'
```

**Response:**

```json
{
  "valid": true,
  "promo": {
    "id": "promo-uuid",
    "code": "NEWUSER20",
    "description": "20% off for new users",
    "discount_percent": 20,
    "max_discount_amount": 50000.0,
    "min_booking_hours": 2,
    "valid_from": "2024-01-01T00:00:00Z",
    "valid_until": "2024-12-31T23:59:59Z"
  }
}
```

---

### AI Recommendations

#### Get Personalized Recommendations

```bash
curl http://localhost:8000/api/ai/recommendations \
  -H "Authorization: Bearer $TOKEN"
```

**Response (Cold Start - New User):**

```json
{
  "recommendations": [
    {
      "id": "room-uuid-1",
      "name": "VIP Room 1",
      "description": "Premium VIP room with PS5 Pro",
      "category": "VIP",
      "base_price_per_hour": 50000.0,
      "similarity_score": null,
      "final_score": 0.85,
      "reason": "Trending: Popular choice with high ratings"
    },
    {
      "id": "room-uuid-2",
      "name": "PS5 Room Premium",
      "description": "PS5 room with 4K display",
      "category": "PS_SERIES",
      "base_price_per_hour": 30000.0,
      "similarity_score": null,
      "final_score": 0.78,
      "reason": "Trending: Frequently booked this week"
    }
  ],
  "is_cold_start": true,
  "user_event_count": 0
}
```

**Response (Personalized - Active User):**

```json
{
  "recommendations": [
    {
      "id": "room-uuid-1",
      "name": "VIP Room 2",
      "description": "VIP room similar to your preferences",
      "category": "VIP",
      "base_price_per_hour": 55000.0,
      "similarity_score": 0.92,
      "final_score": 0.88,
      "reason": "Similar to rooms you've booked"
    },
    {
      "id": "room-uuid-3",
      "name": "VIP Room 1",
      "description": "Premium VIP room",
      "category": "VIP",
      "base_price_per_hour": 50000.0,
      "similarity_score": 0.87,
      "final_score": 0.82,
      "reason": "Matches your VIP room preferences"
    }
  ],
  "is_cold_start": false,
  "user_event_count": 15
}
```

#### Log User Event

```bash
curl -X POST http://localhost:8000/api/ai/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "room-uuid",
    "event_type": "VIEW_ROOM"
  }'
```

**Event Types:**

- `VIEW_ROOM` - User viewed room details
- `CLICK_ROOM` - User clicked on room card
- `BOOK_ROOM` - User booked the room
- `RATE_ROOM` - User rated the room (include `rating_value`)
- `SEARCH` - User searched (include `search_query`)

---

### Reviews

#### Submit Review

```bash
curl -X POST http://localhost:8000/api/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_id": "res-uuid",
    "rating": 5,
    "comment": "Amazing experience! The VIP room was fantastic."
  }'
```

**Response:**

```json
{
  "id": "review-uuid",
  "user_id": "user-uuid",
  "room_id": "room-uuid",
  "reservation_id": "res-uuid",
  "rating": 5,
  "comment": "Amazing experience! The VIP room was fantastic.",
  "created_at": "2024-01-21T10:00:00Z"
}
```

#### Get Room Reviews

```bash
curl http://localhost:8000/api/rooms/room-uuid/reviews
```

---

### Admin Routes

#### Dashboard Stats

```bash
curl http://localhost:8000/api/admin/stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response:**

```json
{
  "total_users": 150,
  "total_reservations": 523,
  "revenue_today": 2500000.0,
  "revenue_this_month": 45000000.0,
  "pending_payments": 12,
  "active_reservations": 8
}
```

#### Get All Users (Admin)

```bash
curl http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Create Room (Admin)

```bash
curl -X POST http://localhost:8000/api/admin/rooms \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New VIP Room",
    "description": "Brand new VIP experience",
    "category": "VIP",
    "capacity": 8,
    "base_price_per_hour": 60000,
    "status": "ACTIVE"
  }'
```

---

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_availability.py -v
pytest tests/test_payment.py -v
pytest tests/test_ai.py -v
```

### Test Coverage

1. **Availability Tests** (`test_availability.py`)

   - Overlap detection for room bookings
   - Edge cases: adjacent slots, same time, partial overlaps

2. **Payment Tests** (`test_payment.py`)

   - Payment confirmation updates reservation status
   - Payment rejection handling
   - Role-based access control

3. **AI Tests** (`test_ai.py`)
   - Cold start returns trending rooms
   - FakeEmbeddingProvider determinism
   - Personalized recommendations

---

## Evaluating AI Recommendations

```bash
python scripts/evaluate_recommender.py
```

**Output:**

```
=== AI Recommender Evaluation ===

Metrics:
- HitRate@8: 0.75
- MRR@8: 0.583

Cold Start Test: PASSED
Determinism Test: PASSED
```

---

## AI Recommendation Algorithm

### Scoring Formula

```
final_score = 0.65 * similarity + 0.10 * rating_norm + 0.10 * popularity_norm + 0.10 * price_match + 0.05 * freshness
```

### Components

| Component   | Weight | Description                                                |
| ----------- | ------ | ---------------------------------------------------------- |
| Similarity  | 0.65   | Cosine similarity between user profile and room embeddings |
| Rating      | 0.10   | Normalized average rating (0-1)                            |
| Popularity  | 0.10   | Normalized booking count in last 30 days                   |
| Price Match | 0.10   | How close room price is to user's average booking price    |
| Freshness   | 0.05   | Recency of room data (newer rooms get slight boost)        |

### Cold Start Handling

When a user has fewer than 3 events:

1. Returns **trending rooms** instead of personalized recommendations
2. Trending = most booked in last 30 days + highest rated
3. Response includes `is_cold_start: true`

---

## Project Structure

```
biggames_backend/
├── alembic/                 # Database migrations
│   └── versions/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── core/                # Config, security
│   ├── db/                  # Database session
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── main.py              # FastAPI app
├── scripts/
│   ├── seed_demo_data.py    # Demo data seeder
│   └── evaluate_recommender.py
├── tests/
│   ├── conftest.py
│   ├── test_availability.py
│   ├── test_payment.py
│   └── test_ai.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## License

MIT License - BIG GAMES Indonesia 2024
