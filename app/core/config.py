"""Application configuration using Pydantic settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Spam Detection API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://spam_user:spam_pass@localhost:5432/spam_detection"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # IMAP Configuration (hardcoded for all users)
    IMAP_HOST: str = "imap.yourdomain.com"
    IMAP_PORT: int = 993
    IMAP_USE_SSL: bool = True

    # SMTP Configuration (hardcoded for all users)
    SMTP_HOST: str = "smtp.yourdomain.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True

    # Security
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Fernet encryption key for IMAP passwords (must be 32 url-safe base64-encoded bytes)
    FERNET_KEY: str = "your-fernet-key-change-this-in-production"

    # Email Monitoring
    EMAIL_CHECK_INTERVAL_SECONDS: int = 120  # Check every 2 minutes

    # ML Model Paths
    SPAM_MODEL_PATH: str = "models/spam_classifier_model.joblib"
    VECTORIZER_PATH: str = "models/tfidf_vectorizer.joblib"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars like DOCKER_CONFIG
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
