from app.models.match import MatchResult
from app.repositories.mongo import get_db

COLLECTION = "matches"


async def upsert_match(match: MatchResult) -> MatchResult:
    key = {"tender_id": match.tender_id, "company_id": match.company_id}
    doc = match.model_dump()
    await get_db()[COLLECTION].replace_one(key, doc, upsert=True)
    return match


async def list_matches(company_id: str) -> list[MatchResult]:
    cursor = get_db()[COLLECTION].find({"company_id": company_id}).sort("score", -1)
    results = []
    async for doc in cursor:
        doc.pop("_id", None)
        results.append(MatchResult(**doc))
    return results
