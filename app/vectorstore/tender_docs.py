from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb import Collection
from chromadb.api import ClientAPI

from app.core.settings import settings

logger = logging.getLogger(__name__)

TENDER_DOCS_COLLECTION = "tender_docs"

_client: ClientAPI | None = None
_collection: Collection | None = None


def _get_collection() -> Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.chroma_path)
        _collection = _client.get_or_create_collection(TENDER_DOCS_COLLECTION)
    return _collection


def upsert_chunks(chunks: list[dict[str, Any]]) -> None:
    col = _get_collection()
    col.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )


def get_all_tender_chunks(tender_id: str) -> list[dict[str, Any]]:
    col = _get_collection()
    try:
        result = col.get(
            where={"tender_id": tender_id},
            include=["metadatas", "documents"],
        )
        ids: list[str] = result.get("ids") or []
        docs: list[str] = result.get("documents") or []
        raw_metas = result.get("metadatas") or []
        metas: list[dict[str, Any]] = [dict(m) for m in raw_metas]
        return [
            {"id": id_, "text": doc, "metadata": meta} for id_, doc, meta in zip(ids, docs, metas)
        ]
    except Exception:
        return []


def query_tender_docs(
    tender_id: str,
    query_text: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    col = _get_collection()
    try:
        result = col.query(
            query_texts=[query_text],
            n_results=top_k,
            where={"tender_id": tender_id},
            include=["metadatas", "documents", "distances"],
        )
    except Exception:
        return []

    raw_ids = result.get("ids") or [[]]
    raw_docs = result.get("documents") or [[]]
    raw_metas = result.get("metadatas") or [[]]
    raw_dists = result.get("distances") or [[]]

    if not raw_ids[0]:
        return []

    return [
        {
            "id": id_,
            "text": doc,
            "metadata": dict(meta),
            "distance": dist,
        }
        for id_, doc, meta, dist in zip(raw_ids[0], raw_docs[0], raw_metas[0], raw_dists[0])
    ]


def has_tender_docs(tender_id: str) -> bool:
    col = _get_collection()
    try:
        result = col.get(where={"tender_id": tender_id}, limit=1, include=[])
        return len(result.get("ids", [])) > 0
    except Exception:
        return False
