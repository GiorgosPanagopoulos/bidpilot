from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agent.executor import run_drafting_agent
from app.api.deps import ensure_own_company, get_current_user, require_writer
from app.core.exceptions import NotFoundError
from app.models.draft import BidDraft
from app.models.user import User
from app.repositories.audit import fire_and_forget
from app.repositories.drafts import get_draft, get_trace
from app.services.demo_quota import consume_draft_quota, refund_draft_quota

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
    user: User = Depends(require_writer),
) -> Any:
    ensure_own_company(req.company_id, user)
    charged_day = await consume_draft_quota(user)
    try:
        draft = await run_drafting_agent(
            company_id=req.company_id,
            tender_id=req.tender_id,
        )
    except Exception:
        # A failed run shouldn't burn one of the demo's few daily drafts.
        if charged_day is not None:
            await refund_draft_quota(user, charged_day)
        raise
    fire_and_forget(
        "drafts.run",
        {"company_id": req.company_id, "tender_id": req.tender_id, "draft_id": draft.id},
    )
    return {**draft.model_dump(), "notice": _REVIEW_NOTICE}


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft_endpoint(
    draft_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    draft = await get_draft(draft_id)
    if draft is None:
        raise NotFoundError(f"draft {draft_id} not found")
    return {**draft.model_dump(), "notice": _REVIEW_NOTICE}


@router.get("/{draft_id}/trace")
async def get_draft_trace(
    draft_id: str,
    _: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    trace = await get_trace(draft_id)
    if trace is None:
        raise NotFoundError(f"draft {draft_id} not found")
    return trace
