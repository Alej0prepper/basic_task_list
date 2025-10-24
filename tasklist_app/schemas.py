from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TaskBase(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    status: Optional[str] = Field(default="pending")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    text: Optional[str] = None
    status: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    text: str
    status: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
