from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Literal

from app.models.award import Award, PricingStats, SupplierWinRate, TrendPoint, TrendSeries

_ZERO = Decimal("0")


def compute_pricing_stats(awards: list[Award], cpv: str | None = None) -> PricingStats:
    """Compute min/max/mean/median/p25/p75 over award_value.

    Mixed-currency awards are skipped; only EUR values are included unless all
    awards share a single currency, in which case that currency is used.
    """
    if not awards:
        return PricingStats(
            cpv=cpv,
            count=0,
            min=None,
            max=None,
            mean=None,
            median=None,
            p25=None,
            p75=None,
            currency="EUR",
        )

    # Determine reference currency: majority currency wins; default EUR.
    currency_counts: dict[str, int] = defaultdict(int)
    for a in awards:
        currency_counts[a.currency] += 1
    ref_currency = max(currency_counts, key=lambda c: currency_counts[c])

    values = sorted(a.award_value for a in awards if a.currency == ref_currency)

    if not values:
        return PricingStats(
            cpv=cpv,
            count=0,
            min=None,
            max=None,
            mean=None,
            median=None,
            p25=None,
            p75=None,
            currency=ref_currency,
        )

    n = len(values)
    total = sum(values, _ZERO)

    return PricingStats(
        cpv=cpv,
        count=n,
        min=values[0],
        max=values[-1],
        mean=total / n,
        median=_percentile(values, 0.5),
        p25=_percentile(values, 0.25),
        p75=_percentile(values, 0.75),
        currency=ref_currency,
    )


def compute_win_rates(
    awards: list[Award],
    top_n: int | None = None,
) -> list[SupplierWinRate]:
    """Compute per-supplier award counts and values, sorted by awards_won descending."""
    if not awards:
        return []

    totals: dict[str, Decimal] = defaultdict(lambda: _ZERO)
    counts: dict[str, int] = defaultdict(int)
    vats: dict[str, str | None] = {}

    for a in awards:
        key = a.supplier_name
        counts[key] += 1
        totals[key] += a.award_value
        vats.setdefault(key, a.supplier_vat)

    total_awards = len(awards)
    rates = [
        SupplierWinRate(
            supplier_name=name,
            supplier_vat=vats[name],
            awards_won=counts[name],
            total_value=totals[name],
            win_share=counts[name] / total_awards,
        )
        for name in counts
    ]
    rates.sort(key=lambda r: r.awards_won, reverse=True)

    if top_n is not None:
        rates = rates[:top_n]

    return rates


def compute_trends(
    awards: list[Award],
    interval: Literal["month", "quarter", "year"],
) -> TrendSeries:
    """Bucket awards by award_date into period strings and compute count/total/mean per bucket."""
    buckets: dict[str, list[Decimal]] = defaultdict(list)

    for a in awards:
        period = _period_key(a.award_date, interval)
        buckets[period].append(a.award_value)

    points: list[TrendPoint] = []
    for period in sorted(buckets):
        vals = buckets[period]
        n = len(vals)
        total = sum(vals, _ZERO)
        points.append(
            TrendPoint(
                period=period,
                count=n,
                total_value=total,
                mean_value=total / n,
            )
        )

    return TrendSeries(interval=interval, points=points)


def _percentile(sorted_values: list[Decimal], p: float) -> Decimal:
    n = len(sorted_values)
    # Nearest-rank method; clamp to valid index range.
    idx = max(0, min(n - 1, int(p * n)))
    return sorted_values[idx]


def _period_key(dt, interval: Literal["month", "quarter", "year"]) -> str:  # type: ignore[no-untyped-def]
    if interval == "month":
        return dt.strftime("%Y-%m")
    if interval == "quarter":
        q = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{q}"
    return str(dt.year)
