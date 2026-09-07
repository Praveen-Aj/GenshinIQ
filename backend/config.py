"""Configuration management for GenshinIQ using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    APP_NAME: str = "GenshinIQ"
    APP_VERSION: str = "0.3.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # User Genshin UID
    USER_UID: Optional[str] = Field(default="817739968", description="Default user Genshin Impact UID")

    # LLM Settings
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Gemini API Key")

    # Enka Integration Settings
    ENKA_API_BASE_URL: str = "https://enka.network/api"
    ENKA_CACHE_TTL_SECONDS: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
