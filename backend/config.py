"""Configuration management for GenshinIQ using Pydantic Settings."""

from typing import Any, Optional

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: Any) -> bool:
        """Accept common boolean aliases and IDE-injected release labels.

        Some editors and launchers inject `DEBUG=release` or similar non-boolean
        values into the process environment. We treat those as false so config
        loading remains stable and the app does not fail during import.
        """

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod", "live"}:
                return False

        raise ValueError(
            "DEBUG must be a boolean value or a known environment label such as "
            "'development' or 'release'"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
