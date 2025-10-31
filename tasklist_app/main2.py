from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas, crud
from .deps import get_db

app = FastAPI(title="Tasklist API (MI PROYECTO WSL)")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks", response_model=list[schemas.TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return crud.list_tasks(db)

@app.post("/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db, task)

@app.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    obj = crud.get_task(db, task_id)
    if not obj:
        raise HTTPException(404, "Task not found")
    return obj

@app.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, patch: schemas.TaskUpdate, db: Session = Depends(get_db)):
    obj = crud.update_task(db, task_id, patch)
    if not obj:
        raise HTTPException(404, "Task not found")
    return obj

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_task(db, task_id)
    if not ok:
        raise HTTPException(404, "Task not found")
    return
