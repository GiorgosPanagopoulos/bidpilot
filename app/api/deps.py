from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.context import current_tenant
from app.core.exceptions import NotFoundError
from app.core.security import decode_access_token
from app.models.user import Role, User
from app.repositories.users import get_user_by_id

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    """Authenticate the Bearer token and bind the request to the token's company."""
    if creds is None:
        raise _unauthorized("Not authenticated")
    payload = decode_access_token(creds.credentials)
    if payload is None:
        raise _unauthorized("Invalid or expired token")
    user = await get_user_by_id(payload.sub)
    if user is None or user.company_id != payload.company_id:
        raise _unauthorized("Invalid or expired token")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account")
    current_tenant.set(payload.company_id)
    return user


def require_roles(*roles: Role, allow_demo: bool = False) -> Callable[..., Awaitable[User]]:
    async def guard(user: User = Depends(get_current_user)) -> User:
        if user.role in roles or (allow_demo and user.is_demo):
            return user
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return guard


require_admin = require_roles("admin")
# Runs that cost compute or write tenant data; the demo account (a viewer) may run them under quota.
require_writer = require_roles("admin", "member", allow_demo=True)


def ensure_own_company(company_id: str, user: User) -> None:
    # 404, not 403: other tenants' ids must not be confirmable.
    if company_id != user.company_id:
        raise NotFoundError(f"company {company_id} not found")
