from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILES = (str(_PROJECT_ROOT / ".env"), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILES, env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Kenko AI Healthcare Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://kenko:kenko@postgres:5432/kenko"
    DATABASE_URL_SYNC: str = "postgresql://kenko:kenko@postgres:5432/kenko"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # AI Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    DEFAULT_AI_PROVIDER: str = "openai"
    DEFAULT_AI_MODEL: str = "gpt-4o"

    # LINE
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # Google Calendar
    GOOGLE_CALENDAR_CREDENTIALS: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STANDARD: str = ""
    STRIPE_PRICE_PREMIUM: str = ""

    # Storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    # RAG
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Subscription
    FREE_TRIAL_DAYS: int = 7
    FRONTEND_URL: str = "http://localhost:3000"
    # Comma-separated emails that can switch plans without Stripe (testing)
    TEST_ACCOUNT_EMAILS: str = "toms90305@gmail.com"

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@kenko-ai.jp"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
