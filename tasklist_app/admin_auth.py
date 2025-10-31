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
    Authentication backend for the /admin UI.

    This backend validates credentials against real users stored in the database
    (email + password_hash) and enforces a whitelist via the `ADMIN_EMAILS`
    environment variable (comma-separated). If the whitelist is empty, no one is
    allowed (fail-closed). The Starlette SessionMiddleware stores the session
    under the `session_key` (default: "admin").
    """

    def __init__(self, *, secret_key: str, session_key: str = "admin") -> None:
        """Initialize the backend with the secret key and session key."""
        super().__init__(secret_key=secret_key)
        self.session_key = session_key
        admins = os.getenv("ADMIN_EMAILS", "")
        self.admin_emails = {e.strip().lower() for e in admins.split(",") if e.strip()}

    def _allowed(self, email: str) -> bool:
        """Return True if the email is present in the configured whitelist."""
        if not self.admin_emails:
            return False
        return email.lower() in self.admin_emails

    async def login(self, request: Request) -> bool:
        """
        Handle the /admin/login POST. Expects `username`/`email` and `password`.
        Returns True on successful authentication and authorization.
        """
        form = await request.form()
        email = (form.get("username") or form.get("email") or "").strip().lower()
        password = form.get("password") or ""
        if not email or not password:
            return False

        with SessionLocal() as db:
            user: Optional[models.User] = (
                db.query(models.User).filter(models.User.email == email).first()
            )
            if not user:
                return False
            if not utils.verify_password(password, user.password_hash):
                return False

        if not self._allowed(email):
            return False

        request.session.update({self.session_key: email})
        return True

    async def logout(self, request: Request) -> bool:
        """Clear the admin session and return True."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Authorize access if the admin session key is present."""
        return bool(request.session.get(self.session_key))
