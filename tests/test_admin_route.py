def test_admin_route_exists(client):
    r = client.get("/admin")
    # sqladmin puede responder 200 o redirect inicial, pero no debe ser 404
    assert r.status_code in (200, 302, 307)
