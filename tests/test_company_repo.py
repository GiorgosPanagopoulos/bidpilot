from decimal import Decimal

from app.models.company import CompanyProfile
from app.repositories.companies import get_company, upsert_company


async def test_turnover_round_trips_through_bson(fake_db):
    profile = CompanyProfile(id="acme", name="Acme", annual_turnover=Decimal("1250000.50"))

    await upsert_company(profile)
    loaded = await get_company("acme")

    assert loaded.annual_turnover == Decimal("1250000.50")
    assert loaded == profile


async def test_reads_legacy_numeric_turnover(fake_db):
    fake_db["companies"].docs.append({"_id": "old", "name": "Old", "annual_turnover": 5000})

    assert (await get_company("old")).annual_turnover == Decimal("5000")
