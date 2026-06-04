# 导入 LRU 缓存装饰器，用于缓存配置对象（单例模式）
# 避免每次调用都重新读取 .env 文件和验证配置
from functools import lru_cache

# 导入 Pydantic v2 的核心组件
from pydantic import Field, field_validator
# 导入 Pydantic Settings，专门用于管理应用配置（从环境变量/.env 文件加载）
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类，遵循 12-Factor App 原则。
    
    配置加载优先级（从高到低）：
    1. 操作系统环境变量（如 export DATABASE_URL=...）
    2. .env 文件中的配置
    3. 类定义中的默认值
    
    所有配置项都是类型安全的，Pydantic 会自动进行类型转换和验证。
    """

    # 配置 Pydantic Settings 的行为
    model_config = SettingsConfigDict(
        env_file=".env",              # 从项目根目录的 .env 文件读取配置
        env_file_encoding="utf-8",    # 支持中文注释等特殊字符
        extra="ignore"                # 忽略 .env 中未定义的变量（不报错）
    )

    # ==================== 应用基础配置 ====================
    app_name: str = "ShortLink"                    # 应用名称（显示在 API 文档中）
    environment: str = "development"               # 运行环境：development / staging / production
    debug: bool = False                            # 是否开启调试模式（生产环境必须为 False）
    base_url: str = "http://localhost:8000"        # 应用基础 URL，用于拼接完整的短链接地址

    # ==================== 数据库配置 ====================
    # 异步数据库连接字符串，支持两种驱动：
    # - PostgreSQL: postgresql+asyncpg://user:pass@host:port/dbname
    # - SQLite:     sqlite+aiosqlite:///./shortlink.db（本地开发用）
    database_url: str = "postgresql+asyncpg://shortlink:shortlink@localhost:5432/shortlink"

    # ==================== Redis 配置 ====================
    redis_url: str = "redis://localhost:6379/0"    # Redis 连接地址（用于缓存和限流）
    cache_ttl_seconds: int = 3600                  # 缓存过期时间（秒），默认 1 小时

    # ==================== 安全配置 ====================
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"    # JWT 签名密钥（⚠️ 生产环境必须替换为强随机字符串）
    access_token_expire_minutes: int = 60          # JWT Token 过期时间（分钟）
    jwt_algorithm: str = "HS256"                   # JWT 签名算法（HMAC-SHA256）

    # ==================== 速率限制配置（滑动窗口算法）====================
    rate_limit_requests: int = 100                 # 每个窗口允许的最大请求数
    rate_limit_window_seconds: int = 60            # 滑动窗口大小（秒）
    # 示例：60 秒内最多允许 100 个请求，超出返回 429 Too Many Requests

    # ==================== CORS 跨域配置 ====================
    # 允许的前端域名列表，使用 default_factory 避免可变对象共享问题
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    # 注意：生产环境应设置为具体域名，如 ["https://example.com"]

    # 自定义字段验证器：将逗号分隔的字符串转换为列表
    # 场景：用户在 .env 文件中写 CORS_ORIGINS="http://localhost:3000,https://example.com"
    #       需要自动转换成 ["http://localhost:3000", "https://example.com"]
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> object:
        """
        在 Pydantic 类型转换之前执行，处理 CORS 配置的格式转换。
        
        Args:
            v: 原始值（可能是字符串或列表）
        
        Returns:
            转换后的列表
        """
        if isinstance(v, str):
            # 按逗号分割，去除空白，过滤空字符串
            return [o.strip() for o in v.split(",") if o.strip()]
        return v  # 如果已经是列表，直接返回


# 配置对象工厂函数（带缓存）
# 使用 @lru_cache 实现单例模式：第一次调用时创建 Settings 实例，
# 之后每次调用都返回同一个对象，避免重复读取 .env 文件和验证
@lru_cache
def get_settings() -> Settings:
    """
    获取应用配置的单例对象。
    
    Returns:
        Settings 配置对象（全局唯一实例）
    """
    return Settings()


# 全局导出配置对象（整个应用共享这一个实例）
# 在其他模块中使用：from app.core.config import settings
settings = get_settings()
