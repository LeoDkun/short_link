# 导入异步迭代器类型注解，用于 lifespan 函数的返回类型
from collections.abc import AsyncIterator
# 导入异步上下文管理器装饰器，用于定义应用的生命周期
from contextlib import asynccontextmanager
# 导入 UUID 生成函数，用于生成唯一的请求 ID
from uuid import uuid4

# 导入结构化日志库，提供更强大的日志记录功能
import structlog
# 导入 FastAPI 核心类和 Request 对象
from fastapi import FastAPI, Request
# 导入 CORS 中间件，用于处理跨域请求
from fastapi.middleware.cors import CORSMiddleware
# 导入 JSON 响应类，用于返回自定义状态码的 JSON 数据
from fastapi.responses import HTMLResponse, JSONResponse
# 导入 SQLAlchemy 的 text 函数，用于执行原始 SQL 语句
from sqlalchemy import text

# 导入重定向路由（处理短链接跳转的核心路由）
from app.api.redirect import router as redirect_router
# 导入 API v1 版本的路由（包含认证、短链管理等接口）
from app.api.v1.router import api_router
# 导入应用配置对象，包含所有环境变量和配置项
from app.core.config import settings
# 导入静态文件和SPA路由支持
from pathlib import Path
from fastapi.staticfiles import StaticFiles
# 导入日志配置函数和日志获取函数
from app.core.logging import configure_logging, get_logger
# 导入 Redis 客户端实例，用于缓存和限流
from app.db.redis import redis_client
# 导入数据库引擎实例，用于数据库操作
from app.db.session import engine
# 导入 Prometheus 监控中间件和指标端点
from app.observability.metrics import PrometheusMiddleware, metrics_endpoint

# 创建当前模块的日志记录器实例
logger = get_logger(__name__)


# 定义应用的生命周期管理器（启动和关闭时的钩子函数）
# @asynccontextmanager 装饰器将其转换为异步上下文管理器
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # 启动时：初始化日志系统配置
    configure_logging()
    # 记录应用启动日志，包含环境和应用名称信息
    logger.info("startup", environment=settings.environment, app=settings.app_name)
    # yield 之前的代码在应用启动时执行
    yield
    # yield 之后的代码在应用关闭时执行（优雅关闭）
    # 断开数据库连接池，释放数据库资源
    await engine.dispose()
    # 关闭 Redis 连接，释放 Redis 资源
    await redis_client.aclose()
    # 记录应用关闭日志
    logger.info("shutdown")


# 应用工厂函数：创建并配置 FastAPI 应用实例
# 使用工厂模式便于在测试中创建独立的应用实例
def create_app() -> FastAPI:
    # 初始化日志系统配置
    configure_logging()
    # 创建 FastAPI 应用实例，配置基本信息
    app = FastAPI(
        title=settings.app_name,  # 应用标题（显示在 API 文档中）
        version="0.1.0",  # 应用版本号
        debug=settings.debug,  # 是否开启调试模式（从环境变量读取）
        lifespan=lifespan,  # 绑定生命周期管理器（启动/关闭钩子）
        description=(  # 应用描述（显示在 API 文档首页）
            "一个面向生产的 URL 缩短器，带有点击分析、Redis 缓存和滑动窗口速率限制。"

        ),
        # 配置 Swagger UI 为中文界面
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,  # 隐藏 Models 部分
            "displayRequestDuration": True,  # 显示请求耗时
            "filter": True,  # 启用搜索过滤
            "tryItOutEnabled": True,  # 默认启用"试用"功能
        },
        # 自定义 Swagger UI 的翻译配置
        docs_url="/docs",  # Swagger UI 地址
        redoc_url="/redoc",  # ReDoc 地址
    )

    # 添加 CORS（跨域资源共享）中间件
    # 允许前端网页从不同域名访问后端 API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # 允许的源域名列表（从配置读取）
        allow_credentials=True,  # 允许携带凭证（如 Cookie、Authorization 头）
        allow_methods=["*"],  # 允许所有 HTTP 方法（GET、POST、PUT、DELETE 等）
        allow_headers=["*"],  # 允许所有 HTTP 请求头
    )
    # 添加 Prometheus 监控中间件
    # 自动收集每个请求的指标数据（请求数、响应时间等）
    app.add_middleware(PrometheusMiddleware)

    # 添加自定义 HTTP 中间件：为每个请求生成唯一的 request_id
    # 用于在日志系统中追踪同一个请求的完整链路
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        # 从请求头中获取 request_id，如果不存在则生成一个新的 UUID
        # 优先使用客户端传来的 X-Request-ID（便于全链路追踪）
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        # 将 request_id 绑定到 structlog 的上下文变量中
        # 这样后续所有日志都会自动包含这个 request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            # 继续处理请求（调用下一个中间件或路由处理器）
            response = await call_next(request)
        finally:
            # 请求处理完成后，清除上下文变量（避免内存泄漏）
            structlog.contextvars.clear_contextvars()
        # 在响应头中添加 request_id，方便客户端排查问题
        response.headers["X-Request-ID"] = request_id
        # 返回响应
        return response

    # 健康检查端点：Liveness Probe（存活探针）
    # Kubernetes 等容器编排系统用它判断容器是否还在运行
    @app.get("/health", tags=["ops"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        # 简单返回 ok，表示应用进程正常运行
        return {"status": "ok"}

    # 就绪检查端点：Readiness Probe（就绪探针）
    # Kubernetes 用它判断容器是否可以接收流量（依赖服务是否可用）
    @app.get("/health/ready", tags=["ops"], summary="Readiness probe")
    async def ready() -> JSONResponse:
        # 存储各个依赖服务的检查结果
        checks: dict[str, str] = {}
        # 检查数据库连接是否正常
        try:
            # 建立数据库连接并执行简单的查询
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            # 如果查询成功，标记数据库状态为 ok
            checks["database"] = "ok"
        except Exception:
            # 如果查询失败，标记数据库状态为 error
            checks["database"] = "error"
        # 检查 Redis 连接是否正常
        try:
            # 向 Redis 发送 ping 命令
            await redis_client.ping()
            # 如果 ping 成功，标记 Redis 状态为 ok
            checks["redis"] = "ok"
        except Exception:
            # 如果 ping 失败，标记 Redis 状态为 error
            checks["redis"] = "error"
        # 判断所有依赖服务是否都正常（全部为 ok 才算健康）
        healthy = all(v == "ok" for v in checks.values())
        # 根据健康状况返回不同的 HTTP 状态码
        # 200 表示健康，503 表示服务不可用（Kubernetes 会停止向其转发流量）
        return JSONResponse(checks, status_code=200 if healthy else 503)

    # 注册 Prometheus 指标端点
    # 访问 /metrics 可以获取监控指标数据（供 Prometheus 抓取）
    app.add_route("/metrics", metrics_endpoint)

    # 注册管理 API 路由（挂载到 /api/v1 前缀下）
    # 包含用户认证、短链 CRUD、点击分析等接口
    app.include_router(api_router, prefix="/api/v1")
    # 注册重定向路由（处理短链接跳转，路径为 /{code}）
    # 注意：必须最后注册，因为它的路径是通配符形式
    # 如果放在前面，会拦截 /health、/metrics、/docs 等系统路径
    app.include_router(redirect_router)

    # 挂载前端静态文件（Vue 构建产物）
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
        
        # SPA 路由回退：非 API 和非静态文件请求都返回 index.html
        @app.get("/{path:path}", include_in_schema=False)
        async def serve_spa(path: str):
            from fastapi.responses import FileResponse
            index = static_dir / "index.html"
            if index.exists():
                return FileResponse(index)
            return {"error": "Frontend not built. Run: cd frontend && npm run build"}

    # 返回配置完成的应用实例
    return app


# 创建全局应用实例（uvicorn 启动时会使用这个对象）
# 命令示例：uvicorn app.main:app --reload
app = create_app()


# 允许直接运行此文件进行开发（自动启动 Uvicorn 服务器）
# 用法：python -m app.main 或 python app/main.py
if __name__ == "__main__":
    import uvicorn
    
    # 启动 Uvicorn 开发服务器
    uvicorn.run(
        "app.main:app",  # 应用路径：模块名:应用实例名
        host="127.0.0.1",  # 监听地址（仅本地访问）
        port=8000,  # 监听端口
        reload=True,  # 开启热重载（代码修改后自动重启）
        log_level="info",  # 日志级别
    )
