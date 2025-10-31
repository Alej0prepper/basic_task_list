# test_mentions_and_tags.py
from tasklist_app import models
from sqlalchemy.orm import Session


def test_create_task_replicates_mentions_to_users(client):
    # Crea los usuarios destino de las menciones
    client.post("/auth/register", json={"email": "alice@example.com", "password": "12345678"})
    client.post("/auth/register", json={"email": "bob.builder@company.com", "password": "12345678"})

    # Crea una tarea que menciona a @alice y @bob.builder (se crea para el usuario de test)
    r = client.post("/tasks", json={"text": "revisar contrato @alice y @bob.builder #legal", "status": "pending"})
    assert r.status_code == 201, r.text

    # 1) El usuario actual ve su propia tarea
    r_cur = client.get("/tasks?limit=100&offset=0&q=revisar contrato")
    assert r_cur.status_code == 200
    assert len(r_cur.json().get("items", [])) >= 1

    # 2) Alice tiene su réplica → logueamos y pedimos con Bearer
    lr_alice = client.post("/auth/login", data={"username": "alice@example.com", "password": "12345678"})
    token_alice = lr_alice.json()["access_token"]
    r_alice = client.get(
        "/tasks?limit=100&offset=0&q=revisar contrato",
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    assert r_alice.status_code == 200
    assert len(r_alice.json().get("items", [])) >= 1

    # 3) Bob.builder también
    lr_bob = client.post("/auth/login", data={"username": "bob.builder@company.com", "password": "12345678"})
    token_bob = lr_bob.json()["access_token"]
    r_bob = client.get(
        "/tasks?limit=100&offset=0&q=revisar contrato",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert r_bob.status_code == 200
    assert len(r_bob.json().get("items", [])) >= 1

def test_extract_tags_contains_special_tokens(client):
    r = client.post(
        "/tasks",
        json={"text": "hola @dev #alfa mail@site.com https://ex.com", "status": "pending"},
    )
    assert r.status_code == 201, r.text
    tags = r.json().get("tags", [])
    # Ajusta si tu extract_tags normaliza distinto, pero en general deberían estar:
    assert "@dev" in tags
    assert "#alfa" in tags
    assert "mail@site.com" in tags
    assert "https://ex.com" in tags
