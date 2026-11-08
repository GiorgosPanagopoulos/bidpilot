from fastapi import APIRouter, Depends

from app.api.deps import ensure_own_company, get_current_user, require_admin
from app.models.company import CompanyProfile
from app.models.user import User
from app.repositories.audit import fire_and_forget
from app.repositories.companies import get_company, upsert_company

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyProfile, status_code=201)
async def create_company(
    profile: CompanyProfile,
    user: User = Depends(require_admin),
) -> CompanyProfile:
    # An admin only ever writes their own company's profile, whatever id the body carries.
    profile = profile.model_copy(update={"id": user.company_id})
    result = await upsert_company(profile)
    fire_and_forget("company.upsert", {"id": result.id})
    return result


@router.get("/{company_id}", response_model=CompanyProfile)
async def read_company(
    company_id: str,
    user: User = Depends(get_current_user),
) -> CompanyProfile:
    ensure_own_company(company_id, user)
    return await get_company(company_id)
