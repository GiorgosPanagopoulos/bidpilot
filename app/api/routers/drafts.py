from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agent.executor import run_drafting_agent
from app.api.deps import set_tenant
from app.core.exceptions import NotFoundError
from app.models.draft import BidDraft
from app.repositories.audit import fire_and_forget
from app.repositories.drafts import get_draft, get_trace

router = APIRouter(prefix="/drafts", tags=["drafts"])

_REVIEW_NOTICE = (
    "This is decision-support output. Mandatory human review is required before any submission."
)


class DraftRequest(BaseModel):
    company_id: str
    tender_id: str


class DraftResponse(BidDraft):
    notice: str = _REVIEW_NOTICE


@router.post("/run", response_model=DraftResponse, status_code=201)
async def run_draft(
    req: DraftRequest,
    _: None = Depends(set_tenant),
) -> Any:
    draft = await run_drafting_agent(
        company_id=req.company_id,
        tender_id=req.tender_id,
    )
    fire_and_forget(
        "drafts.run",
        {"company_id": req.company_id, "tender_id": req.tender_id, "draft_id": draft.id},
    )
    return {**draft.model_dump(), "notice": _REVIEW_NOTICE}


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft_endpoint(
    draft_id: str,
    _: None = Depends(set_tenant),
) -> Any:
    draft = await get_draft(draft_id)
    if draft is None:
        raise NotFoundError(f"draft {draft_id} not found")
    return {**draft.model_dump(), "notice": _REVIEW_NOTICE}


@router.get("/{draft_id}/trace")
async def get_draft_trace(
    draft_id: str,
    _: None = Depends(set_tenant),
) -> list[dict[str, Any]]:
    trace = await get_trace(draft_id)
    if trace is None:
        raise NotFoundError(f"draft {draft_id} not found")
    return trace
