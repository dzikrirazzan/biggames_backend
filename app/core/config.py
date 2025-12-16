"""Application configuration."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "BIG GAMES Online Booking"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://biggames:biggames123@localhost:5432/biggames_db"
    DATABASE_URL_SYNC: str = "postgresql://biggames:biggames123@localhost:5432/biggames_db"
    
    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Payment Info
    QRIS_IMAGE_URL: str = "https://example.com/qris-biggames.png"
    BANK_NAME: str = "BCA"
    BANK_ACCOUNT_NUMBER: str = "1234567890"
    BANK_ACCOUNT_NAME: str = "BIG GAMES Online Booking"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
