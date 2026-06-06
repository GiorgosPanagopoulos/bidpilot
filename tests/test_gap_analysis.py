from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.company import CompanyProfile
from app.models.draft import (
    GapReport,
    ProposalCitation,
    RequirementChecklist,
    RequirementItem,
)


def _citation(tender_id: str = "t1") -> ProposalCitation:
    return ProposalCitation(tender_id=tender_id, locator="Art.1", snippet="x")


def _make_checklist(items: list[RequirementItem], tender_id: str = "t1") -> RequirementChecklist:
    return RequirementChecklist(
        tender_id=tender_id,
        items=items,
        prompt_version="requirement_extraction/v1",
    )


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
async def test_technical_requirement_met_when_tag_present():
    from agent.tools import _analyze_gaps_logic, _checklist_cache

    tender_id = "t-tech"
    company_id = "c-tech"
    profile = CompanyProfile(
        id=company_id,
        name="ACME",
        capacity_tags=["civil engineering"],
        annual_turnover=Decimal("5000000"),
    )
    item = RequirementItem(
        id="req-001",
        category="technical",
        text="Civil engineering expertise is required.",
        mandatory=True,
        citation=_citation(tender_id),
    )
    _checklist_cache[tender_id] = _make_checklist([item], tender_id)

    with patch("agent.tools.get_company", AsyncMock(return_value=profile)):
        report = await _analyze_gaps_logic(company_id, tender_id)

    assert report.items[0].status == "met"
    assert report.coverage_ratio == 1.0


@pytest.mark.asyncio
async def test_financial_requirement_unmet_when_turnover_too_low():
    from agent.tools import _analyze_gaps_logic, _checklist_cache

    tender_id = "t-fin"
    company_id = "c-fin"
    profile = CompanyProfile(
        id=company_id,
        name="ACME",
        capacity_tags=[],
        annual_turnover=Decimal("100000"),
    )
    item = RequirementItem(
        id="req-002",
        category="financial",
        text="Annual turnover must exceed 5000000 EUR.",
        mandatory=True,
        citation=_citation(tender_id),
    )
    _checklist_cache[tender_id] = _make_checklist([item], tender_id)

    with patch("agent.tools.get_company", AsyncMock(return_value=profile)):
        report = await _analyze_gaps_logic(company_id, tender_id)

    assert report.items[0].status == "unmet"
    assert report.coverage_ratio == 0.0


@pytest.mark.asyncio
async def test_legal_requirement_met_when_no_exclusion_flags():
    from agent.tools import _analyze_gaps_logic, _checklist_cache

    tender_id = "t-legal"
    company_id = "c-legal"
    profile = CompanyProfile(
        id=company_id,
        name="Clean Co",
        exclusion_flags=[],
        annual_turnover=Decimal("0"),
    )
    item = RequirementItem(
        id="req-003",
        category="legal",
        text="No sanctions or fraud convictions permitted.",
        mandatory=True,
        citation=_citation(tender_id),
    )
    _checklist_cache[tender_id] = _make_checklist([item], tender_id)

    with patch("agent.tools.get_company", AsyncMock(return_value=profile)):
        report = await _analyze_gaps_logic(company_id, tender_id)

    assert report.items[0].status == "met"


@pytest.mark.asyncio
async def test_coverage_ratio_mixed():
    from agent.tools import _analyze_gaps_logic, _checklist_cache

    tender_id = "t-mixed"
    company_id = "c-mixed"
    profile = CompanyProfile(
        id=company_id,
        name="Mixed Co",
        capacity_tags=["software"],
        annual_turnover=Decimal("3000000"),
        exclusion_flags=[],
    )
    items = [
        RequirementItem(
            id="req-a",
            category="technical",
            text="Software development required.",
            mandatory=True,
            citation=_citation(tender_id),
        ),
        RequirementItem(
            id="req-b",
            category="technical",
            text="Hardware assembly skills needed.",
            mandatory=False,
            citation=_citation(tender_id),
        ),
        RequirementItem(
            id="req-c",
            category="financial",
            text="Turnover above 10000000 EUR required.",
            mandatory=True,
            citation=_citation(tender_id),
        ),
    ]
    _checklist_cache[tender_id] = _make_checklist(items, tender_id)

    with patch("agent.tools.get_company", AsyncMock(return_value=profile)):
        report = await _analyze_gaps_logic(company_id, tender_id)

    assert isinstance(report, GapReport)
    statuses = {g.requirement_id: g.status for g in report.items}
    assert statuses["req-a"] == "met"
    assert statuses["req-c"] == "unmet"
    # coverage_ratio counts "met" / total
    met_count = sum(1 for g in report.items if g.status == "met")
    assert report.coverage_ratio == pytest.approx(met_count / 3)


@pytest.mark.asyncio
async def test_missing_checklist_raises():
    from agent.tools import _analyze_gaps_logic
    from app.core.exceptions import RequirementExtractionError

    with pytest.raises(RequirementExtractionError):
        await _analyze_gaps_logic("c-none", "t-none")
