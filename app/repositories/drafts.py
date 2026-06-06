from __future__ import annotations

from typing import Any

from app.core.context import current_tenant
from app.models.draft import BidDraft
from app.repositories.mongo import get_db

COLLECTION = "bid_drafts"


async def upsert_draft(draft: BidDraft) -> None:
    doc: dict[str, Any] = draft.model_dump(mode="json")
    doc["tenant"] = current_tenant.get()
    await get_db()[COLLECTION].replace_one({"id": draft.id}, doc, upsert=True)


async def get_draft(draft_id: str) -> BidDraft | None:
    tenant = current_tenant.get()
    query: dict[str, Any] = {"id": draft_id}
    if tenant:
        query["tenant"] = tenant
    doc = await get_db()[COLLECTION].find_one(query)
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("tenant", None)
    return BidDraft.model_validate(doc)


async def save_trace(draft_id: str, trace: list[dict[str, Any]]) -> None:
    await get_db()[COLLECTION].update_one(
        {"id": draft_id},
        {"$set": {"_trace": trace}},
    )


async def get_trace(draft_id: str) -> list[dict[str, Any]] | None:
    tenant = current_tenant.get()
    query: dict[str, Any] = {"id": draft_id}
    if tenant:
        query["tenant"] = tenant
    doc = await get_db()[COLLECTION].find_one(query, {"_trace": 1})
    if doc is None:
        return None
    return doc.get("_trace", [])
