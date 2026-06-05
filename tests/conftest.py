from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models.company import CompanyProfile


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
        "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "status": "open",
    }


@pytest.fixture()
def closed_tender_meta() -> dict:
    return {
        "cpv": "45000000",
        "nuts": "EL30",
        "budget": "2000000",
        "deadline": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "status": "open",
    }


@pytest.fixture()
def ted_notice_payload() -> dict:
    return {
        "ND": "12345678",
        "TI": "Road Construction Services",
        "PC": ["45000000", "45233000"],
        "TW": ["EL30"],
        "DD": (datetime.now(timezone.utc) + timedelta(days=60)).strftime("%Y%m%d"),
        "TVA": "3500000",
        "TE": "Construction of road infrastructure in Attica region.",
        "uri": "https://ted.europa.eu/en/notice/12345678",
    }
