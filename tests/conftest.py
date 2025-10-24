# tests/conftest.py
import os, sys, pathlib, pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]  # ← raíz del repo
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from sqlalchemy.orm import Session
from tasklist_app.database import Base, engine, SessionLocal
from fastapi.testclient import TestClient
from tasklist_app.main import app

@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db() -> Session:
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def api_create(client):
    def _make(text: str, status: str = "pending"):
        r = client.post("/tasks", json={"text": text, "status": status})
        assert r.status_code == 201, r.text
        return r.json()
    return _make
