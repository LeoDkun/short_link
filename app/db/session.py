from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# 全局异步引擎。pool_pre_ping 避免连接被数据库回收后报错。
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

# expire_on_commit=False：commit 后对象属性仍可访问，便于直接序列化返回
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """请求级数据库会话依赖。提交由 service/路由显式控制。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
