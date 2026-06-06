from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.models.award import Award
from app.services.analytics import compute_win_rates


def _award(supplier: str, value: str, vat: str | None = None) -> Award:
    return Award(
        source="DIAVGEIA",
        contracting_authority="Authority",
        supplier_name=supplier,
        supplier_vat=vat,
        award_value=Decimal(value),
        currency="EUR",
        award_date=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_win_rates_ordering():
    awards = [
        _award("Alpha", "100"),
        _award("Beta", "200"),
        _award("Alpha", "300"),
        _award("Gamma", "50"),
        _award("Alpha", "150"),
    ]
    rates = compute_win_rates(awards)

    assert rates[0].supplier_name == "Alpha"
    assert rates[0].awards_won == 3
    assert rates[0].total_value == Decimal("550")
    assert rates[1].awards_won == 1
    assert rates[2].awards_won == 1


def test_win_rates_win_share():
    awards = [_award("A", "100"), _award("A", "200"), _award("B", "300")]
    rates = compute_win_rates(awards)

    a_rate = next(r for r in rates if r.supplier_name == "A")
    b_rate = next(r for r in rates if r.supplier_name == "B")
    assert a_rate.win_share == pytest.approx(2 / 3)
    assert b_rate.win_share == pytest.approx(1 / 3)
    assert a_rate.win_share + b_rate.win_share == pytest.approx(1.0)


def test_win_rates_top_n():
    awards = [
        _award("A", "100"),
        _award("A", "100"),
        _award("B", "100"),
        _award("C", "100"),
    ]
    rates = compute_win_rates(awards, top_n=2)

    assert len(rates) == 2
    assert rates[0].supplier_name == "A"


def test_win_rates_supplier_vat_preserved():
    awards = [_award("Supplier X", "1000", vat="EL999999999")]
    rates = compute_win_rates(awards)

    assert rates[0].supplier_vat == "EL999999999"


def test_win_rates_empty():
    assert compute_win_rates([]) == []


def test_win_rates_single():
    awards = [_award("Solo", "500")]
    rates = compute_win_rates(awards)

    assert len(rates) == 1
    assert rates[0].win_share == pytest.approx(1.0)
