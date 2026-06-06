from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProposalCitation(BaseModel):
    tender_id: str
    locator: str
    snippet: str


class RequirementItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: Literal["technical", "financial", "legal", "administrative", "submission"]
    text: str
    mandatory: bool
    citation: ProposalCitation


class RequirementChecklist(BaseModel):
    tender_id: str
    items: list[RequirementItem]
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    prompt_version: str


class GapItem(BaseModel):
    requirement_id: str
    status: Literal["met", "partial", "unmet"]
    evidence: str | None = None
    note: str | None = None


class GapReport(BaseModel):
    company_id: str
    tender_id: str
    items: list[GapItem]
    coverage_ratio: float


class BidDraftSection(BaseModel):
    title: str
    content: str
    citations: list[ProposalCitation] = Field(default_factory=list)
    covers_requirements: list[str] = Field(default_factory=list)
    self_check_status: Literal["ok", "gaps"]


class BidDraft(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    tender_id: str
    sections: list[BidDraftSection]
    checklist: RequirementChecklist
    gap_report: GapReport
    status: Literal["needs_review"] = "needs_review"
    prompt_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
