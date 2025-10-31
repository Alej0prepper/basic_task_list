"""Application settings using pydantic-settings.

Loads configuration from environment variables or a `.env` file.
Includes database URL, JWT configuration, and CORS origins.
"""

from __future__ import annotations

import json
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    DATABASE_URL: str

    # --- App / JWT ---
    SECRET_KEY: str = Field(default="change_me")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # --- CORS ---
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # --- Optional ---
    APP_ENV: Optional[str] = Field(default="prod")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        """Parse CORS origins from JSON or comma-separated list."""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            if s.startswith("["):
                try:
                    return json.loads(s)
                except json.JSONDecodeError:
                    raise ValueError(
                        "CORS_ORIGINS must be valid JSON or a comma-separated list."
                    )
            return [part.strip() for part in s.split(",") if part.strip()]
        return v


settings = Settings()
