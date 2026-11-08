from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_admin
from app.ingestion.scheduler import ingest_awards_pipeline
from app.models.award import Award
from app.models.user import User
from app.repositories.audit import fire_and_forget
from app.repositories.awards import list_awards

router = APIRouter(prefix="/awards", tags=["awards"])


@router.post("/ingest", status_code=202)
async def trigger_award_ingest(_: User = Depends(require_admin)) -> dict:
    count = await ingest_awards_pipeline()
    fire_and_forget("awards.ingest", {"count": count})
    return {"ingested": count}


@router.get("", response_model=list[Award])
async def list_awards_endpoint(
    cpv: str | None = Query(default=None),
    authority: str | None = Query(default=None),
    supplier: str | None = Query(default=None),
    supplier_vat: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    _: User = Depends(get_current_user),
) -> list[Award]:
    return await list_awards(
        cpv=cpv,
        contracting_authority=authority,
        supplier_name=supplier,
        supplier_vat=supplier_vat,
        from_date=from_date,
        to_date=to_date,
    )
