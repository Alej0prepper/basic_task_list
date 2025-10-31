"""CRUD helpers for users and tasks.

This module contains database operations used by the API layer:
- User helpers for registration/login flows.
- Task CRUD plus listing with ordering and pagination.
The function names, signatures, and behavior are preserved as-is.
"""

from typing import Optional, Sequence
import re
import datetime as dt

from sqlalchemy import asc, desc, case
from sqlalchemy.orm import Session

from . import models, schemas, utils


# -----------------------------------------------------------------------------
# USERS (helpers for registration/login)
# -----------------------------------------------------------------------------
def get_user_by_email(db: Session, email: str) -> models.User | None:
    """Return a user by normalized email or None if not found."""
    norm = (email or "").strip().lower()
    if not norm:
        return None
    return db.query(models.User).filter(models.User.email == norm).first()


def user_exists(db: Session, email: str) -> bool:
    """Return True if a user with the given email already exists."""
    return get_user_by_email(db, email) is not None


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    """Create a new user hashing the provided password."""
    email_norm = (user_in.email or "").strip().lower()
    user = models.User(
        email=email_norm,
        password_hash=utils.hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_handle(db: Session, handle: str) -> models.User | None:
    """Return a user by handle (email prefix before '@')."""
    norm = (handle or "").strip().lower()
    if not norm:
        return None
    return db.query(models.User).filter(models.User.email.ilike(f"{norm}@%")).first()


# -----------------------------------------------------------------------------
# TASKS
# -----------------------------------------------------------------------------
def create_task(db: Session, task_in: schemas.TaskCreate, owner_id: int) -> models.Task:
    """Create a task and replicate it to mentioned users via @handle."""
    obj = models.Task(
        text=task_in.text,
        status=task_in.status,
        tags=utils.extract_tags(task_in.text),
        owner_id=owner_id,
        created_at=dt.datetime.now(dt.timezone.utc),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)

    mention_pattern = re.compile(r"@([A-Za-z0-9._-]+)")
    handles = set(m.group(1).lower() for m in mention_pattern.finditer(task_in.text or ""))

    if handles:
        owner = db.query(models.User).filter(models.User.id == owner_id).first()
        owner_handle = (owner.email.split("@", 1)[0].lower() if owner and owner.email else "")
        for handle in handles:
            if handle == owner_handle:
                continue
            target_user = get_user_by_handle(db, handle)
            if not target_user:
                continue
            replica = models.Task(
                text=task_in.text,
                status=task_in.status,
                tags=utils.extract_tags(task_in.text),
                owner_id=target_user.id,
            )
            db.add(replica)
        db.commit()

    return obj


def get_task(db: Session, task_id: int) -> models.Task | None:
    """Return a task by its ID or None if not found."""
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def update_task(db: Session, task_id: int, task_in: schemas.TaskUpdate) -> models.Task | None:
    """Update task text, status, and tags; return the updated task or None."""
    obj = get_task(db, task_id)
    if not obj:
        return None
    obj.text = task_in.text
    obj.status = task_in.status
    obj.tags = utils.extract_tags(task_in.text)
    db.commit()
    db.refresh(obj)
    return obj


def delete_task(db: Session, task_id: int) -> bool:
    """Delete a task by ID; return True if it existed and was deleted."""
    obj = get_task(db, task_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def list_tasks_page(
    db, owner_id, limit, offset, status, order_by, order_dir, search=None
):
    """List tasks with optional filters and pagination, preserving original logic."""
    q = db.query(models.Task)

    if owner_id is not None:
        q = q.filter(models.Task.owner_id == owner_id)
    if status:
        q = q.filter(models.Task.status == status)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(models.Task.text.ilike(like))

    desc_dir = (order_dir or "").lower() == "desc"

    if (order_by or "").lower() == "done":
        is_done = case((models.Task.status == "DONE", 1), else_=0)
        primary = desc(is_done) if desc_dir else asc(is_done)
        secondary = desc(models.Task.created_at) if desc_dir else asc(models.Task.created_at)
        tertiary = desc(models.Task.id) if desc_dir else asc(models.Task.id)
        q = q.order_by(primary, secondary, tertiary)
    else:
        col = getattr(models.Task, order_by, models.Task.created_at)
        primary = desc(col) if desc_dir else asc(col)
        tertiary = desc(models.Task.id) if desc_dir else asc(models.Task.id)
        q = q.order_by(primary, tertiary)

    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return schemas.PageTasks(
        items=items,
        meta=schemas.PageMeta(total=total, limit=limit, offset=offset),
    )


def list_tasks_for_export(db, owner_id, status, order_by, order_dir, search=None):
    """Return all matching tasks for export, preserving original selection logic."""
    q = db.query(models.Task)
    desc_dir = (order_dir or "").lower() == "desc"

    if (order_by or "").lower() == "done":
        is_done = case((models.Task.status == "DONE", 1), else_=0)
        q = q.order_by(
            desc(is_done) if desc_dir else asc(is_done),
            desc(models.Task.created_at) if desc_dir else asc(models.Task.created_at),
            desc(models.Task.id) if desc_dir else asc(models.Task.id),
        )
    else:
        col = getattr(models.Task, order_by, models.Task.created_at)
        q = q.order_by(
            desc(col) if desc_dir else asc(col),
            desc(models.Task.id) if desc_dir else asc(models.Task.id),
        )
    return q.all()
