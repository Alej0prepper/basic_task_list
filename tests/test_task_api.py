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

def test_pagination_filter_order(client, api_create):
    # datos
    ids = []
    ids.append(api_create("t1 #a", "pending")["id"])
    sleep(0.01)
    ids.append(api_create("t2 #b", "done")["id"])
    sleep(0.01)
    ids.append(api_create("t3 #a", "pending")["id"])

    # paginación
    r = client.get("/tasks?limit=2&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["limit"] == 2
    assert data["meta"]["total"] >= 3
    assert len(data["items"]) <= 2

    # filtro por status
    r = client.get("/tasks?status=pending")
    assert r.status_code == 200
    for it in r.json()["items"]:
        assert it["status"] == "pending"

    # orden asc por created_at debería tener el primero más viejo
    r = client.get("/tasks?order_by=created_at&order_dir=asc&limit=3")
    assert r.status_code == 200
    arr = r.json()["items"]
    # monotonía no estricta (por si igualan): fechas no decrecientes
    dates = [it["created_at"] for it in arr]
    assert dates == sorted(dates)

def test_update_text_recomputes_tags(client, api_create):
    t = api_create("hola #a")
    tid = t["id"]
    r = client.put(f"/tasks/{tid}", json={"text": "nuevo @x https://site.com"})
    assert r.status_code == 200
    tags = r.json()["tags"]
    assert "#a" not in tags
    assert "@x" in tags and "https://site.com" in tags
