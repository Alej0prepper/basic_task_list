"""Utility functions for password hashing, JWT handling, and text tag extraction."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt
from passlib.context import CryptContext

from .settings import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Patterns for detecting tags, mentions, URLs, and emails
TAG_PATTERNS = [
    r"(?<!\w)(#[\w-]+)",
    r"(?<!\w)(@[\w.-]+)",
    r"(https?://[^\s]+)",
    r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,})",
]


def extract_tags(text: str) -> list[str]:
    """Return a list of unique tags, mentions, URLs, and emails found in the text."""
    tags: list[str] = []
    for pat in TAG_PATTERNS:
        for m in re.findall(pat, text or ""):
            if m not in tags:
                tags.append(m)
    return tags


# ---------- Password hashing ----------
def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


# ---------- JWT ----------
def create_access_token(data: Dict[str, Any], expires_minutes: int | None = None) -> str:
    """Create a JWT access token with an expiration timestamp."""
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
