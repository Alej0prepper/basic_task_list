# tasklist_app/settings.py
from __future__ import annotations

import json
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # --- DB ---
    DATABASE_URL: str

    # --- App/JWT ---
    SECRET_KEY: str = Field(default='change_me')
    ALGORITHM: str = Field(default='HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # --- CORS ---
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # --- Otros opcionales ---
    APP_ENV: Optional[str] = Field(default='prod')

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        """
        Admite:
        - JSON: '["http://a","http://b"]'
        - Comas: 'http://a,http://b'
        - Vacío: usa default
        """
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                # vacío -> usa default del Field
                return None
            if s.startswith("["):
                # intentar JSON
                try:
                    return json.loads(s)
                except json.JSONDecodeError:
                    raise ValueError("CORS_ORIGINS debe ser JSON válido o lista separada por comas.")
            # comas
            return [part.strip() for part in s.split(",") if part.strip()]
        return v

settings = Settings()
