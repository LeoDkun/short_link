from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import decode_access_token
from app.db.redis import get_redis
from app.db.session import AsyncSessionLocal, get_db
from app.models.user import User
from app.repositories.link import LinkRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.links import LinkService
from app.services.ratelimit import RateLimiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_sessionmaker() -> async_sessionmaker:
    """暴露 sessionmaker 供后台任务创建独立会话；测试可覆盖为内存库。"""
    return AsyncSessionLocal


Sessionmaker = Annotated[async_sessionmaker, Depends(get_sessionmaker)]


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_link_repository(db: DbSession) -> LinkRepository:
    return LinkRepository(db)


def get_auth_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(repo)


def get_link_service(
    repo: Annotated[LinkRepository, Depends(get_link_repository)],
    redis=Depends(get_redis),
) -> LinkService:
    return LinkService(repo, redis)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exc
    except jwt.PyJWTError:
        raise credentials_exc from None
    user = await repo.get_by_id(int(subject))
    if user is None or not user.is_active:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_rate_limiter(redis=Depends(get_redis)) -> RateLimiter:
    return RateLimiter(redis)



async def enforce_rate_limit(
    request: Request,
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """应用速率限制，Redis 不可用时自动跳过（优雅降级）。"""
    try:
        identifier = request.client.host if request.client else "anonymous"
        allowed, remaining = await limiter.hit(f"{request.url.path}:{identifier}")
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(limiter.window)},
            )
    except Exception:
        # Redis 不可用时，跳过限流（开发环境友好）
        # 生产环境应该记录日志或监控此情况
        pass


