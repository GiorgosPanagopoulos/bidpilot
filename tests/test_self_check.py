from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.draft import (
    BidDraftSection,
    ProposalCitation,
    RequirementChecklist,
    RequirementItem,
)


def _citation(tender_id: str = "t1") -> ProposalCitation:
    return ProposalCitation(tender_id=tender_id, locator="Art.1", snippet="x")


@pytest.fixture(autouse=True)
def _clear_caches():
    from agent import tools as t

    t._checklist_cache.clear()
    t._gap_report_cache.clear()
    t._section_cache.clear()
    yield
    t._checklist_cache.clear()
    t._gap_report_cache.clear()
    t._section_cache.clear()


@pytest.mark.asyncio
async def test_self_check_ok_when_all_covered():
    from agent.tools import _checklist_cache, _section_cache, _self_check_logic

    tender_id = "t-sc-ok"
    company_id = "c-sc-ok"
    session_key = f"{company_id}:{tender_id}"

    items = [
        RequirementItem(
            id="req-1",
            category="technical",
            text="Civil engineering required.",
            mandatory=True,
            citation=_citation(tender_id),
        ),
    ]
    _checklist_cache[tender_id] = RequirementChecklist(
        tender_id=tender_id, items=items, prompt_version="v1"
    )
    section = BidDraftSection(
        title="Technical Approach",
        content="We have extensive civil engineering experience [Art.1].",
        citations=[],
        covers_requirements=["req-1"],
        self_check_status="ok",
    )
    _section_cache[session_key] = [section]

    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = json.dumps(
        {"status": "ok", "missing_requirement_ids": [], "notes": "All covered."}
    )
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    result = await _self_check_logic("Technical Approach", tender_id, company_id, llm=mock_llm)

    assert result["status"] == "ok"
    assert result["missing_requirement_ids"] == []


@pytest.mark.asyncio
async def test_self_check_gaps_when_mandatory_missing():
    from agent.tools import _checklist_cache, _section_cache, _self_check_logic

    tender_id = "t-sc-gap"
    company_id = "c-sc-gap"
    session_key = f"{company_id}:{tender_id}"

    items = [
        RequirementItem(
            id="req-m1",
            category="technical",
            text="Must have ISO 9001 certification.",
            mandatory=True,
            citation=_citation(tender_id),
        ),
        RequirementItem(
            id="req-m2",
            category="financial",
            text="Annual turnover above 1000000 EUR.",
            mandatory=True,
            citation=_citation(tender_id),
        ),
    ]
    _checklist_cache[tender_id] = RequirementChecklist(
        tender_id=tender_id, items=items, prompt_version="v1"
    )
    section = BidDraftSection(
        title="Compliance",
        content="We meet financial requirements.",
        citations=[],
        covers_requirements=["req-m2"],
        self_check_status="ok",
    )
    _section_cache[session_key] = [section]

    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = json.dumps(
        {
            "status": "gaps",
            "missing_requirement_ids": ["req-m1"],
            "notes": "ISO 9001 certification not addressed.",
        }
    )
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    result = await _self_check_logic("Compliance", tender_id, company_id, llm=mock_llm)

    assert result["status"] == "gaps"
    assert "req-m1" in result["missing_requirement_ids"]


@pytest.mark.asyncio
async def test_self_check_section_not_in_cache_returns_gaps():
    from agent.tools import _self_check_logic

    result = await _self_check_logic(
        "Nonexistent Section", "t-missing", "c-missing", llm=AsyncMock()
    )
    assert result["status"] == "gaps"
