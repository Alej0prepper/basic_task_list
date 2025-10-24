# tasklist_app/settings.py
import os
from pydantic import BaseModel

class Settings(BaseModel):
    """
    Configuración central de la aplicación.
    Lee variables desde .env o el entorno del contenedor.
    """
    app_env: str = os.getenv("APP_ENV", "dev")

    # orígenes permitidos para CORS (frontend, swagger, etc.)
    cors_origins: list[str] = (
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        .split(",")
        if os.getenv("CORS_ORIGINS") else []
    )

settings = Settings()
