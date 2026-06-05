from fastapi import APIRouter, Depends

from app.api.deps import set_tenant
from app.models.company import CompanyProfile
from app.repositories.audit import fire_and_forget
from app.repositories.companies import get_company, upsert_company

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyProfile, status_code=201)
async def create_company(
    profile: CompanyProfile,
    _: None = Depends(set_tenant),
) -> CompanyProfile:
    result = await upsert_company(profile)
    fire_and_forget("company.upsert", {"id": result.id})
    return result


@router.get("/{company_id}", response_model=CompanyProfile)
async def read_company(
    company_id: str,
    _: None = Depends(set_tenant),
) -> CompanyProfile:
    return await get_company(company_id)
