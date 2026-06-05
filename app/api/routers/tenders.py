from fastapi import APIRouter, Depends, Query

from app.api.deps import set_tenant
from app.ingestion.scheduler import ingest_pipeline
from app.models.tender import Tender, TenderStatus
from app.repositories.audit import fire_and_forget
from app.repositories.tenders import list_tenders

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.post("/ingest", status_code=202)
async def trigger_ingest(_: None = Depends(set_tenant)) -> dict:
    count = await ingest_pipeline()
    fire_and_forget("tenders.ingest", {"count": count})
    return {"ingested": count}


@router.get("", response_model=list[Tender])
async def list_tenders_endpoint(
    status: TenderStatus | None = Query(default=None),
    cpv: str | None = Query(default=None),
    _: None = Depends(set_tenant),
) -> list[Tender]:
    return await list_tenders(status=status, cpv=cpv)
