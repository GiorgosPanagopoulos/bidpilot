from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb import Collection
from chromadb.api import ClientAPI

from app.core.settings import settings
from app.models.tender import Tender

logger = logging.getLogger(__name__)

COLLECTION_NAME = "tenders"

_client: ClientAPI | None = None
_collection: Collection | None = None


def _get_collection() -> Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.chroma_path)
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
    return _collection


def _tender_text(tender: Tender) -> str:
    cpv_str = " ".join(tender.cpv_codes)
    nuts_str = " ".join(tender.nuts)
    return f"{tender.title} {tender.description} CPV:{cpv_str} NUTS:{nuts_str}"


def upsert_tender_embedding(tender: Tender) -> None:
    col = _get_collection()
    text = _tender_text(tender)
    meta: dict[str, Any] = {
        "title": tender.title,
        "cpv": ",".join(tender.cpv_codes),
        "nuts": ",".join(tender.nuts),
        "budget": str(tender.budget) if tender.budget else "",
        "deadline": tender.deadline.isoformat(),
        "status": tender.status.value,
        "description": tender.description,
        "exclusion_flags": ",".join(tender.exclusion_flags),
    }
    # ChromaDB default embedding function (sentence-transformers) used for Phase 1;
    # swap for Voyage-3 via langchain-anthropic in Phase 3 when prompt layer is ready.
    col.upsert(ids=[tender.id], metadatas=[meta], documents=[text])


def query_tenders(
    query_text: str,
    top_k: int = 20,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    col = _get_collection()
    kwargs: dict[str, Any] = {
        "query_texts": [query_text],
        "n_results": top_k,
        "include": ["metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    result = col.query(**kwargs)
    raw_ids = result["ids"]
    raw_metadatas = result["metadatas"]
    raw_distances = result["distances"]
    if raw_ids is None or raw_metadatas is None or raw_distances is None:
        return []
    ids = raw_ids[0]
    metadatas = raw_metadatas[0]
    distances = raw_distances[0]
    return [
        {"id": tid, "metadata": meta, "distance": dist}
        for tid, meta, dist in zip(ids, metadatas, distances)
    ]
