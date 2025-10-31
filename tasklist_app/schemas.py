from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, List

# ---------- Users ----------
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: EmailStr | None = None

# ---------- Tasks ----------
TaskStatus = Literal["pending", "done"]

class TaskBase(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    status: TaskStatus = "pending"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    pass

class TaskOut(BaseModel):
    id: int
    text: str
    status: TaskStatus
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# ---------- Paginación ----------
class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int

class PageTasks(BaseModel):
    items: list[TaskOut]
    meta: PageMeta
