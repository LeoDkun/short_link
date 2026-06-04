from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    # code 可空且唯一：先插入拿到自增 id，再用 base62(id) 回填，避免占位串并发冲突
    code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True, nullable=True)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # 冗余计数器，O(1) 读取总点击数，热点重定向路径无需 COUNT(*)
    click_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    owner: Mapped[User] = relationship(back_populates="links")
    clicks: Mapped[list[ClickEvent]] = relationship(
        back_populates="link", cascade="all, delete-orphan"
    )


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id", ondelete="CASCADE"), index=True)
    # 落库时写入 UTC 日期列，使按天聚合在 SQLite/Postgres 下都可走索引 GROUP BY
    event_day: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    referrer: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 隐私：仅存哈希
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    link: Mapped[Link] = relationship(back_populates="clicks")


# 复合索引服务于「按链接 + 按天」的分析查询
Index("ix_click_events_link_day", ClickEvent.link_id, ClickEvent.event_day)
