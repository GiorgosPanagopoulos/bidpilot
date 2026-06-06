from app.models.tender import Tender, TenderStatus
from app.repositories.mongo import get_db

COLLECTION = "tenders"


async def get_tender(tender_id: str) -> Tender | None:
    doc = await get_db()[COLLECTION].find_one({"_id": tender_id})
    if doc is None:
        return None
    doc["id"] = doc.pop("_id")
    return Tender(**doc)


async def upsert_tender(tender: Tender) -> Tender:
    doc = tender.model_dump()
    doc["_id"] = doc.pop("id")
    if doc.get("budget") is not None:
        doc["budget"] = str(doc["budget"])
    if doc.get("deadline"):
        doc["deadline"] = tender.deadline.isoformat()
    await get_db()[COLLECTION].replace_one({"_id": doc["_id"]}, doc, upsert=True)
    return tender


async def list_tenders(
    status: TenderStatus | None = None,
    cpv: str | None = None,
    limit: int = 100,
) -> list[Tender]:
    query: dict = {}
    if status:
        query["status"] = status.value
    if cpv:
        query["cpv_codes"] = cpv
    cursor = get_db()[COLLECTION].find(query).limit(limit)
    results = []
    async for doc in cursor:
        doc["id"] = doc.pop("_id")
        results.append(Tender(**doc))
    return results
