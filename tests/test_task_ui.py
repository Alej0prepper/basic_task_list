def test_ui_endpoint_json_shape(client):
    # crea dos
    client.post("/tasks", json={"text": "a @m", "status": "pending"})
    client.post("/tasks", json={"text": "b #x", "status": "done"})

    r = client.get("/tasks/ui?limit=5&offset=0&order_by=created_at&order_dir=desc")
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(data.keys()) == {"items", "meta"}
    assert isinstance(data["items"], list)
    assert {"total", "limit", "offset"} <= set(data["meta"].keys())

    # campos serializables
    it0 = data["items"][0]
    for k in ("id", "text", "status", "tags", "created_at", "updated_at"):
        assert k in it0

def test_ui_endpoint_filters(client):
    client.post("/tasks", json={"text": "c1", "status": "pending"})
    client.post("/tasks", json={"text": "c2", "status": "done"})

    r = client.get("/tasks/ui?status=pending")
    assert r.status_code == 200
    for it in r.json()["items"]:
        assert it["status"] == "pending"
