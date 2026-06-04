from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import FileResponse, RedirectResponse

from app.api.deps import Sessionmaker, get_link_service
from app.services.links import LinkService, record_click_task

router = APIRouter(tags=["redirect"])

# 前端 SPA 的一级路由路径（与 frontend/src/router/index.js 保持一致）
# 注意：这些词也应在创建短链时作为保留字拒绝，避免自定义别名遮住前端页面
_FRONTEND_ROUTES = {"login", "register", "dashboard", "create"}

# 前端构建产物目录：app/api/redirect.py 往上三级 -> D:\shortlink\static
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


def _spa_response():
    """返回前端入口页；构建产物不存在时返回 404。"""
    index = _STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.get("/analytics/{code}", include_in_schema=False)
async def spa_analytics(code: str):
    # 两段式前端路由（/analytics/xxx），直接访问或刷新时返回 SPA 入口
    return _spa_response()


@router.get("/{code}", include_in_schema=False)
async def redirect_or_spa(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    service: Annotated[LinkService, Depends(get_link_service)],
    sessionmaker: Sessionmaker,
):
    # 先按 code 查库（自动码和自定义别名一视同仁），查到就跳转
    target = await service.resolve(code)
    if target is not None:
        background_tasks.add_task(
            record_click_task,
            sessionmaker,
            code,
            request.headers.get("referer"),
            request.headers.get("user-agent"),
            request.client.host if request.client else None,
        )
        return RedirectResponse(url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # 前端一级路由（直接访问或刷新 /login 等）→ 返回 SPA 入口，由 Vue 接管
    if code in _FRONTEND_ROUTES:
        return _spa_response()

    # 既不是有效短码，也不是前端路由 → 真 404
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
