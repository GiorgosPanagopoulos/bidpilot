from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.draft import RequirementChecklist


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


@pytest.fixture()
def mock_chunks():
    return [
        {
            "id": "tender-001-p1-c0",
            "text": "The contractor must have at least five years of civil engineering experience.",
            "metadata": {"tender_id": "tender-001", "locator": "Article 5"},
        },
        {
            "id": "tender-001-p1-c1",
            "text": "Annual turnover must exceed 2000000 EUR for the last three years.",
            "metadata": {"tender_id": "tender-001", "locator": "Article 6"},
        },
    ]


@pytest.fixture()
def llm_json_response():
    return {
        "items": [
            {
                "id": "req-001",
                "category": "technical",
                "text": "At least five years of civil engineering experience required.",
                "mandatory": True,
                "citation": {
                    "tender_id": "tender-001",
                    "locator": "Article 5",
                    "snippet": "five years of civil engineering experience",
                },
            },
            {
                "id": "req-002",
                "category": "financial",
                "text": "Annual turnover must exceed EUR 2,000,000.",
                "mandatory": True,
                "citation": {
                    "tender_id": "tender-001",
                    "locator": "Article 6",
                    "snippet": "Annual turnover must exceed 2000000 EUR",
                },
            },
        ]
    }


@pytest.mark.asyncio
async def test_requirement_extraction_returns_checklist(mock_chunks, llm_json_response):
    tender_id = "tender-001"

    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = json.dumps(llm_json_response)
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    with patch("agent.tools.get_all_tender_chunks", return_value=mock_chunks):
        from agent.tools import _extract_requirements_logic

        checklist = await _extract_requirements_logic(tender_id, llm=mock_llm)

    assert isinstance(checklist, RequirementChecklist)
    assert checklist.tender_id == tender_id
    assert len(checklist.items) == 2
    assert checklist.prompt_version == "requirement_extraction/v1"


@pytest.mark.asyncio
async def test_extraction_citations_carry_locator(mock_chunks, llm_json_response):
    tender_id = "tender-001"

    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = json.dumps(llm_json_response)
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    with patch("agent.tools.get_all_tender_chunks", return_value=mock_chunks):
        from agent.tools import _extract_requirements_logic

        checklist = await _extract_requirements_logic(tender_id, llm=mock_llm)

    locators = [item.citation.locator for item in checklist.items]
    assert "Article 5" in locators
    assert "Article 6" in locators


@pytest.mark.asyncio
async def test_extraction_no_chunks_raises():
    from agent.tools import _extract_requirements_logic
    from app.core.exceptions import RequirementExtractionError

    with patch("agent.tools.get_all_tender_chunks", return_value=[]):
        with pytest.raises(RequirementExtractionError):
            await _extract_requirements_logic("tender-empty")


@pytest.mark.asyncio
async def test_extraction_populates_cache(mock_chunks, llm_json_response):
    tender_id = "tender-cache"

    llm_json_response_copy = dict(llm_json_response)
    for item in llm_json_response_copy["items"]:
        item = dict(item)
        item["citation"] = dict(item["citation"])
        item["citation"]["tender_id"] = tender_id

    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = json.dumps(llm_json_response)
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    with patch("agent.tools.get_all_tender_chunks", return_value=mock_chunks):
        from agent import tools as t
        from agent.tools import _extract_requirements_logic

        await _extract_requirements_logic(tender_id, llm=mock_llm)
        assert tender_id in t._checklist_cache
