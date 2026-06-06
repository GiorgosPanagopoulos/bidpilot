from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.draft import (
    BidDraft,
    BidDraftSection,
    GapItem,
    GapReport,
    ProposalCitation,
    RequirementChecklist,
    RequirementItem,
)


def _citation(tid: str = "t1") -> ProposalCitation:
    return ProposalCitation(tender_id=tid, locator="Art.1", snippet="x")


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
async def test_ingest_guard_raises_drafting_error():
    from agent.executor import run_drafting_agent
    from app.core.exceptions import DraftingError

    with patch("agent.executor.has_tender_docs", return_value=False):
        with pytest.raises(DraftingError, match="no ingested document"):
            await run_drafting_agent(company_id="comp-001", tender_id="tender-001")


@pytest.mark.asyncio
async def test_draft_pipeline_assembles_bid_draft_needs_review():
    from agent import tools as t
    from agent.executor import run_drafting_agent

    tender_id = "tender-pipe"
    company_id = "comp-pipe"
    session_key = f"{company_id}:{tender_id}"

    citation = _citation(tender_id)
    checklist = RequirementChecklist(
        tender_id=tender_id,
        items=[
            RequirementItem(
                id="r1",
                category="technical",
                text="Civil engineering required.",
                mandatory=True,
                citation=citation,
            )
        ],
        prompt_version="requirement_extraction/v1",
    )
    gap_report = GapReport(
        company_id=company_id,
        tender_id=tender_id,
        items=[GapItem(requirement_id="r1", status="met")],
        coverage_ratio=1.0,
    )
    section = BidDraftSection(
        title="Technical Approach",
        content="We have extensive civil engineering experience.",
        citations=[citation],
        covers_requirements=["r1"],
        self_check_status="ok",
    )

    # Pre-populate caches as if the agent had run the tools
    t._checklist_cache[tender_id] = checklist
    t._gap_report_cache[session_key] = gap_report
    t._section_cache[session_key] = [section]

    mock_agent = AsyncMock()
    mock_agent.ainvoke = AsyncMock(return_value={"messages": []})

    with (
        patch("agent.executor.has_tender_docs", return_value=True),
        patch("agent.executor.get_drafting_llm", return_value=MagicMock()),
        patch("agent.executor.create_react_agent", return_value=mock_agent),
        patch("agent.executor.upsert_draft", AsyncMock()),
        patch("agent.executor.save_trace", AsyncMock()),
        patch("agent.executor.fire_and_forget", lambda *a, **kw: None),
    ):
        draft = await run_drafting_agent(company_id=company_id, tender_id=tender_id)

    assert isinstance(draft, BidDraft)
    assert draft.status == "needs_review"
    assert draft.company_id == company_id
    assert draft.tender_id == tender_id
    assert len(draft.sections) == 1
    assert draft.sections[0].title == "Technical Approach"
    assert draft.checklist.tender_id == tender_id
    assert draft.gap_report.coverage_ratio == 1.0


@pytest.mark.asyncio
async def test_draft_pipeline_fails_when_steps_incomplete():
    from agent.executor import run_drafting_agent
    from app.core.exceptions import DraftingError

    mock_agent = AsyncMock()
    mock_agent.ainvoke = AsyncMock(return_value={"messages": []})

    with (
        patch("agent.executor.has_tender_docs", return_value=True),
        patch("agent.executor.get_drafting_llm", return_value=MagicMock()),
        patch("agent.executor.create_react_agent", return_value=mock_agent),
    ):
        with pytest.raises(DraftingError, match="did not complete all required steps"):
            await run_drafting_agent(company_id="comp-x", tender_id="tender-x")
