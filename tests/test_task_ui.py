def test_ui_endpoint_json_shape(client):
    # Crea un par de tareas para tener datos
    client.post("/tasks", json={"text": "a @m", "status": "pending"})
    client.post("/tasks", json={"text": "b #x", "status": "done"})

    # Nueva ruta: /tasks-ui  (antes era /tasks/ui)
    r = client.get("/tasks-ui?limit=5&offset=0&sort=date&dir=desc")
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(data.keys()) == {"items", "meta"}
    assert {"total", "limit", "offset"} <= set(data["meta"].keys())
    assert isinstance(data["items"], list)


def test_ui_endpoint_filters(client):
    # Semilla simple
    client.post("/tasks", json={"text": "c1", "status": "pending"})
    client.post("/tasks", json={"text": "c2", "status": "done"})

    # Filtro por status usando la nueva ruta
    r = client.get("/tasks-ui?status=pending&limit=50&offset=0")
    assert r.status_code == 200, r.text
    items = r.json().get("items", [])
    # Todas las devueltas deberían ser 'pending'
    assert all((it.get("status") or "").lower() == "pending" for it in items)
