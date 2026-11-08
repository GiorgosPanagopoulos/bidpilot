"""Company B must never read or act on company A's data."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.draft import BidDraft, GapReport, RequirementChecklist
from app.repositories.drafts import save_trace, upsert_draft
from tests.api_fixtures import bearer


async def _fake_agent(company_id: str, tender_id: str) -> BidDraft:
    draft = BidDraft(
        company_id=company_id,
        tender_id=tender_id,
        sections=[],
        checklist=RequirementChecklist(tender_id=tender_id, items=[], prompt_version="test"),
        gap_report=GapReport(
            company_id=company_id, tender_id=tender_id, items=[], coverage_ratio=1.0
        ),
        prompt_version="test",
    )
    await upsert_draft(draft)
    await save_trace(draft.id, [{"action": "extract_requirements"}])
    return draft


@pytest.fixture
def agent():
    with patch(
        "app.api.routers.drafts.run_drafting_agent", new=AsyncMock(side_effect=_fake_agent)
    ) as m:
        yield m


@pytest.fixture
async def tenants(make_user):
    _, token_a = await make_user("acme", "member")
    _, token_b = await make_user("globex", "member")
    return token_a, token_b


async def _run(api, token: str, company_id: str = "acme"):
    return await api.post(
        "/drafts/run", json={"company_id": company_id, "tender_id": "t1"}, headers=bearer(token)
    )


async def test_draft_is_stored_under_token_tenant(api, agent, tenants, fake_db):
    token_a, _ = tenants

    res = await _run(api, token_a)

    assert res.status_code == 201
    stored = fake_db["bid_drafts"].docs
    assert len(stored) == 1 and stored[0]["tenant"] == "acme"


async def test_company_b_cannot_read_company_a_draft(api, agent, tenants):
    token_a, token_b = tenants
    draft_id = (await _run(api, token_a)).json()["id"]

    assert (await api.get(f"/drafts/{draft_id}", headers=bearer(token_a))).status_code == 200
    assert (await api.get(f"/drafts/{draft_id}/trace", headers=bearer(token_a))).status_code == 200

    assert (await api.get(f"/drafts/{draft_id}", headers=bearer(token_b))).status_code == 404
    assert (await api.get(f"/drafts/{draft_id}/trace", headers=bearer(token_b))).status_code == 404


async def test_header_spoofing_does_not_cross_tenants(api, agent, tenants):
    token_a, token_b = tenants
    draft_id = (await _run(api, token_a)).json()["id"]

    res = await api.get(f"/drafts/{draft_id}", headers={**bearer(token_b), "X-Company-Id": "acme"})

    assert res.status_code == 404


async def test_company_b_cannot_run_draft_for_company_a(api, agent, tenants):
    _, token_b = tenants

    res = await _run(api, token_b, company_id="acme")

    assert res.status_code == 404
    agent.assert_not_awaited()


async def test_company_b_cannot_read_company_a_profile(api, tenants):
    token_a, token_b = tenants

    assert (await api.get("/companies/acme", headers=bearer(token_a))).status_code == 200
    assert (await api.get("/companies/acme", headers=bearer(token_b))).status_code == 404


async def test_company_b_cannot_list_or_run_company_a_matches(api, tenants):
    _, token_b = tenants

    with patch("app.api.routers.matches.run_matching", new=AsyncMock(return_value=[])) as matcher:
        assert (
            await api.get("/matches?company_id=acme", headers=bearer(token_b))
        ).status_code == 404
        assert (
            await api.post("/matches/run?company_id=acme", headers=bearer(token_b))
        ).status_code == 404
        matcher.assert_not_awaited()
