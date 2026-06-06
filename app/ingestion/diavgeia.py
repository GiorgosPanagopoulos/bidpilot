from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import httpx

from app.core.exceptions import AwardIngestionError, SourceUnavailableError
from app.models.award import Award, AwardSource, RawAward

logger = logging.getLogger(__name__)

# ΔΙΑΥΓΕΙΑ opendata REST API — contract/award decision search
# TODO: verify exact base URL path against live ΔΙΑΥΓΕΙΑ opendata documentation
_BASE_URL = "https://diavgeia.gov.gr/opendata"
_SEARCH_PATH = "/search"

# Decision type codes that represent contract awards on ΔΙΑΥΓΕΙΑ.
# TODO: verify this list is exhaustive against live API decision-type catalogue
_AWARD_TYPES = ["ΣΣ", "ΑΝΑΘΕΣΗ", "ΚΑΤΑΚΥΡΩΣΗ"]


class DiavgeiaSource:
    def __init__(self, base_url: str | None = None) -> None:
        self._base = (base_url or _BASE_URL).rstrip("/")

    async def _search(self, params: dict) -> list[dict]:
        url = f"{self._base}{_SEARCH_PATH}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                # TODO: verify top-level result key name in live API response
                return data.get("decisions", data.get("results", []))
        except httpx.HTTPStatusError as exc:
            raise SourceUnavailableError(f"ΔΙΑΥΓΕΙΑ API error {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise SourceUnavailableError(f"ΔΙΑΥΓΕΙΑ network error: {exc}") from exc

    async def fetch(self, since: datetime) -> list[RawAward]:
        since_str = since.strftime("%Y-%m-%d")
        all_raw: list[RawAward] = []
        for decision_type in _AWARD_TYPES:
            params = {
                "type": decision_type,
                "from_date": since_str,
                "page": 0,
                "size": 500,
            }
            try:
                records = await self._search(params)
            except SourceUnavailableError:
                raise
            except Exception as exc:
                raise AwardIngestionError(str(exc)) from exc
            all_raw.extend(RawAward(source=AwardSource.DIAVGEIA, payload=r) for r in records)
        return all_raw

    def normalize(self, raw: RawAward) -> Award:
        p = raw.payload
        # TODO: verify "ada" is the stable unique decision identifier in live responses
        ada = str(p.get("ada", p.get("id", "")))
        # TODO: verify issuer structure — live API may nest it as {"uid": ..., "label": ...}
        issuer = p.get("issuer") or {}
        if isinstance(issuer, dict):
            contracting_authority = issuer.get("label") or "Unknown"
        else:
            contracting_authority = str(issuer) or "Unknown"
        # TODO: verify extraFields structure for supplier and financial data
        extra: dict = p.get("extraFields") or {}
        supplier_name = str(extra.get("supplierName", extra.get("supplier_name", "Unknown")))
        supplier_vat = _coerce_str(extra.get("supplierVat", extra.get("supplier_vat")))
        # TODO: verify amount field name — live API may use "amountWithVat" or "totalAmount"
        award_value = _parse_decimal(
            extra.get("amountWithVat", extra.get("totalAmount", "0"))
        ) or Decimal("0")
        currency = str(extra.get("currency", "EUR")) or "EUR"
        # TODO: verify publishedDate format in live responses (ISO 8601 or epoch ms)
        award_date = _parse_date(p.get("publishedDate") or p.get("award_date"))
        # TODO: verify CPV code field name in extraFields
        cpv_raw = extra.get("cpvCode", extra.get("cpv_codes", []))
        if isinstance(cpv_raw, str):
            cpv_codes = [cpv_raw] if cpv_raw else []
        elif isinstance(cpv_raw, list):
            cpv_codes = [str(c) for c in cpv_raw]
        else:
            cpv_codes = []
        # TODO: verify NUTS field presence and structure in live API responses
        nuts_raw = extra.get("nuts", [])
        nuts = [str(n) for n in nuts_raw] if isinstance(nuts_raw, list) else []
        raw_doc_uri_str = str(p.get("documentUrl", ""))
        raw_doc_uri: str | None = raw_doc_uri_str if raw_doc_uri_str else None

        return Award(
            id=f"diavgeia-{ada}",
            source="DIAVGEIA",
            cpv_codes=cpv_codes,
            contracting_authority=contracting_authority,
            supplier_name=supplier_name,
            supplier_vat=supplier_vat,
            award_value=award_value,
            currency=currency,
            award_date=award_date,
            nuts=nuts,
            tender_ref=ada if ada else None,
            raw_doc_uri=raw_doc_uri,
        )


class KimdisSource:
    """Placeholder connector for ΚΙΜΔΙΣ procurement portal. Not yet implemented."""

    async def fetch(self, since: datetime) -> list[RawAward]:
        raise SourceUnavailableError("ΚΙΜΔΙΣ source is not yet implemented")

    def normalize(self, raw: RawAward) -> Award:
        raise SourceUnavailableError("ΚΙΜΔΙΣ source is not yet implemented")


def _coerce_str(value: object) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _parse_date(value: object) -> datetime:
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
        # epoch milliseconds string
        try:
            return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
        except (ValueError, OSError):
            pass
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value / 1000, tz=UTC)
        except (ValueError, OSError):
            pass
    return datetime.now(UTC)


def _parse_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None
