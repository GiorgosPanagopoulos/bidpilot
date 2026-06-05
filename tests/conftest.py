import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

from datetime import UTC, datetime, timedelta  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402

from app.models.company import CompanyProfile  # noqa: E402


@pytest.fixture()
def sample_company() -> CompanyProfile:
    return CompanyProfile(
        id="comp-001",
        name="Acme Engineering",
        cpv_codes=["45000000", "72000000"],
        regions=["EL30", "EL41"],
        annual_turnover=Decimal("5000000"),
        capacity_tags=["civil engineering", "software"],
    )


@pytest.fixture()
def open_tender_meta() -> dict:
    return {
        "cpv": "45000000,72000000",
        "nuts": "EL30",
        "budget": "2000000",
        "deadline": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "status": "open",
    }


@pytest.fixture()
def closed_tender_meta() -> dict:
    return {
        "cpv": "45000000",
        "nuts": "EL30",
        "budget": "2000000",
        "deadline": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        "status": "open",
    }


@pytest.fixture()
def ted_notice_payload() -> dict:
    return {
        "ND": "12345678",
        "TI": "Road Construction Services",
        "PC": ["45000000", "45233000"],
        "TW": ["EL30"],
        "DD": (datetime.now(UTC) + timedelta(days=60)).strftime("%Y%m%d"),
        "TVA": "3500000",
        "TE": "Construction of road infrastructure in Attica region.",
        "uri": "https://ted.europa.eu/en/notice/12345678",
    }
