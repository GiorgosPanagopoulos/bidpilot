import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-for-unit-tests-only-0123456789abcdef"
)  # pragma: allowlist secret
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

from datetime import UTC, datetime, timedelta  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402

from app.models.company import CompanyProfile  # noqa: E402

pytest_plugins = ["tests.api_fixtures"]


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
    # Shape of a live TED v3 search hit (Nov 2026), trimmed.
    deadline = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d") + "+02:00"
    return {
        "publication-number": "756583-2026",
        "notice-title": {
            "eng": "Greece - Boat scale models",
            "ell": "Ελλάδα - Μοντέλα θαλάσσιων σκαφών",
        },
        "description-proc": {"ell": "Μουσείο Εναλίων Αρχαιοτήτων"},
        "classification-cpv": ["34999420", "92311000", "34999420", "92311000"],
        "place-of-performance": ["EL307", "GRC", "EL307", "GRC"],
        "deadline-receipt-tender-date-lot": [deadline],
        "estimated-value-proc": 3500000,
        "estimated-value-cur-proc": "EUR",
        "buyer-country": ["GRC"],
        "links": {
            "xml": {"MUL": "https://ted.europa.eu/en/notice/756583-2026/xml"},
            "pdf": {
                "ENG": "https://ted.europa.eu/en/notice/756583-2026/pdf",
                "ELL": "https://ted.europa.eu/el/notice/756583-2026/pdf",
            },
        },
    }
