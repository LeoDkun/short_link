# ShortLink · 短链接与点击分析服务

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/<user>/shortlink/actions/workflows/ci.yml/badge.svg)](https://github.com/<user>/shortlink/actions)

一个**生产形态**的全栈 URL 短链接服务：后端提供短链生成、重定向、点击分析等核心 API，前端用 Vue 3 打造完整管理界面。重点不在功能多，而在工程深度——异步、缓存、限流、可观测性、迁移、容器化、CI 一应俱全，代码按 router → service → repository 分层，便于讲清每个决策背后的取舍。

## 功能特性

- **短链管理**：创建、查看、更新、删除短链接，支持自定义别名
- **智能重定向**：基于 Redis 缓存的 O(1) 重定向，异步记录点击
- **点击分析**：按天聚合、Top Referrer、总量统计，双轨计数（冗余计数器 + 明细表）
- **滑动窗口限流**：基于 Redis 有序集合，无窗口边界突刺问题
- **JWT 鉴权**：OAuth2 password flow，Argon2 密码哈希
- **前端管理界面**：Vue 3 + Element Plus，含仪表盘、创建短链、分析看板、登录注册
- **可观测性**：structlog 结构化日志 + Prometheus 指标 + 存活/就绪探针
- **一键启动**：`start.bat` / `start.ps1` 自动构建前端并启动后端

## 技术栈

### 后端

| 领域 | 选型 | 说明 |
| --- | --- | --- |
| Web 框架 | **FastAPI** | 异步、自带 OpenAPI 文档、类型驱动 |
| ORM | **SQLAlchemy 2.0（async）** | `Mapped` 声明式；asyncpg(生产) / aiosqlite(测试) |
| 迁移 | **Alembic**（async env） | 版本化 schema |
| 校验/配置 | **Pydantic v2 + pydantic-settings** | 12-factor，环境变量注入 |
| 缓存/限流 | **Redis**（redis.asyncio） | cache-aside + 滑动窗口限流 |
| 鉴权 | **JWT(PyJWT) + Argon2(pwdlib)** | OAuth2 password flow |
| 可观测性 | **structlog + prometheus-client** | 结构化日志 + 指标 |
| 测试 | **pytest-asyncio + httpx + fakeredis** | 全异步，零外部依赖 |
| 质量 | **ruff + mypy + GitHub Actions** | lint/格式/类型/测试 |
| 运行 | **Docker(多阶段) + docker-compose** | api + postgres + redis |

### 前端

| 领域 | 选型 | 说明 |
| --- | --- | --- |
| 框架 | **Vue 3** | Composition API + `<script setup>` |
| 路由 | **Vue Router 4** | 历史模式、路由守卫鉴权 |
| 状态管理 | **Pinia** | 轻量级 store 管理认证状态 |
| HTTP | **Axios** | 统一拦截器、Token 注入 |
| UI 组件 | **Element Plus** | 表格、表单、消息提示等 |
| 构建 | **Vite 5** | 开发热重载 + 生产构建输出到 `static/` |

## 架构与目录

```
app/
├── main.py              # 应用工厂、中间件、生命周期、路由装配
├── core/                # 横切关注点
│   ├── config.py        #   Settings（环境变量）
│   ├── security.py      #   Argon2 哈希 + JWT 签发/校验
│   └── logging.py       #   structlog 配置
├── db/
│   ├── session.py       # 异步引擎 + sessionmaker + get_db 依赖
│   └── redis.py         # Redis 客户端 + get_redis 依赖
├── models/              # ORM 模型：User / Link / ClickEvent
├── schemas/             # Pydantic 出入参模型
├── repositories/        # 数据访问层（只碰 SQL，不含业务）
├── services/            # 业务层：短码、限流、鉴权、链接
│   ├── shortcode.py     #   base62 编解码
│   ├── ratelimit.py     #   滑动窗口限流器（Redis sorted set）
│   └── links.py         #   cache-aside 解析 + 后台埋点任务
├── api/
│   ├── deps.py          # FastAPI 依赖（当前用户、限流、DI）
│   ├── v1/              # 管理 API（/api/v1）
│   └── redirect.py      # 公开重定向 /{code}
└── observability/
    └── metrics.py       # Prometheus 中间件 + /metrics

frontend/                # Vue 3 前端
├── src/
│   ├── api/             # Axios 实例 + 拦截器
│   ├── components/      # 通用组件（Navbar）
│   ├── views/           # 页面：登录、注册、仪表盘、创建短链、分析
│   ├── router/          # Vue Router 路由定义 + 鉴权守卫
│   ├── stores/          # Pinia store（认证状态）
│   └── styles/          # 全局主题样式
└── vite.config.js       # Vite 构建配置（产物输出到 static/）

alembic/                 # 迁移
tests/                   # 异步测试（sqlite + fakeredis）
```

依赖方向单向向内：`api → services → repositories → models`。每层都能单独 mock/替换，这也是测试能完全脱离 Postgres/Redis 的原因。

## 快速开始

### 方式一：一键启动（推荐）

双击 `start.bat` 或在 PowerShell 中运行 `.\start.ps1`，脚本会自动构建前端并启动后端：

```bash
# Windows 双击或命令行
start.bat
# 或 PowerShell
.\start.ps1

# 等效的 Make 命令
make frontend
```

启动后访问 http://127.0.0.1:8000 即可使用完整的前后端应用。

### 方式二：conda + pip（本地开发）

```bash
conda create -n shortlink python=3.12 -y
conda activate shortlink
pip install -r requirements-dev.txt

# 最省事：本地直接用 SQLite 跑（无需 Postgres/Redis 时，鉴权/CRUD 可用；
# 限流与缓存需要 Redis，可临时跳过相关路径或起一个本地 redis）
export DATABASE_URL="sqlite+aiosqlite:///./shortlink.db"
alembic upgrade head
uvicorn app.main:app --reload
# 打开 http://localhost:8000/docs
```

> 用 conda 管理解释器与隔离、用 pip 安装库是社区常见组合；想要更快的安装器可换 **uv**：
> `uv pip install -r requirements-dev.txt`。

### 方式三：docker compose（最接近生产，一键起全套）

```bash
cp .env.example .env          # 按需修改，务必替换 SECRET_KEY
docker compose up --build
# api 容器启动时会自动执行 alembic 迁移，再用 gunicorn + uvicorn worker 起服务
```

### 前端开发模式

如果需要单独开发前端（支持热重载），可以在两个终端分别启动：

```bash
# 终端 1：启动后端
uvicorn app.main:app --reload

# 终端 2：启动前端开发服务器（端口 3000，自动代理 /api 到后端）
cd frontend && npm install && npm run dev
```

或使用 Make 命令：

```bash
make frontend-dev   # Windows 下同时启动前端和后端
```

### 开发命令（Makefile）

```bash
make install       # 安装开发依赖
make lint          # ruff check
make format        # ruff format
make typecheck     # mypy
make test          # pytest
make frontend      # 构建前端 + 启动后端
make frontend-dev  # 开发模式：同时启动前端和后端
```

## API 一览

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register` | 注册 | – |
| POST | `/api/v1/auth/login` | 登录，返回 JWT | – |
| POST | `/api/v1/links` | 创建短链（可选 `custom_alias`） | ✅ |
| GET | `/api/v1/links` | 分页列出自己的短链 | ✅ |
| GET | `/api/v1/links/{code}` | 查看单个短链 | ✅ |
| PATCH | `/api/v1/links/{code}` | 更新目标 URL / 启停 | ✅ |
| DELETE | `/api/v1/links/{code}` | 删除短链 | ✅ |
| GET | `/api/v1/links/{code}/analytics` | 点击分析（总量/按天/Top Referrer） | ✅ |
| GET | `/{code}` | 公开重定向（307），异步记录点击 | – |
| GET | `/health` · `/health/ready` | 存活 / 就绪探针 | – |
| GET | `/metrics` | Prometheus 指标 | – |

完整交互文档：启动后访问 http://127.0.0.1:8000/docs（Swagger UI）

## 技术亮点 / 面试讲解点

> 下面每一条都是可以展开聊「为什么这么做、有什么取舍」的点。

1. **分层架构（router / service / repository）**：路由只做 HTTP 适配，业务在 service，SQL 在 repository。
   好处是单测可以只测 service，数据库可替换，职责清晰。

2. **真·全异步**：SQLAlchemy 2.0 异步引擎 + asyncpg，IO 密集场景吞吐更高。测试切换到 aiosqlite，
   完全靠 `dependency_overrides` 注入，业务代码零改动。

3. **短码生成策略**：用自增主键做 **base62** 编码并加偏移量。
   - 天然唯一、**无需冲突检测与重试**；
   - 偏移量保证最短也有 5 位、且不会暴露成 `0/1/2` 这种可遍历序列；
   - `code` 列设计为**可空 + 唯一**：先以 `NULL` 插入拿到自增 id，再回填 `base62(id)`。
     这样避开了「用占位字符串插入 → 并发下撞唯一索引」的坑（唯一索引中多个 `NULL` 互不冲突）。

4. **双轨点击分析**：
   - `Link.click_count` 冗余计数器 → **O(1)** 读取总点击；
   - `ClickEvent` 明细表带一个**反规范化的 `event_day` 日期列**，让「按天聚合」在 SQLite 和 Postgres 上
     都能走索引 `GROUP BY`、且 SQL 可移植（避免 `date()` 这类方言函数）；配 `(link_id, event_day)` 复合索引。

5. **缓存（cache-aside）**：重定向解析短码先查 Redis、未命中回源数据库再写缓存；
   更新/删除短链时**主动失效缓存**，避免脏读。

6. **滑动窗口限流**：用 Redis **有序集合**实现——剔除窗口外时间戳、`ZADD` 当前请求、`ZCARD` 计数，
   用 **pipeline** 打包减少往返。相比固定窗口没有边界突刺问题。

7. **埋点异步化**：重定向用 `BackgroundTask` 写点击事件，热路径只读缓存、立即返回 307；
   后台任务用**独立会话**，规避「请求会话已在响应后关闭」的陷阱。

8. **隐私**：IP 只落 `sha256` 哈希，不存明文。

9. **可观测性**：structlog 结构化日志 + 每请求注入 `request_id`（贯穿全链路）；
   Prometheus 指标按**路由模板**而非真实路径打标签，避免短码导致标签基数爆炸；提供存活/就绪探针。

10. **前后端整合部署**：Vite 构建产物输出到 `static/`，FastAPI 同时服务 API 和前端 SPA，
    生产环境只需部署一个服务。非 API 请求自动回退到 `index.html`，支持 Vue Router 历史模式。

11. **工程化**：ruff（lint+format）、mypy 类型检查、pytest 全异步覆盖核心链路；
    GitHub Actions CI 用 SQLite + fakeredis，**无需任何外部服务**即可绿；
    多阶段 Dockerfile 以非 root 运行，compose 带健康检查与依赖编排。

## 可扩展性 / 演进方向

- **点击量暴涨**：重定向只把事件发到 **Redis Streams / Kafka**，由独立消费者批量落库与做实时聚合，
  彻底解耦「重定向热路径」与「分析写入」。
- **读多写少**：Postgres 只读副本 + 缓存层，短码解析几乎全命中缓存。
- **计数器热点**：高并发自增可改为 Redis `INCR` 周期回刷，或分桶计数。
- **水平扩展**：服务无状态，可多副本横向扩；若分库，号段/雪花替代自增 id。
- **产品化**：自定义域名、链接过期、软删除、批量导入、二维码等可增量叠加。

## 测试

```bash
pytest                       # 18 项：鉴权 / CRUD / 重定向+缓存 / 限流
```

测试覆盖：注册登录与鉴权失败、短链 CRUD 与自定义别名冲突、非法 URL 校验、
重定向 307 与点击计数、cache-aside 命中与更新失效、滑动窗口限流（单元 + 接口 429）。

## 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://...` | 数据库连接字符串 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `SECRET_KEY` | `CHANGE_ME_IN_PRODUCTION` | JWT 签名密钥（**生产务必替换**） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token 过期时间（分钟） |
| `RATE_LIMIT_REQUESTS` | `100` | 滑动窗口最大请求数 |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | 滑动窗口大小（秒） |
| `CACHE_TTL_SECONDS` | `3600` | 缓存过期时间（秒） |
| `CORS_ORIGINS` | `*` | 允许的跨域来源 |
| `BASE_URL` | `http://localhost:8000` | 应用基础 URL |

完整示例见 [`.env.example`](.env.example)。

## License

[MIT](LICENSE)
