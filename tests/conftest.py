import os
import sys
import pathlib
import tempfile
import pytest

# --- Asegurar ruta del proyecto antes de importar la app ---
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Usamos SQLite en disco temporal (estable entre hilos del TestClient)
TEST_DIR = tempfile.mkdtemp(prefix="tasklist_tests_")
DB_PATH = pathlib.Path(TEST_DIR) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from tasklist_app.database import Base
from tasklist_app import models
from tasklist_app.main import app
from tasklist_app import deps

# Creamos un engine y SessionLocal específicos para los tests
engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def _schema():
    """
    Crea el esquema al iniciar la sesión de tests y lo elimina al final.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db() -> Session:
    """
    Sesión de BD por test.
    """
    s = TestingSessionLocal()
    try:
        yield s
    finally:
        s.close()


import uuid

@pytest.fixture()
def test_user(db: Session) -> models.User:
    email = f"tester_{uuid.uuid4().hex[:8]}@example.com"
    u = models.User(email=email, password_hash="hash-no-usado")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

@pytest.fixture()
def client(db: Session, test_user: models.User):
    """
    TestClient con overrides:
      - get_db -> usa la sesión de pruebas
      - get_current_user / get_current_user_optional -> devuelve test_user
    """
    def _get_db():
        try:
            yield db
        finally:
            pass

    def _get_current_user():
        return test_user

    def _get_current_user_optional():
        return test_user

    # Overrides de dependencias
    app.dependency_overrides[deps.get_db] = _get_db
    # Si tu módulo deps tiene solo una de estas, la otra override no molesta
    app.dependency_overrides[getattr(deps, "get_current_user", _get_current_user)] = _get_current_user
    app.dependency_overrides[getattr(deps, "get_current_user_optional", _get_current_user_optional)] = _get_current_user_optional

    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c

    # Limpieza overrides
    app.dependency_overrides.clear()

@pytest.fixture()
def api_create(client):
    """
    Helper para crear tareas en tests de forma concisa.
    """
    def _make(text: str, status: str = "pending"):
        r = client.post("/tasks", json={"text": text, "status": status})
        assert r.status_code == 201, r.text
        return r.json()
    return _make
