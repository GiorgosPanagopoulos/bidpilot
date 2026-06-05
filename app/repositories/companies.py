from app.core.exceptions import NotFoundError
from app.models.company import CompanyProfile
from app.repositories.mongo import get_db

COLLECTION = "companies"


async def upsert_company(profile: CompanyProfile) -> CompanyProfile:
    doc = profile.model_dump()
    doc["_id"] = doc.pop("id")
    await get_db()[COLLECTION].replace_one({"_id": doc["_id"]}, doc, upsert=True)
    return profile


async def get_company(company_id: str) -> CompanyProfile:
    doc = await get_db()[COLLECTION].find_one({"_id": company_id})
    if not doc:
        raise NotFoundError(f"company {company_id} not found")
    doc["id"] = doc.pop("_id")
    return CompanyProfile(**doc)
