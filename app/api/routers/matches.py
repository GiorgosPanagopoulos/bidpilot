from fastapi import APIRouter, Depends, Query

from app.api.deps import ensure_own_company, get_current_user, require_writer
from app.matching.eligibility import engine
from app.matching.matcher import run_matching
from app.models.match import MatchResult
from app.models.user import User
from app.repositories.audit import fire_and_forget
from app.repositories.companies import get_company
from app.repositories.matches import list_matches, upsert_match

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/run", response_model=list[MatchResult])
async def compute_matches(
    company_id: str = Query(...),
    user: User = Depends(require_writer),
) -> list[MatchResult]:
    ensure_own_company(company_id, user)
    profile = await get_company(company_id)
    results = await run_matching(profile)
    for r in results:
        await upsert_match(r)
    fire_and_forget(
        "matches.run",
        {"company_id": company_id, "count": len(results), "rule_version": engine.rule_version},
    )
    return results


@router.get("", response_model=list[MatchResult])
async def get_matches(
    company_id: str = Query(...),
    user: User = Depends(get_current_user),
) -> list[MatchResult]:
    ensure_own_company(company_id, user)
    return await list_matches(company_id)
