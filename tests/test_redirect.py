from tests.conftest import register_and_login


async def _make_link(client, target="https://example.com/dest") -> tuple[str, dict]:
    token = await register_and_login(client, "redir@example.com", "supersecret")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/v1/links", json={"target_url": target}, headers=headers)
    return resp.json()["code"], headers


async def test_redirect_returns_307_and_records_click(client):
    code, headers = await _make_link(client)

    resp = await client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com/dest"

    # 后台埋点在 ASGITransport 下会在响应返回前完成 -> 计数确定可断言
    analytics = await client.get(f"/api/v1/links/{code}/analytics", headers=headers)
    assert analytics.status_code == 200
    assert analytics.json()["total_clicks"] == 1


async def test_redirect_unknown_code_404(client):
    resp = await client.get("/nonexistent", follow_redirects=False)
    assert resp.status_code == 404


async def test_redirect_populates_cache(client, fake_redis):
    code, _ = await _make_link(client)
    assert await fake_redis.get(f"link:{code}") is None
    await client.get(f"/{code}", follow_redirects=False)
    # cache-aside：解析后目标 URL 应已写入缓存
    assert await fake_redis.get(f"link:{code}") == "https://example.com/dest"


async def test_cache_invalidated_after_update(client, fake_redis):
    code, headers = await _make_link(client)
    await client.get(f"/{code}", follow_redirects=False)  # 预热缓存
    assert await fake_redis.get(f"link:{code}") is not None

    await client.patch(
        f"/api/v1/links/{code}",
        json={"target_url": "https://example.com/changed"},
        headers=headers,
    )
    # 更新后缓存被失效
    assert await fake_redis.get(f"link:{code}") is None

    resp = await client.get(f"/{code}", follow_redirects=False)
    assert resp.headers["location"] == "https://example.com/changed"
