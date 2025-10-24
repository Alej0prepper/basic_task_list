from sqlalchemy.orm import Session
from . import models, schemas, utils

def list_tasks(db: Session):
    return db.query(models.Task).order_by(models.Task.created_at.desc()).all()

def create_task(db: Session, task_in: schemas.TaskCreate):
    tags = utils.extract_tags(task_in.text)
    obj = models.Task(text=task_in.text, status=task_in.status or "pending", tags=tags)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_task(db: Session, task_id: int):
    return db.get(models.Task, task_id)

def update_task(db: Session, task_id: int, task_in: schemas.TaskUpdate):
    obj = db.get(models.Task, task_id)
    if not obj:
        return None
    updated = False
    if task_in.text is not None:
        obj.text = task_in.text
        obj.tags = utils.extract_tags(task_in.text)
        updated = True
    if task_in.status is not None:
        obj.status = task_in.status
        updated = True
    if updated:
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj

def delete_task(db: Session, task_id: int) -> bool:
    obj = db.get(models.Task, task_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
