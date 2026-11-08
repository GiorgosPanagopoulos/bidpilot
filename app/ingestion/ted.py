from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.core.exceptions import SourceUnavailableError, TenderIngestionError
from app.core.settings import settings
from app.models.tender import RawTender, Tender, TenderSource, TenderStatus

logger = logging.getLogger(__name__)

# TED Search API v3, expert-query endpoint. Field names verified against a live response (Nov 2026).
_SEARCH_PATH = "/notices/search"
_FIELDS = [
    "publication-number",
    "notice-title",
    "description-proc",
    "classification-cpv",
    "place-of-performance",
    "deadline-receipt-tender-date-lot",
    "estimated-value-proc",
    "estimated-value-cur-proc",
    "buyer-country",
    "links",
]
_PAGE_LIMIT = 250
# Multilingual fields come keyed by ISO 639-3 code; Greek suppliers read Greek first.
_LANG_PREFERENCE = ("ell", "eng")
_LINK_LANG_PREFERENCE = ("ELL", "ENG")
# NUTS codes are two letters then a digit-led suffix (EL3, EL307); country codes (GRC) are dropped.
_NUTS_RE = re.compile(r"^[A-Z]{2}[0-9][0-9A-Z]{0,2}$")
_DATE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})(T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?(Z|[+-]\d{2}:\d{2})?$"
)


class TEDSource:
    def __init__(self, base_url: str | None = None) -> None:
        self._base = (base_url or settings.ted_api_base).rstrip("/")

    async def _search(self, body: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"{self._base}{_SEARCH_PATH}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=body)
                resp.raise_for_status()
                return list(resp.json().get("notices", []))
        except httpx.HTTPStatusError as exc:
            # TED explains rejected queries in the body; keep it for the logs.
            logger.error(
                "TED search failed: %s %s", exc.response.status_code, exc.response.text[:500]
            )
            raise SourceUnavailableError(f"TED API error {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise SourceUnavailableError(f"TED network error: {exc}") from exc

    @staticmethod
    def build_query(since: datetime, country: str = "") -> dict[str, Any]:
        query = f"publication-date>={since.strftime('%Y%m%d')}"
        if country:
            query += f" AND buyer-country={country}"
        return {"query": query, "fields": _FIELDS, "limit": _PAGE_LIMIT, "page": 1}

    async def fetch(self, since: datetime) -> list[RawTender]:
        body = self.build_query(since, settings.ted_buyer_country)
        try:
            notices = await self._search(body)
        except SourceUnavailableError:
            raise
        except Exception as exc:
            raise TenderIngestionError(str(exc)) from exc
        return [RawTender(source=TenderSource.TED, payload=n) for n in notices]

    def normalize(self, raw: RawTender) -> Tender:
        p = raw.payload
        notice_id = str(p.get("publication-number") or "").strip()
        if not notice_id:
            raise ValueError("notice without publication-number")
        deadline = _parse_deadline(p.get("deadline-receipt-tender-date-lot"))
        if deadline is None:
            # Award and result notices carry no submission deadline: nothing to bid on.
            raise ValueError(f"notice {notice_id} has no tender deadline")
        return Tender(
            id=f"ted-{notice_id}",
            source="TED",
            title=_pick_lang(p.get("notice-title")) or "Untitled",
            cpv_codes=_unique(_as_list(p.get("classification-cpv"))),
            budget=_parse_decimal(p.get("estimated-value-proc")),
            deadline=deadline,
            nuts=[c for c in _unique(_as_list(p.get("place-of-performance"))) if _NUTS_RE.match(c)],
            description=_pick_lang(p.get("description-proc")) or "",
            raw_doc_uri=_pick_link(p.get("links")),
            status=TenderStatus.OPEN if deadline > datetime.now(UTC) else TenderStatus.CLOSED,
        )


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v.strip() for v in values if v.strip()))


def _pick_lang(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return _pick_lang(value[0]) if value else None
    if isinstance(value, dict) and value:
        for lang in _LANG_PREFERENCE:
            if value.get(lang):
                return _pick_lang(value[lang])
        return _pick_lang(next(iter(value.values())))
    return None


def _pick_link(links: object) -> str:
    if not isinstance(links, dict):
        return ""
    pdf = links.get("pdf")
    if isinstance(pdf, dict) and pdf:
        for lang in _LINK_LANG_PREFERENCE:
            if pdf.get(lang):
                return str(pdf[lang])
        return str(next(iter(pdf.values())))
    return ""


def _parse_date(value: str) -> datetime | None:
    m = _DATE_RE.match(value.strip())
    if not m:
        return None
    day, time, tz = m.groups()
    iso = day + (time or "T23:59:59") + ("+00:00" if tz in (None, "Z") else tz)
    try:
        return datetime.fromisoformat(iso).astimezone(UTC)
    except ValueError:
        return None


def _parse_deadline(value: object) -> datetime | None:
    # Multi-lot notices list one deadline per lot; the earliest is the binding one.
    dates = [d for d in (_parse_date(v) for v in _as_list(value)) if d is not None]
    return min(dates) if dates else None


def _parse_decimal(value: object) -> Decimal | None:
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None
