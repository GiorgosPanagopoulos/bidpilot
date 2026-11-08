from decimal import Decimal
from typing import Any

from bson.decimal128 import Decimal128

from app.core.exceptions import NotFoundError
from app.models.company import CompanyProfile
from app.repositories.mongo import get_db

COLLECTION = "companies"


def _to_doc(profile: CompanyProfile) -> dict[str, Any]:
    doc = profile.model_dump()
    doc["_id"] = doc.pop("id")
    # BSON has no Python Decimal; Decimal128 keeps the value exact and numeric in Mongo.
    doc["annual_turnover"] = Decimal128(doc["annual_turnover"])
    return doc


def _from_doc(doc: dict[str, Any]) -> CompanyProfile:
    doc["id"] = doc.pop("_id")
    turnover = doc.get("annual_turnover")
    if isinstance(turnover, Decimal128):
        doc["annual_turnover"] = turnover.to_decimal()
    elif turnover is not None and not isinstance(turnover, Decimal):
        doc["annual_turnover"] = Decimal(str(turnover))
    return CompanyProfile(**doc)


async def upsert_company(profile: CompanyProfile) -> CompanyProfile:
    doc = _to_doc(profile)
    await get_db()[COLLECTION].replace_one({"_id": doc["_id"]}, doc, upsert=True)
    return profile


async def get_company(company_id: str) -> CompanyProfile:
    doc = await get_db()[COLLECTION].find_one({"_id": company_id})
    if not doc:
        raise NotFoundError(f"company {company_id} not found")
    return _from_doc(doc)
