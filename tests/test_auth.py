# asyncio_mode=auto（见 pyproject）：async 测试无需显式标记


async def test_register_returns_user(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "supersecret"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["is_active"] is True
    assert "id" in body


async def test_register_duplicate_email_conflicts(client):
    payload = {"email": "dup@example.com", "password": "supersecret"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


async def test_login_returns_token_and_grants_access(client):
    email, password = "bob@example.com", "supersecret"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me = await client.get("/api/v1/links", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json() == []


async def test_login_wrong_password_unauthorized(client):
    email = "carol@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret"})
    resp = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": "wrongpass"}
    )
    assert resp.status_code == 401


async def test_protected_route_without_token_unauthorized(client):
    resp = await client.get("/api/v1/links")
    assert resp.status_code == 401
