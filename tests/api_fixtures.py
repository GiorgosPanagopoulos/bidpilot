"""Shared fixtures for router-level tests: real app, real auth, fake Mongo, no LLM."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable

import bcrypt
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.context import current_tenant
from app.core.security import create_access_token
from app.models.company import CompanyProfile
from app.models.user import Role, User
from app.repositories import mongo
from app.repositories.companies import upsert_company
from app.repositories.users import create_user
from tests.fake_mongo import FakeClient, FakeDB

PASSWORD = "CorrectHorse42!"  # pragma: allowlist secret
# Low-cost hash so creating many users stays fast.
PASSWORD_HASH = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(4)).decode()

MakeUser = Callable[..., Awaitable[tuple[User, str]]]


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakeDB:
    client = FakeClient()
    monkeypatch.setattr(mongo, "_client", client)
    return client.db


@pytest.fixture(autouse=True)
def _reset_tenant() -> None:
    current_tenant.set(None)


@pytest.fixture
async def api(fake_db: FakeDB) -> AsyncIterator[AsyncClient]:
    from app.main import app

    # ASGITransport skips lifespan, so the scheduler never starts.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def make_user(fake_db: FakeDB) -> MakeUser:
    async def _make(
        company_id: str,
        role: Role = "member",
        *,
        is_demo: bool = False,
        is_active: bool = True,
        email: str | None = None,
    ) -> tuple[User, str]:
        await upsert_company(CompanyProfile(id=company_id, name=f"Company {company_id}"))
        user = await create_user(
            User(
                email=email or f"{role}{'-demo' if is_demo else ''}@{company_id}.test",
                hashed_password=PASSWORD_HASH,
                company_id=company_id,
                role=role,
                is_demo=is_demo,
                is_active=is_active,
            )
        )
        return user, create_access_token(user.id, user.company_id, user.role)

    return _make


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
