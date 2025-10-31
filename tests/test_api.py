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

import json

def _body_text(resp):
    try:
        return json.dumps(resp.json(), ensure_ascii=False)
    except Exception:
        return resp.text

def test_crud_flow(client):
    # 1) CREATE
    payload = {
        "text":"algo @dev #tag someone@gmail.com https://example.com",
        "status":"pending"
    }
    r = client.post("/tasks", json=payload)
    assert r.status_code == 201, f"[POST /tasks] esperado 201, recibido {r.status_code}. Body: {_body_text(r)}"

    t = r.json()
    assert "tags" in t, f"[POST /tasks] 'tags' no está en la respuesta. Body: {json.dumps(t, ensure_ascii=False)}"
    assert isinstance(t["tags"], list), f"[POST /tasks] 'tags' no es lista: {type(t['tags'])}. Body: {json.dumps(t, ensure_ascii=False)}"
    assert len(t["tags"]) >= 3, f"[POST /tasks] se esperaban >=3 tags, recibido {len(t['tags'])}. Body: {json.dumps(t, ensure_ascii=False)}"

    tid = t.get("id")
    assert isinstance(tid, int), f"[POST /tasks] 'id' no es int: {tid!r}. Body: {json.dumps(t, ensure_ascii=False)}"

    # 2) READ by id
    r = client.get(f"/tasks/{tid}")
    assert r.status_code == 200, f"[GET /tasks/{tid}] esperado 200, recibido {r.status_code}. Body: {_body_text(r)}"

    # 3) UPDATE
    upd = {"text":"nuevo #x","status":"done"}
    r = client.put(f"/tasks/{tid}", json=upd)
    assert r.status_code == 200, f"[PUT /tasks/{tid}] esperado 200, recibido {r.status_code}. Body: {_body_text(r)}"
    jr = r.json()
    assert "#x" in jr.get("tags", []), f"[PUT /tasks/{tid}] '#x' no aparece en tags. Body: {json.dumps(jr, ensure_ascii=False)}"

    # 4) LIST (acepta lista plana o paginado {items, meta})
    r = client.get("/tasks")
    assert r.status_code == 200, f"[GET /tasks] esperado 200, recibido {r.status_code}. Body: {_body_text(r)}"

    try:
        body = r.json()
    except Exception:
        assert False, f"[GET /tasks] respuesta no es JSON. Texto: {r.text}"

    if isinstance(body, list):
        # lista plana
        assert any(x.get("id") == tid for x in body), (
            f"[GET /tasks] no se encontró id={tid} en lista plana. Body: {json.dumps(body, ensure_ascii=False)[:800]}"
        )
    elif isinstance(body, dict):
        # objeto paginado
        assert "items" in body, f"[GET /tasks] falta 'items' en objeto paginado. Body: {json.dumps(body, ensure_ascii=False)}"
        items = body["items"]
        assert isinstance(items, list), f"[GET /tasks] 'items' no es lista. Body: {json.dumps(body, ensure_ascii=False)}"
        assert any(x.get("id") == tid for x in items), (
            f"[GET /tasks] no se encontró id={tid} en 'items'. Body: {json.dumps(body, ensure_ascii=False)[:800]}"
        )
    else:
        assert False, f"[GET /tasks] forma inesperada: {type(body)}. Body: {json.dumps(body, ensure_ascii=False)}"

    # 5) DELETE
    r = client.delete(f"/tasks/{tid}")
    assert r.status_code == 204, f"[DELETE /tasks/{tid}] esperado 204, recibido {r.status_code}. Body: {_body_text(r)}"

    # 6) READ de nuevo debe ser 404
    r = client.get(f"/tasks/{tid}")
    assert r.status_code == 404, f"[GET /tasks/{tid}] después de borrar, esperado 404, recibido {r.status_code}. Body: {_body_text(r)}"
