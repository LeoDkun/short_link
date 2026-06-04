from tests.conftest import register_and_login


async def _auth_headers(client) -> dict[str, str]:
    token = await register_and_login(client, "owner@example.com", "supersecret")
    return {"Authorization": f"Bearer {token}"}


async def test_create_link_generates_code_and_short_url(client):
    headers = await _auth_headers(client)
    resp = await client.post(
        "/api/v1/links", json={"target_url": "https://example.com/page"}, headers=headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"]
    assert body["short_url"].endswith(body["code"])
    assert body["click_count"] == 0


async def test_create_link_with_custom_alias(client):
    headers = await _auth_headers(client)
    resp = await client.post(
        "/api/v1/links",
        json={"target_url": "https://example.com", "custom_alias": "mylink"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "mylink"


async def test_duplicate_alias_conflicts(client):
    headers = await _auth_headers(client)
    payload = {"target_url": "https://example.com", "custom_alias": "dupalias"}
    await client.post("/api/v1/links", json=payload, headers=headers)
    resp = await client.post("/api/v1/links", json=payload, headers=headers)
    assert resp.status_code == 409


async def test_list_and_get_link(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/links", json={"target_url": "https://example.com"}, headers=headers
    )
    code = created.json()["code"]

    listing = await client.get("/api/v1/links", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    fetched = await client.get(f"/api/v1/links/{code}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["code"] == code


async def test_update_link(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/links", json={"target_url": "https://old.example.com"}, headers=headers
    )
    code = created.json()["code"]

    resp = await client.patch(
        f"/api/v1/links/{code}",
        json={"target_url": "https://new.example.com/", "is_active": False},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["target_url"] == "https://new.example.com/"
    assert resp.json()["is_active"] is False


async def test_delete_link(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/links", json={"target_url": "https://example.com"}, headers=headers
    )
    code = created.json()["code"]

    deleted = await client.delete(f"/api/v1/links/{code}", headers=headers)
    assert deleted.status_code == 204

    missing = await client.get(f"/api/v1/links/{code}", headers=headers)
    assert missing.status_code == 404


async def test_invalid_url_rejected(client):
    headers = await _auth_headers(client)
    resp = await client.post("/api/v1/links", json={"target_url": "not-a-url"}, headers=headers)
    assert resp.status_code == 422
