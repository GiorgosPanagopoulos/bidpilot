from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AwardSource(StrEnum):
    DIAVGEIA = "DIAVGEIA"
    KIMDIS = "KIMDIS"


class RawAward(BaseModel):
    source: AwardSource
    payload: dict[str, Any]


class Award(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: Literal["DIAVGEIA", "KIMDIS"]
    cpv_codes: list[str] = Field(default_factory=list)
    contracting_authority: str
    supplier_name: str
    supplier_vat: str | None = None
    award_value: Decimal
    currency: str = "EUR"
    award_date: datetime
    nuts: list[str] = Field(default_factory=list)
    tender_ref: str | None = None
    raw_doc_uri: str | None = None


# Analytics result models


class PricingStats(BaseModel):
    cpv: str | None
    count: int
    min: Decimal | None
    max: Decimal | None
    mean: Decimal | None
    median: Decimal | None
    p25: Decimal | None
    p75: Decimal | None
    currency: str


class SupplierWinRate(BaseModel):
    supplier_name: str
    supplier_vat: str | None
    awards_won: int
    total_value: Decimal
    win_share: float


class TrendPoint(BaseModel):
    period: str
    count: int
    total_value: Decimal
    mean_value: Decimal


class TrendSeries(BaseModel):
    interval: Literal["month", "quarter", "year"]
    points: list[TrendPoint]
