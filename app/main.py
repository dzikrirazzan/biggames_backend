"""Main FastAPI application."""
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import (
    auth_router,
    rooms_router,
    reservations_router,
    promo_router,
    payment_router,
    menu_router,
    fb_orders_router,
    ai_router,
    admin_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for BIG GAMES PlayStation Room Rental and Food Ordering",
    version="1.0.0",
    lifespan=lifespan,
)

# Performance monitoring middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header for monitoring."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))  # ms
    
    # Log slow requests (> 1 second)
    if process_time > 1.0:
        print(f"⚠️  SLOW REQUEST: {request.method} {request.url.path} took {process_time:.2f}s")
    
    return response

# CORS middleware - Allow all origins for ngrok compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development with ngrok
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(rooms_router, prefix="/api")
app.include_router(reservations_router, prefix="/api")
app.include_router(promo_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(menu_router, prefix="/api")
app.include_router(fb_orders_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
