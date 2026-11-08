from datetime import UTC, datetime

import pytest

from app.ingestion.ted import TEDSource
from app.models.tender import RawTender, TenderSource


@pytest.fixture()
def ted_source() -> TEDSource:
    return TEDSource(base_url="http://localhost")


def _norm(source: TEDSource, payload: dict):
    return source.normalize(RawTender(source=TenderSource.TED, payload=payload))


def test_normalize_live_shape(ted_source, ted_notice_payload):
    tender = _norm(ted_source, ted_notice_payload)

    assert tender.id == "ted-756583-2026"
    assert tender.source == "TED"
    assert tender.title == "Ελλάδα - Μοντέλα θαλάσσιων σκαφών"
    assert tender.description == "Μουσείο Εναλίων Αρχαιοτήτων"
    assert tender.cpv_codes == ["34999420", "92311000"]
    assert tender.nuts == ["EL307"]
    assert str(tender.budget) == "3500000"
    assert tender.raw_doc_uri == "https://ted.europa.eu/el/notice/756583-2026/pdf"
    assert tender.deadline.tzinfo is not None
    assert tender.status.value == "open"


def test_title_falls_back_to_english_then_any(ted_source, ted_notice_payload):
    ted_notice_payload["notice-title"] = {"eng": "English title", "deu": "Deutsch"}
    assert _norm(ted_source, ted_notice_payload).title == "English title"

    ted_notice_payload["notice-title"] = {"deu": "Deutsch"}
    assert _norm(ted_source, ted_notice_payload).title == "Deutsch"


def test_deadline_offset_and_earliest_lot(ted_source, ted_notice_payload):
    ted_notice_payload["deadline-receipt-tender-date-lot"] = [
        "2099-03-10+02:00",
        "2099-03-05T10:00:00+02:00",
        "2099-03-07Z",
    ]

    tender = _norm(ted_source, ted_notice_payload)

    assert tender.deadline == datetime(2099, 3, 5, 8, 0, tzinfo=UTC)


def test_past_deadline_is_closed(ted_source, ted_notice_payload):
    ted_notice_payload["deadline-receipt-tender-date-lot"] = ["2020-01-01+02:00"]

    assert _norm(ted_source, ted_notice_payload).status.value == "closed"


def test_notice_without_deadline_is_rejected(ted_source, ted_notice_payload):
    del ted_notice_payload["deadline-receipt-tender-date-lot"]

    with pytest.raises(ValueError, match="no tender deadline"):
        _norm(ted_source, ted_notice_payload)


def test_missing_optional_fields(ted_source):
    tender = _norm(
        ted_source,
        {"publication-number": "1-2026", "deadline-receipt-tender-date-lot": "2099-01-01Z"},
    )

    assert tender.title == "Untitled"
    assert tender.cpv_codes == []
    assert tender.nuts == []
    assert tender.budget is None
    assert tender.raw_doc_uri == ""


def test_invalid_budget(ted_source, ted_notice_payload):
    ted_notice_payload["estimated-value-proc"] = "n/a"

    assert _norm(ted_source, ted_notice_payload).budget is None


def test_query_filters_by_buyer_country():
    body = TEDSource.build_query(datetime(2026, 11, 1, tzinfo=UTC), "GRC")

    assert body["query"] == "publication-date>=20261101 AND buyer-country=GRC"
    assert "publication-number" in body["fields"]
    assert body["limit"] == 250

    assert TEDSource.build_query(datetime(2026, 11, 1, tzinfo=UTC))["query"] == (
        "publication-date>=20261101"
    )
