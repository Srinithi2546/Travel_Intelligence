from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
from typing import List
import os


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "SmartTravelAPI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Security ─────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-must-be-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/smart_travel"
    SYNC_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/smart_travel"

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── External APIs ────────────────────────────────────────
    OPENWEATHER_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    HOLIDAY_API_KEY: str = ""
    RAPIDAPI_KEY: str = ""

    # ── CORS ─────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # ── Cache TTL ────────────────────────────────────────────
    WEATHER_CACHE_TTL: int = 1800      # 30 minutes
    HOLIDAY_CACHE_TTL: int = 86400     # 24 hours
    ROUTE_CACHE_TTL: int = 3600        # 1 hour

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
