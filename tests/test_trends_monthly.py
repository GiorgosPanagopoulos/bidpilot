from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.models.award import Award
from app.services.analytics import compute_trends


def _award(year: int, month: int, value: str) -> Award:
    return Award(
        source="DIAVGEIA",
        contracting_authority="Authority",
        supplier_name="Supplier",
        award_value=Decimal(value),
        currency="EUR",
        award_date=datetime(year, month, 15, tzinfo=UTC),
    )


def test_trends_monthly_buckets():
    awards = [
        _award(2026, 1, "100"),
        _award(2026, 1, "200"),
        _award(2026, 2, "500"),
        _award(2026, 3, "300"),
    ]
    series = compute_trends(awards, interval="month")

    assert series.interval == "month"
    periods = [p.period for p in series.points]
    assert periods == ["2026-01", "2026-02", "2026-03"]

    jan = next(p for p in series.points if p.period == "2026-01")
    assert jan.count == 2
    assert jan.total_value == Decimal("300")
    assert jan.mean_value == Decimal("150")

    feb = next(p for p in series.points if p.period == "2026-02")
    assert feb.count == 1
    assert feb.total_value == Decimal("500")
    assert feb.mean_value == Decimal("500")


def test_trends_quarterly_buckets():
    awards = [
        _award(2026, 1, "100"),
        _award(2026, 4, "200"),
        _award(2026, 7, "300"),
        _award(2026, 10, "400"),
    ]
    series = compute_trends(awards, interval="quarter")

    assert series.interval == "quarter"
    periods = [p.period for p in series.points]
    assert "2026-Q1" in periods
    assert "2026-Q2" in periods
    assert "2026-Q3" in periods
    assert "2026-Q4" in periods
    assert len(series.points) == 4


def test_trends_yearly_buckets():
    awards = [
        _award(2024, 6, "100"),
        _award(2025, 3, "200"),
        _award(2025, 9, "300"),
    ]
    series = compute_trends(awards, interval="year")

    assert series.interval == "year"
    periods = [p.period for p in series.points]
    assert periods == ["2024", "2025"]

    y2025 = next(p for p in series.points if p.period == "2025")
    assert y2025.count == 2
    assert y2025.total_value == Decimal("500")


def test_trends_empty():
    series = compute_trends([], interval="month")

    assert series.interval == "month"
    assert series.points == []


def test_trends_sorted_ascending():
    awards = [
        _award(2026, 6, "100"),
        _award(2026, 1, "200"),
        _award(2026, 3, "300"),
    ]
    series = compute_trends(awards, interval="month")

    periods = [p.period for p in series.points]
    assert periods == sorted(periods)
