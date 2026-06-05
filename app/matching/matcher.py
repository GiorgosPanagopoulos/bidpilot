from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from app.core.exceptions import MatchingError
from app.core.settings import settings
from app.models.company import CompanyProfile
from app.models.match import EligibilityCheck, MatchResult
from app.vectorstore.chroma import query_tenders

logger = logging.getLogger(__name__)


def _build_query(profile: CompanyProfile) -> str:
    parts = [profile.name]
    parts.extend(profile.cpv_codes)
    parts.extend(profile.capacity_tags)
    parts.extend(profile.regions)
    return " ".join(parts)


def _cpv_overlap(profile_cpvs: list[str], tender_cpv_str: str) -> int:
    tender_cpvs = set(c.strip() for c in tender_cpv_str.split(",") if c.strip())
    return len(set(profile_cpvs) & tender_cpvs)


def _nuts_match(profile_regions: list[str], tender_nuts_str: str) -> bool:
    tender_nuts = set(n.strip() for n in tender_nuts_str.split(",") if n.strip())
    return bool(set(profile_regions) & tender_nuts)


def _budget_feasible(budget_str: str, turnover: Decimal, factor: float) -> bool:
    if not budget_str:
        return True
    try:
        budget = Decimal(budget_str)
        return budget <= turnover * Decimal(str(factor))
    except Exception:
        return True


def _deadline_future(deadline_str: str) -> bool:
    try:
        dl = datetime.fromisoformat(deadline_str)
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=timezone.utc)
        return dl > datetime.now(timezone.utc)
    except Exception:
        return False


def _rule_score_and_reasons(
    profile: CompanyProfile,
    meta: dict,
) -> tuple[float, list[str], EligibilityCheck]:
    reasons: list[str] = []
    failed: list[str] = []
    warnings: list[str] = []

    # hard criteria
    if not _deadline_future(meta.get("deadline", "")):
        failed.append("deadline passed")
    if meta.get("status", "open") != "open":
        failed.append("tender not open")
    overlap = _cpv_overlap(profile.cpv_codes, meta.get("cpv", ""))
    if overlap == 0:
        failed.append("no CPV overlap")

    passed = len(failed) == 0

    # soft criteria
    score = 0.0

    profile_cpv_count = max(len(profile.cpv_codes), 1)
    tender_cpvs = [c for c in meta.get("cpv", "").split(",") if c.strip()]
    tender_cpv_count = max(len(tender_cpvs), 1)
    cpv_ratio = overlap / min(profile_cpv_count, tender_cpv_count)
    score += 0.5 * cpv_ratio
    if cpv_ratio > 0:
        reasons.append(f"CPV overlap {overlap} code(s) ({cpv_ratio:.0%})")

    nuts_hit = _nuts_match(profile.regions, meta.get("nuts", ""))
    score += 0.3 * (1.0 if nuts_hit else 0.0)
    if nuts_hit:
        reasons.append("NUTS region match")
    else:
        warnings.append("no NUTS region overlap")

    feasible = _budget_feasible(
        meta.get("budget", ""),
        profile.annual_turnover,
        settings.budget_feasibility_factor,
    )
    score += 0.2 * (1.0 if feasible else 0.0)
    if feasible:
        reasons.append("budget within capacity")
    else:
        warnings.append("budget may exceed capacity")

    eligibility = EligibilityCheck(passed=passed, failed_criteria=failed, warnings=warnings)
    return score, reasons, eligibility


async def run_matching(profile: CompanyProfile) -> list[MatchResult]:
    try:
        query = _build_query(profile)
        candidates = query_tenders(query, top_k=settings.match_top_k)
    except Exception as exc:
        raise MatchingError(f"vector query failed: {exc}") from exc

    results: list[MatchResult] = []
    for candidate in candidates:
        tid = candidate["id"]
        meta = candidate["metadata"]
        distance = candidate.get("distance", 1.0)
        semantic_score = max(0.0, 1.0 - float(distance))

        rule_score, reasons, eligibility = _rule_score_and_reasons(profile, meta)

        if not eligibility.passed:
            continue

        final_score = (
            settings.weight_semantic * semantic_score
            + settings.weight_rule * rule_score
        )
        results.append(
            MatchResult(
                tender_id=tid,
                company_id=profile.id,
                score=final_score,
                semantic_score=semantic_score,
                rule_score=rule_score,
                reasons=reasons,
                eligibility=eligibility,
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results
