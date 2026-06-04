import re
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

# 短码格式。注意：必须和你的短码生成器一致！
# 你日志里出现过 /QjA（字母开头、3 位），它并不符合下面这个正则。
# 若短码可能以字母开头或更短，请放宽，例如 r"^[0-9A-Za-z]{3,16}$"
_SHORT_CODE_RE = re.compile(r"^[0-9][0-9A-Za-z]{4,15}$")

# 前端构建产物目录：app/api/redirect.py 往上三级 -> D:\shortlink\static
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


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
        return RedirectResponse(
            url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )

    # 查不到 → 交给前端路由（/login、/dashboard 等走这里，未知路径由前端显示 404）
    index = _STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")