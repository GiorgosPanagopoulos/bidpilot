from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.ingestion.diavgeia import DiavgeiaSource
from app.models.award import AwardSource, RawAward


@pytest.fixture()
def diavgeia_source() -> DiavgeiaSource:
    return DiavgeiaSource(base_url="http://localhost")


@pytest.fixture()
def raw_award_payload() -> dict:
    return {
        "ada": "6ΩΒΝ4653ΠΩ-ΑΒΓ",
        "issuer": {"uid": "0001", "label": "Municipality of Athens"},
        "publishedDate": "2026-03-15",
        "documentUrl": "https://diavgeia.gov.gr/doc/6ΩΒΝ4653ΠΩ-ΑΒΓ",
        "extraFields": {
            "supplierName": "Acme Construction SA",
            "supplierVat": "EL123456789",
            "amountWithVat": "1250000.50",
            "currency": "EUR",
            "cpvCode": ["45000000", "45233000"],
            "nuts": ["EL30"],
        },
    }


def test_normalize_basic(diavgeia_source, raw_award_payload):
    raw = RawAward(source=AwardSource.DIAVGEIA, payload=raw_award_payload)
    award = diavgeia_source.normalize(raw)

    assert award.id == "diavgeia-6ΩΒΝ4653ΠΩ-ΑΒΓ"
    assert award.source == "DIAVGEIA"
    assert award.contracting_authority == "Municipality of Athens"
    assert award.supplier_name == "Acme Construction SA"
    assert award.supplier_vat == "EL123456789"
    assert award.award_value == Decimal("1250000.50")
    assert award.currency == "EUR"
    assert award.award_date == datetime(2026, 3, 15, tzinfo=UTC)
    assert "45000000" in award.cpv_codes
    assert "45233000" in award.cpv_codes
    assert "EL30" in award.nuts
    assert award.tender_ref == "6ΩΒΝ4653ΠΩ-ΑΒΓ"
    assert award.raw_doc_uri is not None
    assert "diavgeia" in award.raw_doc_uri


def test_normalize_missing_optional_fields(diavgeia_source):
    payload = {
        "ada": "ΑΒΓΔ-001",
        "issuer": {"label": "Region of Attica"},
        "publishedDate": "2026-01-10",
        "extraFields": {
            "supplierName": "Unknown Supplier",
            "amountWithVat": "50000",
        },
    }
    raw = RawAward(source=AwardSource.DIAVGEIA, payload=payload)
    award = diavgeia_source.normalize(raw)

    assert award.supplier_vat is None
    assert award.cpv_codes == []
    assert award.nuts == []
    assert award.raw_doc_uri is None


def test_normalize_issuer_string(diavgeia_source):
    payload = {
        "ada": "TEST-002",
        "issuer": "Flat Authority String",
        "publishedDate": "2026-02-01",
        "extraFields": {"supplierName": "Supplier B", "amountWithVat": "10000"},
    }
    raw = RawAward(source=AwardSource.DIAVGEIA, payload=payload)
    award = diavgeia_source.normalize(raw)

    assert award.contracting_authority == "Flat Authority String"


def test_normalize_cpv_single_string(diavgeia_source):
    payload = {
        "ada": "TEST-003",
        "issuer": {"label": "Authority"},
        "publishedDate": "2026-02-01",
        "extraFields": {
            "supplierName": "Supplier C",
            "amountWithVat": "5000",
            "cpvCode": "72000000",
        },
    }
    raw = RawAward(source=AwardSource.DIAVGEIA, payload=payload)
    award = diavgeia_source.normalize(raw)

    assert award.cpv_codes == ["72000000"]


def test_normalize_invalid_amount_defaults_to_zero(diavgeia_source):
    payload = {
        "ada": "TEST-004",
        "issuer": {"label": "Authority"},
        "publishedDate": "2026-03-01",
        "extraFields": {"supplierName": "Supplier D", "amountWithVat": "n/a"},
    }
    raw = RawAward(source=AwardSource.DIAVGEIA, payload=payload)
    award = diavgeia_source.normalize(raw)

    assert award.award_value == Decimal("0")
