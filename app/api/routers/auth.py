from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.context import current_tenant
from app.core.security import create_access_token, dummy_hash, verify_password
from app.core.settings import settings
from app.models.user import User, UserPublic
from app.repositories.audit import fire_and_forget
from app.repositories.users import get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserPublic


def _issue(user: User, action: str) -> TokenResponse:
    current_tenant.set(user.company_id)
    fire_and_forget(action, {"user_id": user.id, "is_demo": user.is_demo})
    return TokenResponse(
        access_token=create_access_token(user.id, user.company_id, user.role),
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserPublic.from_user(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    user = await get_user_by_email(body.email)
    hashed = user.hashed_password if user else dummy_hash()
    # bcrypt is CPU-bound; keep it off the event loop.
    ok = await run_in_threadpool(verify_password, body.password, hashed)
    if user is None or not ok:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account")
    return _issue(user, "auth.login")


@router.post("/demo", response_model=TokenResponse)
async def demo_login() -> TokenResponse:
    if not settings.demo_email:
        raise HTTPException(status_code=404, detail="Demo is not enabled")
    user = await get_user_by_email(settings.demo_email)
    if user is None or not user.is_demo or not user.is_active:
        raise HTTPException(status_code=404, detail="Demo is not enabled")
    return _issue(user, "auth.demo_login")


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.from_user(user)
