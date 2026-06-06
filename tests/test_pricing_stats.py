from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.models.award import Award
from app.services.analytics import compute_pricing_stats


def _award(value: str, currency: str = "EUR") -> Award:
    return Award(
        source="DIAVGEIA",
        contracting_authority="Auth",
        supplier_name="Supplier",
        award_value=Decimal(value),
        currency=currency,
        award_date=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_pricing_stats_basic():
    awards = [_award("100"), _award("200"), _award("300"), _award("400")]
    stats = compute_pricing_stats(awards)

    assert stats.count == 4
    assert stats.min == Decimal("100")
    assert stats.max == Decimal("400")
    assert stats.mean == Decimal("250")
    assert stats.currency == "EUR"
    # p25 at index 1 of sorted [100, 200, 300, 400]
    assert stats.p25 == Decimal("200")
    # median at index 2
    assert stats.median == Decimal("300")
    # p75 at index 3
    assert stats.p75 == Decimal("400")


def test_pricing_stats_single():
    stats = compute_pricing_stats([_award("500")])

    assert stats.count == 1
    assert stats.min == Decimal("500")
    assert stats.max == Decimal("500")
    assert stats.mean == Decimal("500")
    assert stats.median == Decimal("500")
    assert stats.p25 == Decimal("500")
    assert stats.p75 == Decimal("500")


def test_pricing_stats_with_cpv_filter():
    awards = [_award("1000"), _award("2000")]
    stats = compute_pricing_stats(awards, cpv="45000000")

    assert stats.cpv == "45000000"
    assert stats.count == 2


def test_pricing_stats_mixed_currency_skips_minority():
    # 3 EUR, 1 USD — USD award should be excluded
    awards = [
        _award("100", "EUR"),
        _award("200", "EUR"),
        _award("300", "EUR"),
        _award("9999", "USD"),
    ]
    stats = compute_pricing_stats(awards)

    assert stats.currency == "EUR"
    assert stats.count == 3
    assert stats.max == Decimal("300")


def test_pricing_stats_empty():
    stats = compute_pricing_stats([])

    assert stats.count == 0
    assert stats.min is None
    assert stats.max is None
    assert stats.mean is None
    assert stats.median is None
    assert stats.p25 is None
    assert stats.p75 is None


def test_pricing_stats_empty_cpv_is_none():
    stats = compute_pricing_stats([])

    assert stats.cpv is None
