from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.matching.matcher import (
    _budget_feasible,
    _cpv_overlap,
    _deadline_future,
    _nuts_match,
    _rule_score_and_reasons,
)


def test_cpv_overlap_partial():
    assert _cpv_overlap(["45000000", "72000000"], "45000000,99000000") == 1


def test_cpv_overlap_none():
    assert _cpv_overlap(["45000000"], "72000000") == 0


def test_cpv_overlap_full():
    assert _cpv_overlap(["45000000", "72000000"], "45000000,72000000") == 2


def test_nuts_match_hit():
    assert _nuts_match(["EL30", "EL41"], "EL30,DE111") is True


def test_nuts_match_miss():
    assert _nuts_match(["EL30"], "DE111") is False


def test_budget_feasible_within():
    assert _budget_feasible("2000000", Decimal("5000000"), 2.0) is True


def test_budget_feasible_over():
    assert _budget_feasible("15000000", Decimal("5000000"), 2.0) is False


def test_budget_feasible_empty():
    assert _budget_feasible("", Decimal("5000000"), 2.0) is True


def test_deadline_future():
    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    assert _deadline_future(future) is True


def test_deadline_past():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    assert _deadline_future(past) is False


def test_rule_score_open_tender(sample_company, open_tender_meta):
    rule_score, reasons, eligibility = _rule_score_and_reasons(sample_company, open_tender_meta)
    assert eligibility.passed is True
    assert rule_score > 0.0
    assert any("CPV" in r for r in reasons)


def test_rule_score_deadline_failed(sample_company, closed_tender_meta):
    _, _, eligibility = _rule_score_and_reasons(sample_company, closed_tender_meta)
    assert eligibility.passed is False
    assert "deadline passed" in eligibility.failed_criteria


def test_rule_score_no_cpv(sample_company, open_tender_meta):
    meta = {**open_tender_meta, "cpv": "99999999"}
    _, _, eligibility = _rule_score_and_reasons(sample_company, meta)
    assert eligibility.passed is False
    assert "no CPV overlap" in eligibility.failed_criteria
