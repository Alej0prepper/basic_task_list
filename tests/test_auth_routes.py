# test_auth_routes.py
import re
import json
import uuid

from fastapi.testclient import TestClient
from tasklist_app.main import app

def test_register_rejects_short_password(client):
    # password < 8 debe fallar con 422 (validación Pydantic)
    payload = {"email": f"user_{uuid.uuid4().hex[:8]}@example.com", "password": "short"}
    r = client.post("/auth/register", json=payload)
    assert r.status_code in (400, 422), f"Se esperaba 422/400, recibido {r.status_code}. Body: {r.text}"

def test_register_ok_and_login_token(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    pw = "longpass"  # 8 chars exactos
    # register
    rr = client.post("/auth/register", json={"email": email, "password": pw})
    assert rr.status_code == 201, rr.text
    assert rr.json().get("email") == email

    # login (API) via OAuth2PasswordRequestForm => form fields
    lr = client.post("/auth/login", data={"username": email, "password": pw})
    assert lr.status_code == 200, lr.text
    data = lr.json()
    assert "access_token" in data and data.get("token_type") == "bearer"

def test_app_login_sets_cookie_and_redirects():
    with TestClient(app) as c:
        email = f"web_{uuid.uuid4().hex[:8]}@example.com"
        pw = "12345678"
        # primero crear el usuario via API de registro
        rr = c.post("/auth/register", json={"email": email, "password": pw})
        assert rr.status_code == 201, rr.text

        # login de la página HTML (form-urlencoded)
        r = c.post("/app/login", data={"email": email, "password": pw}, follow_redirects=False)
        # Debe redirigir (302) y setear cookie access_token
        assert r.status_code in (302, 303, 307), r.text
        set_cookie = r.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie.lower() or "access_token=" in set_cookie, f"Set-Cookie: {set_cookie}"
