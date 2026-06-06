from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import set_tenant
from app.models.award import PricingStats, SupplierWinRate, TrendSeries
from app.repositories.awards import list_awards
from app.services.analytics import compute_pricing_stats, compute_trends, compute_win_rates

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/pricing", response_model=PricingStats)
async def pricing_stats(
    cpv: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    _: None = Depends(set_tenant),
) -> PricingStats:
    awards = await list_awards(cpv=cpv, from_date=from_date, to_date=to_date)
    return compute_pricing_stats(awards, cpv=cpv)


@router.get("/win-rates", response_model=list[SupplierWinRate])
async def win_rates(
    cpv: str | None = Query(default=None),
    authority: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    top_n: int | None = Query(default=None),
    _: None = Depends(set_tenant),
) -> list[SupplierWinRate]:
    awards = await list_awards(
        cpv=cpv,
        contracting_authority=authority,
        from_date=from_date,
        to_date=to_date,
    )
    return compute_win_rates(awards, top_n=top_n)


@router.get("/trends", response_model=TrendSeries)
async def trends(
    cpv: str | None = Query(default=None),
    authority: str | None = Query(default=None),
    interval: Literal["month", "quarter", "year"] = Query(default="month"),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    _: None = Depends(set_tenant),
) -> TrendSeries:
    awards = await list_awards(
        cpv=cpv,
        contracting_authority=authority,
        from_date=from_date,
        to_date=to_date,
    )
    return compute_trends(awards, interval=interval)
