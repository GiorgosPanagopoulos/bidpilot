import pytest

from app.ingestion.ted import TEDSource
from app.models.tender import RawTender, TenderSource


@pytest.fixture()
def ted_source() -> TEDSource:
    return TEDSource(base_url="http://localhost")


def test_normalize_basic(ted_source, ted_notice_payload):
    raw = RawTender(source=TenderSource.TED, payload=ted_notice_payload)
    tender = ted_source.normalize(raw)
    assert tender.id == "ted-12345678"
    assert tender.source == "TED"
    assert tender.title == "Road Construction Services"
    assert "45000000" in tender.cpv_codes
    assert "45233000" in tender.cpv_codes
    assert "EL30" in tender.nuts
    assert tender.budget is not None
    assert str(tender.budget) == "3500000"
    assert tender.status.value == "open"
    assert tender.raw_doc_uri == "https://ted.europa.eu/en/notice/12345678"
    assert tender.deadline.tzinfo is not None


def test_normalize_missing_optional_fields(ted_source):
    payload = {"ND": "99999", "DD": "20261231"}
    raw = RawTender(source=TenderSource.TED, payload=payload)
    tender = ted_source.normalize(raw)
    assert tender.id == "ted-99999"
    assert tender.title == "Untitled"
    assert tender.cpv_codes == []
    assert tender.budget is None
    assert tender.nuts == []


def test_normalize_cpv_single_string(ted_source):
    payload = {"ND": "1", "DD": "20261231", "PC": "45000000"}
    raw = RawTender(source=TenderSource.TED, payload=payload)
    tender = ted_source.normalize(raw)
    assert tender.cpv_codes == ["45000000"]


def test_normalize_invalid_budget(ted_source):
    payload = {"ND": "2", "DD": "20261231", "TVA": "n/a"}
    raw = RawTender(source=TenderSource.TED, payload=payload)
    tender = ted_source.normalize(raw)
    assert tender.budget is None
