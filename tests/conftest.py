# ruff: noqa: E402  顶部需先设置环境变量，再导入 app（engine 在导入时创建）
import os

# 测试默认用内存 SQLite + fakeredis，免任何外部服务。
# 必须在导入任何 app 模块之前设置（session.py 在导入时即创建 engine）。
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

from collections.abc import AsyncGenerator

import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  确保模型在 create_all 前已注册
from app.api import deps
from app.db.base import Base
from app.db.redis import get_redis
from app.db.session import get_db
from app.main import create_app


@pytest_asyncio.fixture
async def engine():
    # 内存 SQLite + StaticPool：单连接共享，保证内存库在整个测试内持久
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def sessionmaker(engine):
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def fake_redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def client(sessionmaker, fake_redis) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db():
        async with sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def override_get_redis():
        yield fake_redis

    def override_get_sessionmaker():
        return sessionmaker

    # 用内存库 / fakeredis 覆盖生产依赖，测试无需任何外部服务
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[deps.get_sessionmaker] = override_get_sessionmaker

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 将 app 实例附加到 client 上，方便测试中设置额外的依赖覆盖
        ac.app = app
        yield ac


async def register_and_login(client: AsyncClient, email: str, password: str) -> str:
    """注册并登录，返回可用于 Authorization 头的 access token。"""
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]
