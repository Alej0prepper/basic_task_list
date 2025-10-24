from __future__ import annotations

from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from pydantic import BaseModel, Field, ConfigDict, field_validator  


# -----------------------------
# Tipos / Validaciones de dominio
# -----------------------------

class TaskStatus(str, Enum):
    pending = "pending"
    done = "done"


class TaskBase(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    status: TaskStatus = TaskStatus.pending


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    text: Optional[str] = None
    status: Optional[TaskStatus] = None


class TaskOut(BaseModel):
    id: int
    text: str
    status: TaskStatus
    tags: List[str] = Field(default_factory=list)   # <-- default si falta
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    # <-- NORMALIZA None -> []
    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v):
        return v or []
# -----------------------------
# Paginación (para GET /tasks)
# -----------------------------

class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class PageTasks(BaseModel):
    items: List[TaskOut]
    meta: PageMeta
