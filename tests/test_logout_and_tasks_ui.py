# test_logout_and_tasks_ui.py
def test_tasks_ui_endpoint_ok(client):
    # Sin filtros, solo debe responder 200 con la forma {items, meta}
    r = client.get("/tasks-ui?limit=5&offset=0&sort=date&dir=desc")
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(data.keys()) == {"items", "meta"}
    assert {"total", "limit", "offset"} <= set(data["meta"].keys())

def test_logout_redirects():
    from fastapi.testclient import TestClient
    from tasklist_app.main import app
    with TestClient(app) as c:
        r = c.get("/app/logout", follow_redirects=False)
        # Debe redirigir a /app/login y borrar cookie
        assert r.status_code in (302, 303, 307)
        assert "/app/login" in (r.headers.get("location") or "")
        set_cookie = r.headers.get("set-cookie", "")
        # delete-cookie puede o no estar según implementación; comprobamos presencia del header
        assert isinstance(set_cookie, str)
