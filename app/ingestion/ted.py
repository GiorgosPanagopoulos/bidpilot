from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx

from app.core.exceptions import SourceUnavailableError, TenderIngestionError
from app.core.settings import settings
from app.models.tender import RawTender, Tender, TenderSource, TenderStatus

logger = logging.getLogger(__name__)

# TED eForms Search API v3 — notices endpoint
# TODO: verify exact field names against live TED API response schema
_SEARCH_PATH = "/notices/search"


class TEDSource:
    def __init__(self, base_url: str | None = None) -> None:
        self._base = (base_url or settings.ted_api_base).rstrip("/")

    async def _search(self, params: dict) -> list[dict]:
        url = f"{self._base}{_SEARCH_PATH}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("notices", [])
        except httpx.HTTPStatusError as exc:
            raise SourceUnavailableError(f"TED API error {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise SourceUnavailableError(f"TED network error: {exc}") from exc

    async def fetch(self, since: datetime) -> list[RawTender]:
        since_str = since.strftime("%Y%m%d")
        params = {
            "query": f"publication-date>={since_str}",
            "fields": ["ND", "TI", "PC", "TE", "TW", "DD", "TVA", "CY"],
            "limit": 250,
            "page": 1,
        }
        try:
            notices = await self._search(params)
        except SourceUnavailableError:
            raise
        except Exception as exc:
            raise TenderIngestionError(str(exc)) from exc
        return [RawTender(source=TenderSource.TED, payload=n) for n in notices]

    def normalize(self, raw: RawTender) -> Tender:
        p = raw.payload
        # TODO: verify "ND" is the unique notice identifier in live responses
        notice_id = str(p.get("ND", p.get("id", "")))
        # TODO: verify "TI" maps to the English title in multi-lang responses
        title = _first_str(p.get("TI")) or "Untitled"
        # TODO: verify "PC" maps to CPV code list
        cpv_raw = p.get("PC", [])
        cpv_codes = [str(c) for c in (cpv_raw if isinstance(cpv_raw, list) else [cpv_raw])]
        # TODO: verify "TW" maps to NUTS codes
        nuts_raw = p.get("TW", [])
        nuts = [str(n) for n in (nuts_raw if isinstance(nuts_raw, list) else [nuts_raw])]
        # TODO: verify "DD" is deadline in YYYYMMDD format
        deadline = _parse_date(p.get("DD"))
        # TODO: verify "TVA" holds total value amount
        budget = _parse_decimal(p.get("TVA"))
        # TODO: verify "TE" holds the full notice description
        description = _first_str(p.get("TE")) or ""
        raw_doc_uri = str(p.get("uri", ""))
        return Tender(
            id=f"ted-{notice_id}",
            source="TED",
            title=title,
            cpv_codes=cpv_codes,
            budget=budget,
            deadline=deadline,
            nuts=nuts,
            description=description,
            raw_doc_uri=raw_doc_uri,
            status=TenderStatus.OPEN,
        )


def _first_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, dict):
        return next(iter(value.values()), None)
    return None


def _parse_date(value: object) -> datetime:
    if isinstance(value, str):
        for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


def _parse_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None
