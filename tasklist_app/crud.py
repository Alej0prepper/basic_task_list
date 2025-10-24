from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, utils
from .schemas import TaskCreate, TaskUpdate, TaskStatus

def list_tasks(
    db: Session,
    *,
    limit: int = 20,
    offset: int = 0,
    status: TaskStatus | None = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
):
    q = db.query(models.Task)
    if status:
        q = q.filter(models.Task.status == status.value)

    total_q = db.query(func.count(models.Task.id))
    if status:
        total_q = total_q.filter(models.Task.status == status.value)
    total = total_q.scalar()

    order_col = models.Task.created_at if order_by == "created_at" else models.Task.updated_at
    q = q.order_by(order_col.asc() if order_dir.lower() == "asc" else order_col.desc())

    items = q.offset(offset).limit(limit).all()
    return items, total


def create_task(db: Session, task_in: TaskCreate):
    tags = utils.extract_tags(task_in.text)
    obj = models.Task(text=task_in.text, status=task_in.status.value, tags=tags)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_task(db: Session, task_id: int):
    return db.query(models.Task).get(task_id)


def update_task(db: Session, task_id: int, patch: TaskUpdate):
    obj = db.query(models.Task).get(task_id)
    if not obj:
        return None
    if patch.text is not None:
        obj.text = patch.text
        obj.tags = utils.extract_tags(patch.text)
    if patch.status is not None:
        obj.status = patch.status.value
    db.commit()
    db.refresh(obj)
    return obj


def delete_task(db: Session, task_id: int):
    obj = db.query(models.Task).get(task_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
