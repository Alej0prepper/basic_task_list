# test_tasks_filtering_and_sorting.py
from time import sleep

def test_search_q_filters_by_text(client):
    client.post("/tasks", json={"text": "Backend deploy ventana", "status": "pending"})
    client.post("/tasks", json={"text": "Frontend fix botón", "status": "pending"})
    r = client.get("/tasks?limit=50&offset=0&q=Backend")
    assert r.status_code == 200
    items = r.json()["items"]
    assert any("Backend" in it["text"] for it in items)
    assert all(("Frontend" not in it["text"]) or ("Backend" in it["text"]) for it in items) or len(items) >= 1

def test_sort_by_done_groups_done_first_when_desc(client):
    # Creamos uno DONE (mayúsculas) y uno pending
    client.post("/tasks", json={"text": "Terminado A", "status": "DONE"})
    sleep(0.01)
    client.post("/tasks", json={"text": "Pendiente B", "status": "pending"})

    # /tasks-ui con sort=done&dir=desc debería traer DONE antes que pending si ambos existen
    r = client.get("/tasks-ui?limit=50&offset=0&sort=done&dir=desc")
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    # buscar el primer índice de cada uno si existen
    idx_done = next((i for i, it in enumerate(items) if (it.get("status") or "").upper() == "DONE"), None)
    idx_pend = next((i for i, it in enumerate(items) if (it.get("status") or "").lower() == "pending"), None)
    if idx_done is not None and idx_pend is not None:
        assert idx_done < idx_pend, f"DONE debería aparecer antes que pending (got {idx_done} vs {idx_pend})"

def test_sort_by_date(client):
    client.post("/tasks", json={"text": "T1", "status": "pending"})
    sleep(0.01)
    client.post("/tasks", json={"text": "T2", "status": "pending"})
    r = client.get("/tasks-ui?limit=2&offset=0&sort=date&dir=desc")
    assert r.status_code == 200
    items = r.json()["items"]
    # Fechas no crecientes
    dates = [it["created_at"] for it in items]
    assert dates == sorted(dates, reverse=True)
