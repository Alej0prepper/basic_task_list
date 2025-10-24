from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import FastAPI, Depends, Query, HTTPException
from typing import Optional, List
from sqlalchemy.orm import Session
from pathlib import Path
from typing import TypedDict, List
# --- SQLAdmin Panel ---
from sqladmin import Admin, ModelView
from .database import engine
from .models import Task

from . import crud, schemas
from .database import SessionLocal
from .settings import settings
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Tasklist API")

# CORS
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# DB dep
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# UI estática (/app)
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

@app.get("/app")
def app_page():
    return FileResponse(WEB_DIR / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

# --------- Endpoints API de lista/paginación ----------
@app.get("/tasks", response_model=schemas.PageTasks)
def list_tasks(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[schemas.TaskStatus] = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
):
    # VALIDACIÓN MANUAL (evita incompatibilidades de Query/regex)
    if order_by not in ("created_at", "updated_at"):
        raise HTTPException(status_code=400, detail="order_by must be 'created_at' or 'updated_at'")
    if order_dir not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="order_dir must be 'asc' or 'desc'")

    items, total = crud.list_tasks(
        db, limit=limit, offset=offset, status=status,
        order_by=order_by, order_dir=order_dir
    )
    return schemas.PageTasks(
        items=items,
        meta=schemas.PageMeta(total=total, limit=limit, offset=offset)
    )

# --------- Endpoint “robusto” para la UI (JSON plano) ----------
class TaskUI(TypedDict):
    id: int
    text: str
    status: str
    tags: List[str]
    created_at: str
    updated_at: str

def _to_ui_dict(t) -> TaskUI:
    return {
        "id": t.id,
        "text": t.text,
        "status": t.status,
        "tags": list(t.tags or []),
        "created_at": t.created_at.isoformat() if getattr(t, "created_at", None) else "",
        "updated_at": t.updated_at.isoformat() if getattr(t, "updated_at", None) else "",
    }

@app.get("/tasks/ui")
def list_tasks_ui(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[schemas.TaskStatus] = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
):
    if order_by not in ("created_at", "updated_at"):
        raise HTTPException(status_code=400, detail="order_by must be 'created_at' or 'updated_at'")
    if order_dir not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="order_dir must be 'asc' or 'desc'")

    items, total = crud.list_tasks(
        db, limit=limit, offset=offset, status=status,
        order_by=order_by, order_dir=order_dir
    )
    def _to_ui_dict(t):
        return {
            "id": t.id,
            "text": t.text,
            "status": t.status,
            "tags": list(t.tags or []),
            "created_at": t.created_at.isoformat() if getattr(t, "created_at", None) else "",
            "updated_at": t.updated_at.isoformat() if getattr(t, "updated_at", None) else "",
        }
    return {"items": [_to_ui_dict(t) for t in items],
            "meta": {"total": total, "limit": limit, "offset": offset}}

# --------- CRUD por id ----------
@app.post("/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)

@app.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    t = crud.get_task(db, task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    return t

@app.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, patch: schemas.TaskUpdate, db: Session = Depends(get_db)):
    t = crud.update_task(db, task_id, patch)
    if not t:
        raise HTTPException(404, "Task not found")
    return t

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_task(db, task_id)
    if not ok:
        raise HTTPException(404, "Task not found")
    return

@app.get("/tasks/listonly", response_model=List[schemas.TaskOut])
def list_tasks_listonly(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[schemas.TaskStatus] = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
):
    if order_by not in ("created_at", "updated_at"):
        raise HTTPException(status_code=400, detail="order_by must be 'created_at' or 'updated_at'")
    if order_dir not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="order_dir must be 'asc' or 'desc'")

    items, _ = crud.list_tasks(
        db, limit=limit, offset=offset, status=status,
        order_by=order_by, order_dir=order_dir
    )
    return items

admin = Admin(app, engine)

# Define cómo se muestra el modelo en el panel
class TaskAdmin(ModelView, model=Task):
    name = "Task"
    name_plural = "Tasks"
    icon = "fa-solid fa-list-check"

    column_list = [
        Task.id,
        Task.text,
        Task.status,
        Task.tags,
        Task.created_at,
        Task.updated_at,
    ]
    column_sortable_list = [Task.id, Task.created_at, Task.updated_at]
    column_searchable_list = [Task.text, Task.status]
    column_default_sort = ("created_at", True)

# Agrega la vista al panel
admin.add_view(TaskAdmin)