from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .settings import settings
from . import models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _extract_token_from_request(request: Request, authorization: Optional[str]) -> Optional[str]:
    # 1) Authorization header: "Bearer <token>"
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()
    # 2) Cookie HttpOnly: access_token (puede venir con o sin "Bearer ")
    cookie_val = request.cookies.get("access_token")
    if cookie_val:
        if cookie_val.startswith("Bearer "):
            return cookie_val.split(" ", 1)[1].strip()
        return cookie_val.strip()
    return None

from jose import jwt, JWTError, ExpiredSignatureError

def _decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except ExpiredSignatureError:
        # token expirado
        return None
    except JWTError:
        return None

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
) -> models.User:
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
    token = _extract_token_from_request(request, authorization)
    if not token:
        return None
    email = _decode_token(token)
    if not email:
        return None
    return db.query(models.User).filter(models.User.email == email).first()
