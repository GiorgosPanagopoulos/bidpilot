import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    cpv_codes: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)  # NUTS codes
    annual_turnover: Decimal = Field(default=Decimal("0"))
    capacity_tags: list[str] = Field(default_factory=list)
    exclusion_flags: list[str] = Field(default_factory=list)
