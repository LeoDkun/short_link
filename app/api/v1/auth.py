"""
认证模块 API 接口

提供用户注册和登录功能：
- POST /auth/register - 用户注册
- POST /auth/login - 用户登录（OAuth2 标准）
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession, enforce_rate_limit, get_auth_service
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserOut
from app.services.auth import AuthService, EmailAlreadyExists, InvalidCredentials

# 创建认证路由器，所有路由自动添加 /auth 前缀
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit)],  # 应用限流保护，防止恶意注册
)
async def register(
    payload: UserCreate,  # 从请求体中解析注册数据（email + password）
    service: Annotated[AuthService, Depends(get_auth_service)],  # 依赖注入：获取认证服务实例
    db: DbSession,  # 依赖注入：数据库会话
) -> UserOut:
    """
    用户注册接口
    
    Args:
        payload: 用户注册信息（邮箱和密码）
        service: 认证服务实例
        db: 数据库会话
        
    Returns:
        UserOut: 创建成功的用户信息（不包含密码）
        
    Raises:
        HTTPException 409: 邮箱已被注册
    """
    try:
        # 调用业务层创建用户（此时用户尚未提交到数据库）
        user = await service.register(payload.email, payload.password)
    except EmailAlreadyExists:
        # 邮箱已存在，返回冲突错误
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from None
    
    # 提交数据库事务，持久化用户数据
    await db.commit()
    
    # 将用户对象转换为响应模型并返回
    return UserOut.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(enforce_rate_limit)],  # 应用限流保护，防止暴力破解
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],  # OAuth2 标准登录表单（username + password）
    service: Annotated[AuthService, Depends(get_auth_service)],  # 依赖注入：获取认证服务实例
) -> Token:
    """
    用户登录接口（OAuth2 标准）
    
    Args:
        form: OAuth2 登录表单，包含 username（邮箱）和 password
        service: 认证服务实例
        
    Returns:
        Token: JWT 访问令牌
        
    Raises:
        HTTPException 401: 用户名或密码错误
    """
    try:
        # 验证用户凭证，成功则生成 JWT token
        token = await service.authenticate(form.username, form.password)
    except InvalidCredentials:
        # 凭证无效，返回未授权错误
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},  # 标准的 OAuth2 响应头
        ) from None
    
    # 返回 JWT token
    return Token(access_token=token)
