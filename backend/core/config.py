"""
Backend configuration

Configuration settings for the FastAPI backend.
"""

import os
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class BackendConfig(BaseSettings):
    """
    Backend configuration settings

    Loaded from environment variables with defaults.
    """
    model_config = ConfigDict(
        extra='ignore',
        env_file='.env',
        case_sensitive=False
    )

    # API Settings
    api_title: str = "StoryBox API"
    api_version: str = "0.4.0"
    api_description: str = "AI-powered story generation API"
    api_prefix: str = "/api/v1"

    # Server Settings
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    reload: bool = Field(default=False, env="API_RELOAD")
    workers: int = Field(default=1, env="API_WORKERS")

    # CORS Settings
    cors_origins: list = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]

    # Security Settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = Field(default=60, env="JWT_EXPIRATION_MINUTES")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=10, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds

    # Database (for future V1.0)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")

    # Redis (for rate limiting and caching)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")


# Global config instance
settings = BackendConfig()
