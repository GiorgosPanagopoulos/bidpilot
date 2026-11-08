from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_admin, require_writer
from app.core.exceptions import DocumentParsingError, NotFoundError
from app.ingestion.doc_parser import parse_pdf_to_chunks
from app.ingestion.scheduler import ingest_pipeline
from app.models.tender import Tender, TenderStatus
from app.models.user import User
from app.repositories.audit import fire_and_forget
from app.repositories.tenders import get_tender, list_tenders
from app.vectorstore.tender_docs import upsert_chunks

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.post("/ingest", status_code=202)
async def trigger_ingest(_: User = Depends(require_admin)) -> dict:
    count = await ingest_pipeline()
    fire_and_forget("tenders.ingest", {"count": count})
    return {"ingested": count}


@router.get("", response_model=list[Tender])
async def list_tenders_endpoint(
    status: TenderStatus | None = Query(default=None),
    cpv: str | None = Query(default=None),
    _: User = Depends(get_current_user),
) -> list[Tender]:
    return await list_tenders(status=status, cpv=cpv)


@router.post("/{tender_id}/ingest-doc", status_code=202)
async def ingest_doc(
    tender_id: str,
    _: User = Depends(require_writer),
) -> dict:
    tender = await get_tender(tender_id)
    if tender is None:
        raise NotFoundError(f"tender {tender_id} not found")

    raw_uri = tender.raw_doc_uri
    if not raw_uri:
        raise DocumentParsingError(f"tender {tender_id} has no raw_doc_uri")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(raw_uri)
            response.raise_for_status()
            pdf_bytes = response.content
    except Exception as exc:
        raise DocumentParsingError(f"failed to fetch document: {exc}") from exc

    try:
        chunks = parse_pdf_to_chunks(pdf_bytes, tender_id)
    except Exception as exc:
        raise DocumentParsingError(f"failed to parse PDF: {exc}") from exc

    if not chunks:
        raise DocumentParsingError(f"no text extracted from document for tender {tender_id}")

    upsert_chunks(chunks)
    fire_and_forget("tenders.ingest_doc", {"tender_id": tender_id, "chunks": len(chunks)})
    return {"tender_id": tender_id, "chunks_ingested": len(chunks)}
