import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TenderSource(StrEnum):
    TED = "TED"
    KIMDIS = "KIMDIS"
    ESIDIS = "ESIDIS"


class TenderStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    AWARDED = "awarded"


class RawTender(BaseModel):
    source: TenderSource
    payload: dict[str, Any]


class Tender(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: Literal["TED", "KIMDIS", "ESIDIS"]
    title: str
    cpv_codes: list[str] = Field(default_factory=list)
    budget: Decimal | None = None
    deadline: datetime
    nuts: list[str] = Field(default_factory=list)
    description: str = ""
    raw_doc_uri: str = ""
    exclusion_flags: list[str] = Field(default_factory=list)
    status: TenderStatus = TenderStatus.OPEN
