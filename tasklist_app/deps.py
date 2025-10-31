"""FastAPI dependencies for DB sessions and authentication.

Provides:
- get_db: scoped SQLAlchemy session generator.
- JWT extraction/decoding helpers supporting Authorization header and HttpOnly cookie.
- get_current_user / get_current_user_optional: user resolvers for protected routes.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Header, Request, status
from jose import JWTError, ExpiredSignatureError, jwt
from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal
from .settings import settings


def get_db():
    """Yield a SQLAlchemy session and ensure it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_token_from_request(request: Request, authorization: Optional[str]) -> Optional[str]:
    """Extract a bearer token from the Authorization header or the auth cookie."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()
    cookie_val = request.cookies.get("access_token")
    if cookie_val:
        if cookie_val.startswith("Bearer "):
            return cookie_val.split(" ", 1)[1].strip()
        return cookie_val.strip()
    return None


def _decode_token(token: str) -> str | None:
    """Decode a JWT and return the subject (email) or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
) -> models.User:
    """Require a valid token and return the authenticated user; raise 401 otherwise."""
    token = _extract_token_from_request(request, authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    email = _decode_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
) -> Optional[models.User]:
    """Return the authenticated user if a valid token exists; otherwise None."""
    token = _extract_token_from_request(request, authorization)
    if not token:
        return None
    email = _decode_token(token)
    if not email:
        return None
    return db.query(models.User).filter(models.User.email == email).first()
