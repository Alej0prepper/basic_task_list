"""Pydantic schemas for users, authentication, and tasks.

These classes define request and response models used by the FastAPI endpoints:
- UserBase / UserCreate / UserOut
- Token / TokenData
- TaskBase / TaskCreate / TaskUpdate / TaskOut
- PageMeta / PageTasks
"""

from datetime import datetime
from typing import Optional, Literal, List

from pydantic import BaseModel, EmailStr, Field


# ---------- Users ----------
class UserBase(BaseModel):
    """Base user fields shared across schemas."""
    email: EmailStr


class UserCreate(UserBase):
    """Payload for creating a new user."""
    password: str = Field(min_length=6, max_length=128)


class UserOut(UserBase):
    """Public representation of a user."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Auth ----------
class Token(BaseModel):
    """Bearer token returned after successful authentication."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token data containing the subject (email)."""
    sub: EmailStr | None = None


# ---------- Tasks ----------
TaskStatus = Literal["pending", "done"]


class TaskBase(BaseModel):
    """Base fields for creating or updating tasks."""
    text: str = Field(min_length=1, max_length=10_000)
    status: TaskStatus = "pending"


class TaskCreate(TaskBase):
    """Payload for creating a task."""
    pass


class TaskUpdate(TaskBase):
    """Payload for updating a task."""
    pass


class TaskOut(BaseModel):
    """Representation of a task returned by the API."""
    id: int
    text: str
    status: TaskStatus
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Pagination ----------
class PageMeta(BaseModel):
    """Pagination metadata."""
    total: int
    limit: int
    offset: int


class PageTasks(BaseModel):
    """Paginated list of tasks with metadata."""
    items: list[TaskOut]
    meta: PageMeta
