# tasklist_app/admin_auth.py
from __future__ import annotations

import os
from typing import Optional

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from .database import SessionLocal
from . import models, utils


class AdminAuth(AuthenticationBackend):
    """
    Backend de autenticación para /admin basado en:
    - Usuarios reales de la DB (tabla User: email + password_hash)
    - Whitelist por variable de entorno ADMIN_EMAILS (coma-separada).
      Si ADMIN_EMAILS está vacía, no se permite a nadie (fail closed).
    - SessionMiddleware guarda 'admin' en la cookie de sesión.
    """

    def __init__(self, *, secret_key: str, session_key: str = "admin") -> None:
        # IMPORTANTE: AuthenticationBackend requiere secret_key
        super().__init__(secret_key=secret_key)
        self.session_key = session_key

        admins = os.getenv("ADMIN_EMAILS", "")  # "admin@foo.com,owner@bar.com"
        self.admin_emails = {e.strip().lower() for e in admins.split(",") if e.strip()}

    def _allowed(self, email: str) -> bool:
        if not self.admin_emails:
            # Sin admins configurados => nadie entra (fail closed)
            return False
        return email.lower() in self.admin_emails

    async def login(self, request: Request) -> bool:
        """
        sqladmin muestra un login form en /admin/login y POSTea aquí.
        Campos esperados: username/email + password.
        """
        form = await request.form()
        email = (form.get("username") or form.get("email") or "").strip().lower()
        password = form.get("password") or ""

        if not email or not password:
            return False

        # Busca usuario y valida contraseña
        with SessionLocal() as db:
            user: Optional[models.User] = (
                db.query(models.User).filter(models.User.email == email).first()
            )

            if not user:
                return False

            if not utils.verify_password(password, user.password_hash):
                return False

        # Revisa whitelist de ADMIN_EMAILS
        if not self._allowed(email):
            return False

        # Marca sesión autenticada
        request.session.update({self.session_key: email})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        # Permite acceso si la clave de sesión está presente
        return bool(request.session.get(self.session_key))
