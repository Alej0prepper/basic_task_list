from time import sleep

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_create_get_update_delete_flow(client):
    # create
    payload = {"text": "hola @dev #tag mail@site.com https://ex.com", "status": "pending"}
    r = client.post("/tasks", json=payload)
    assert r.status_code == 201, r.text
    t = r.json()
    tid = t["id"]
    assert "@dev" in t["tags"] and "#tag" in t["tags"]
    assert "mail@site.com" in t["tags"] and "https://ex.com" in t["tags"]

    # get
    r = client.get(f"/tasks/{tid}")
    assert r.status_code == 200
    assert r.json()["id"] == tid

    # update
    r = client.put(f"/tasks/{tid}", json={"status": "done", "text": "nuevo #x"})
    assert r.status_code == 200
    t2 = r.json()
    assert t2["status"] == "done"
    assert "#x" in t2["tags"]

    # list
    r = client.get("/tasks?limit=10&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "meta" in data
    assert any(x["id"] == tid for x in data["items"])

    # delete
    r = client.delete(f"/tasks/{tid}")
    assert r.status_code == 204

    # 404s
    assert client.get(f"/tasks/{tid}").status_code == 404
    assert client.delete(f"/tasks/{tid}").status_code == 404

def test_validation_errors(client):
    # texto vacío
    assert client.post("/tasks", json={"text": ""}).status_code == 422
    # falta el campo text
    assert client.post("/tasks", json={"status": "pending"}).status_code == 422
    # status inválido
    assert client.post("/tasks", json={"text": "x", "status": "weird"}).status_code == 422

def test_large_text_boundary(client):
    big = "a" * 10_000
    r = client.post("/tasks", json={"text": big, "status": "pending"})
    assert r.status_code == 201, r.text

def test_pagination_filter_order(client):
    # Creamos varias tareas para tener orden temporal claro
    client.post("/tasks", json={"text": "A", "status": "pending"})
    client.post("/tasks", json={"text": "B", "status": "pending"})
    client.post("/tasks", json={"text": "C", "status": "DONE"})

    # Nuevo contrato: usar sort=date|done y dir=asc|desc (NO order_by/order_dir)
    r = client.get("/tasks?limit=3&offset=0&sort=date&dir=desc")
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    # debe venir de más reciente a más antiguo
    got = [it["created_at"] for it in items]
    assert got == sorted(got, reverse=True)

    # chequeo rápido del orden por 'done': DONE primero con dir=desc
    r2 = client.get("/tasks?limit=50&offset=0&sort=done&dir=desc")
    assert r2.status_code == 200, r2.text
    items2 = r2.json()["items"]
    if items2:
        first_status = (items2[0].get("status") or "").upper()
        # si hay al menos un DONE en el listado, debería aparecer primero
        if any((it.get("status") or "").upper() == "DONE" for it in items2):
            assert first_status == "DONE"

def test_update_text_recomputes_tags(client, api_create):
    t = api_create("hola #a")
    tid = t["id"]
    r = client.put(f"/tasks/{tid}", json={"text": "nuevo @x https://site.com"})
    assert r.status_code == 200
    tags = r.json()["tags"]
    assert "#a" not in tags
    assert "@x" in tags and "https://site.com" in tags
