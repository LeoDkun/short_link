from datetime import date, datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class LinkCreate(BaseModel):
    target_url: AnyHttpUrl
    custom_alias: str | None = Field(
        default=None, min_length=3, max_length=16, pattern=r"^[0-9A-Za-z_-]+$"
    )


class LinkUpdate(BaseModel):
    target_url: AnyHttpUrl | None = None
    is_active: bool | None = None


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    target_url: str
    short_url: str | None = None
    click_count: int
    is_active: bool
    created_at: datetime


class DailyClicks(BaseModel):
    day: date
    count: int


class ReferrerStat(BaseModel):
    referrer: str
    count: int


class LinkAnalytics(BaseModel):
    code: str
    total_clicks: int
    daily: list[DailyClicks]
    top_referrers: list[ReferrerStat]
