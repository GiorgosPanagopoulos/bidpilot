from fastapi import Header

from app.core.context import current_tenant


async def set_tenant(x_company_id: str | None = Header(default=None)) -> None:
    current_tenant.set(x_company_id)
