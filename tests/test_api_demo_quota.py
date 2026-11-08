"""Daily draft budget for the public demo account."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import DraftingError
from app.core.settings import settings
from app.services import demo_quota
from tests.api_fixtures import bearer
from tests.test_api_tenant_isolation import _fake_agent

DAY_1 = datetime(2026, 11, 8, 23, 59, tzinfo=UTC)
DAY_2 = DAY_1 + timedelta(minutes=2)


@pytest.fixture(autouse=True)
def _quota_env(monkeypatch):
    monkeypatch.setattr(settings, "demo_daily_drafts", 2)
    monkeypatch.setattr(demo_quota, "_utc_now", lambda: DAY_1)


@pytest.fixture
def agent():
    with patch(
        "app.api.routers.drafts.run_drafting_agent", new=AsyncMock(side_effect=_fake_agent)
    ) as m:
        yield m


async def _run(api, token: str, company_id: str = "demo-co"):
    return await api.post(
        "/drafts/run", json={"company_id": company_id, "tender_id": "t1"}, headers=bearer(token)
    )


async def test_demo_gets_limit_then_429(api, agent, make_user):
    _, token = await make_user("demo-co", "viewer", is_demo=True)

    assert (await _run(api, token)).status_code == 201
    assert (await _run(api, token)).status_code == 201

    res = await _run(api, token)
    assert res.status_code == 429
    assert res.json()["detail"] == "Demo limit reached for today, try again tomorrow."
    assert agent.await_count == 2


async def test_rejected_attempts_do_not_inflate_the_counter(api, agent, make_user, fake_db):
    _, token = await make_user("demo-co", "viewer", is_demo=True)

    for _ in range(5):
        await _run(api, token)

    [counter] = fake_db["demo_usage"].docs
    assert counter["count"] == 2


async def test_quota_resets_next_utc_day(api, agent, make_user, monkeypatch):
    _, token = await make_user("demo-co", "viewer", is_demo=True)
    for _ in range(2):
        await _run(api, token)
    assert (await _run(api, token)).status_code == 429

    monkeypatch.setattr(demo_quota, "_utc_now", lambda: DAY_2)

    assert (await _run(api, token)).status_code == 201


async def test_failed_run_is_refunded(api, make_user):
    _, token = await make_user("demo-co", "viewer", is_demo=True)

    failing = AsyncMock(side_effect=DraftingError("agent failed"))
    with patch("app.api.routers.drafts.run_drafting_agent", new=failing):
        for _ in range(3):
            assert (await _run(api, token)).status_code == 500

    with patch("app.api.routers.drafts.run_drafting_agent", new=AsyncMock(side_effect=_fake_agent)):
        assert (await _run(api, token)).status_code == 201
        assert (await _run(api, token)).status_code == 201
        assert (await _run(api, token)).status_code == 429


async def test_non_demo_users_are_not_limited(api, agent, make_user, fake_db):
    _, token = await make_user("acme", "member")

    for _ in range(4):
        assert (await _run(api, token, company_id="acme")).status_code == 201
    assert fake_db["demo_usage"].docs == []


async def test_demo_quota_is_checked_after_tenant(api, agent, make_user, fake_db):
    await make_user("acme", "member")
    _, token = await make_user("demo-co", "viewer", is_demo=True)

    assert (await _run(api, token, company_id="acme")).status_code == 404
    assert fake_db["demo_usage"].docs == []
