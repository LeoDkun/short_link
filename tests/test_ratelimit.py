from app.api import deps
from app.services.ratelimit import RateLimiter


async def test_sliding_window_blocks_after_limit(fake_redis):
    limiter = RateLimiter(fake_redis, limit=3, window=60)
    results = [await limiter.hit("user:1") for _ in range(4)]
    allowed_flags = [allowed for allowed, _ in results]
    # 前 3 次放行，第 4 次拒绝
    assert allowed_flags == [True, True, True, False]


async def test_rate_limited_endpoint_returns_429(client, fake_redis):
    # 把限流阈值调到 2，第 3 次请求应被限流
    call_count = [0]  # 使用列表以在闭包中修改

    async def override_get_rate_limiter():
        call_count[0] += 1
        limiter = RateLimiter(fake_redis, limit=2, window=60)
        print(f"DEBUG: get_rate_limiter called {call_count[0]} times")
        print(f"DEBUG: Created RateLimiter with limit={limiter.limit}, window={limiter.window}")
        return limiter

    # 通过 client.app 访问 FastAPI 应用实例并设置依赖覆盖
    client.app.dependency_overrides[deps.get_rate_limiter] = override_get_rate_limiter

    statuses = []
    for i in range(3):
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "x@example.com", "password": "whatever"},
        )
        statuses.append(resp.status_code)
        print(f"DEBUG: Request {i + 1} - Status: {resp.status_code}")

    print(f"DEBUG: All statuses: {statuses}")
    print(f"DEBUG: get_rate_limiter was called {call_count[0]} times")

    # 直接测试限流器看看是否正常工作
    limiter = RateLimiter(fake_redis, limit=2, window=60)
    r1 = await limiter.hit("test:/api/v1/auth/login:127.0.0.1")
    r2 = await limiter.hit("test:/api/v1/auth/login:127.0.0.1")
    r3 = await limiter.hit("test:/api/v1/auth/login:127.0.0.1")
    print(f"DEBUG: Direct limiter test - r1={r1}, r2={r2}, r3={r3}")

    assert statuses[-1] == 429
    assert 429 not in statuses[:2]
