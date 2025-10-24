import os
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from fastapi.testclient import TestClient
from tasklist_app.main import app
from tasklist_app.database import Base, engine

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_crud_flow():
    payload = {"text":"algo @dev #tag someone@gmail.com https://example.com","status":"pending"}
    r = client.post("/tasks", json=payload)
    assert r.status_code == 201
    t = r.json()
    assert len(t["tags"]) >= 3

    tid = t["id"]
    assert client.get(f"/tasks/{tid}").status_code == 200

    r = client.put(f"/tasks/{tid}", json={"text":"nuevo #x","status":"done"})
    assert r.status_code == 200
    assert "#x" in r.json()["tags"]

    r = client.get("/tasks")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    assert client.delete(f"/tasks/{tid}").status_code == 204
    assert client.get(f"/tasks/{tid}").status_code == 404
