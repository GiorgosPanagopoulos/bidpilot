from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.models.award import Award
from app.repositories.mongo import get_db

COLLECTION = "awards"


async def upsert_award(award: Award) -> Award:
    doc = award.model_dump()
    doc["_id"] = doc.pop("id")
    doc["award_value"] = str(doc["award_value"])
    doc["award_date"] = award.award_date.isoformat()
    await get_db()[COLLECTION].replace_one({"_id": doc["_id"]}, doc, upsert=True)
    return award


async def list_awards(
    cpv: str | None = None,
    contracting_authority: str | None = None,
    supplier_name: str | None = None,
    supplier_vat: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 500,
) -> list[Award]:
    query: dict = {}
    if cpv:
        query["cpv_codes"] = cpv
    if contracting_authority:
        query["contracting_authority"] = {"$regex": contracting_authority, "$options": "i"}
    if supplier_name:
        query["supplier_name"] = {"$regex": supplier_name, "$options": "i"}
    if supplier_vat:
        query["supplier_vat"] = supplier_vat
    if from_date or to_date:
        date_filter: dict = {}
        if from_date:
            date_filter["$gte"] = from_date.isoformat()
        if to_date:
            date_filter["$lte"] = to_date.isoformat()
        query["award_date"] = date_filter
    cursor = get_db()[COLLECTION].find(query).limit(limit)
    results: list[Award] = []
    async for doc in cursor:
        doc["id"] = doc.pop("_id")
        doc["award_value"] = Decimal(str(doc["award_value"]))
        results.append(Award(**doc))
    return results
