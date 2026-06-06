from __future__ import annotations

import json
import logging
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from agent.prompt import prompt_loader
from app.core.exceptions import RequirementExtractionError
from app.models.company import CompanyProfile
from app.models.draft import (
    BidDraftSection,
    GapItem,
    GapReport,
    ProposalCitation,
    RequirementChecklist,
    RequirementItem,
)
from app.repositories.companies import get_company
from app.vectorstore.tender_docs import get_all_tender_chunks, query_tender_docs

logger = logging.getLogger(__name__)

# Per-execution caches keyed by tender_id or company_id:tender_id.
# Cleared by run_drafting_agent after assembly.
_checklist_cache: dict[str, RequirementChecklist] = {}
_gap_report_cache: dict[str, GapReport] = {}
_section_cache: dict[str, list[BidDraftSection]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON from raw LLM output, stripping markdown fences if present."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return json.loads(text)


def _check_requirement(item: RequirementItem, profile: CompanyProfile) -> GapItem:
    text_lower = item.text.lower()

    if item.category == "technical":
        matched = [t for t in profile.capacity_tags if t.lower() in text_lower]
        if matched:
            return GapItem(
                requirement_id=item.id,
                status="met",
                evidence=f"matched tags: {', '.join(matched)}",
            )
        if profile.capacity_tags:
            return GapItem(
                requirement_id=item.id,
                status="partial",
                note="no matching capacity tag found",
            )
        return GapItem(
            requirement_id=item.id,
            status="unmet",
            note="company has no capacity tags defined",
        )

    if item.category == "financial":
        numbers = re.findall(r"\d[\d,\.]*", item.text)
        for raw in numbers:
            try:
                threshold = Decimal(re.sub(r"[,\s]", "", raw))
                if threshold <= 0:
                    continue
                if profile.annual_turnover >= threshold:
                    return GapItem(
                        requirement_id=item.id,
                        status="met",
                        evidence=f"turnover {profile.annual_turnover} >= {threshold}",
                    )
                if profile.annual_turnover >= threshold * Decimal("0.5"):
                    return GapItem(
                        requirement_id=item.id,
                        status="partial",
                        evidence=f"turnover {profile.annual_turnover} < {threshold}",
                    )
                return GapItem(
                    requirement_id=item.id,
                    status="unmet",
                    evidence=f"turnover {profile.annual_turnover} < {threshold}",
                )
            except (InvalidOperation, ValueError):
                continue
        return GapItem(
            requirement_id=item.id,
            status="partial",
            note="could not parse financial threshold",
        )

    if item.category == "legal":
        flagged = [f for f in profile.exclusion_flags if f.lower() in text_lower]
        if flagged:
            return GapItem(
                requirement_id=item.id,
                status="unmet",
                evidence=f"exclusion flags triggered: {', '.join(flagged)}",
            )
        return GapItem(
            requirement_id=item.id,
            status="met",
            evidence="no exclusion flags triggered",
        )

    # administrative, submission
    return GapItem(
        requirement_id=item.id,
        status="met",
        evidence="standard compliance assumed",
    )


# ---------------------------------------------------------------------------
# Business logic (separated for testability)
# ---------------------------------------------------------------------------


async def _extract_requirements_logic(tender_id: str, llm: Any = None) -> RequirementChecklist:
    from llm.clients import get_drafting_llm

    if llm is None:
        llm = get_drafting_llm()

    chunks = get_all_tender_chunks(tender_id)
    if not chunks:
        raise RequirementExtractionError(
            f"no document chunks for tender {tender_id}; ingest the document first"
        )

    chunks_text = "\n\n---\n\n".join(f"[{c['metadata']['locator']}]\n{c['text']}" for c in chunks)
    template = prompt_loader.load("requirement_extraction")
    prompt_text = template.format(chunks=chunks_text, tender_id=tender_id)

    response = await llm.ainvoke([HumanMessage(content=prompt_text)])
    content: str = getattr(response, "content", str(response))

    try:
        data = _extract_json(content)
    except Exception as exc:
        raise RequirementExtractionError(f"LLM output is not valid JSON: {exc}") from exc

    items: list[RequirementItem] = []
    for raw in data.get("items", []):
        cit_raw = raw.get("citation", {})
        citation = ProposalCitation(
            tender_id=tender_id,
            locator=cit_raw.get("locator", "unknown"),
            snippet=cit_raw.get("snippet", ""),
        )
        items.append(
            RequirementItem(
                id=raw.get("id") or str(uuid.uuid4()),
                category=raw.get("category", "technical"),
                text=raw.get("text", ""),
                mandatory=bool(raw.get("mandatory", True)),
                citation=citation,
            )
        )

    checklist = RequirementChecklist(
        tender_id=tender_id,
        items=items,
        prompt_version="requirement_extraction/v1",
    )
    _checklist_cache[tender_id] = checklist
    return checklist


async def _analyze_gaps_logic(company_id: str, tender_id: str) -> GapReport:
    checklist = _checklist_cache.get(tender_id)
    if checklist is None:
        raise RequirementExtractionError(
            f"no checklist cached for tender {tender_id}; call extract_requirements first"
        )

    profile = await get_company(company_id)
    gap_items = [_check_requirement(item, profile) for item in checklist.items]

    total = len(gap_items)
    met = sum(1 for g in gap_items if g.status == "met")
    coverage_ratio = met / total if total > 0 else 0.0

    report = GapReport(
        company_id=company_id,
        tender_id=tender_id,
        items=gap_items,
        coverage_ratio=coverage_ratio,
    )
    _gap_report_cache[f"{company_id}:{tender_id}"] = report
    return report


async def _draft_section_logic(
    tender_id: str,
    company_id: str,
    section_title: str,
    requirement_ids: list[str],
    llm: Any = None,
) -> BidDraftSection:
    from llm.clients import get_drafting_llm

    if llm is None:
        llm = get_drafting_llm()

    checklist = _checklist_cache.get(tender_id)
    relevant = [item for item in checklist.items if item.id in requirement_ids] if checklist else []
    requirements_text = "\n".join(
        f"- [{item.id}] ({item.category}, {'mandatory' if item.mandatory else 'optional'}): {item.text}"
        for item in relevant
    )

    clauses = query_tender_docs(tender_id, section_title, top_k=5)
    clauses_text = "\n\n".join(f"[{c['metadata']['locator']}]: {c['text'][:400]}" for c in clauses)

    profile = await get_company(company_id)
    company_caps = (
        f"Capacity tags: {', '.join(profile.capacity_tags)}; Turnover: {profile.annual_turnover}"
    )

    template = prompt_loader.load("draft_section")
    prompt_text = template.format(
        section_title=section_title,
        requirements=requirements_text or "(none specified)",
        clauses=clauses_text or "(no clauses retrieved)",
        company_capabilities=company_caps,
    )

    response = await llm.ainvoke([HumanMessage(content=prompt_text)])
    content: str = getattr(response, "content", str(response))

    try:
        data = _extract_json(content)
    except Exception:
        data = {}

    citations = [
        ProposalCitation(
            tender_id=tender_id,
            locator=c.get("locator", ""),
            snippet=c.get("snippet", ""),
        )
        for c in data.get("citations", [])
    ]

    section = BidDraftSection(
        title=data.get("title", section_title),
        content=data.get("content", content),
        citations=citations,
        covers_requirements=data.get("covers_requirements", requirement_ids),
        self_check_status="ok",
    )

    session_key = f"{company_id}:{tender_id}"
    _section_cache.setdefault(session_key, []).append(section)
    return section


async def _self_check_logic(
    section_title: str,
    tender_id: str,
    company_id: str,
    llm: Any = None,
) -> dict[str, Any]:
    from llm.clients import get_drafting_llm

    if llm is None:
        llm = get_drafting_llm()

    session_key = f"{company_id}:{tender_id}"
    sections = _section_cache.get(session_key, [])
    section = next((s for s in sections if s.title == section_title), None)
    if section is None:
        return {
            "status": "gaps",
            "missing_requirement_ids": [],
            "notes": "section not found in cache",
        }

    checklist = _checklist_cache.get(tender_id)
    mandatory_reqs = [item for item in (checklist.items if checklist else []) if item.mandatory]
    mandatory_text = "\n".join(f"- [{item.id}]: {item.text}" for item in mandatory_reqs)

    template = prompt_loader.load("self_check")
    prompt_text = template.format(
        section_content=section.content,
        mandatory_requirements=mandatory_text or "(none)",
    )

    response = await llm.ainvoke([HumanMessage(content=prompt_text)])
    raw: str = getattr(response, "content", str(response))

    try:
        result = _extract_json(raw)
    except Exception:
        result = {"status": "gaps", "missing_requirement_ids": [], "notes": raw}

    status_val = result.get("status", "gaps")
    if status_val not in ("ok", "gaps"):
        status_val = "gaps"

    # Update self_check_status on the cached section
    for s in sections:
        if s.title == section_title:
            object.__setattr__(s, "self_check_status", status_val)

    return result


# ---------------------------------------------------------------------------
# LangChain tools
# ---------------------------------------------------------------------------


@tool
async def extract_requirements(tender_id: str) -> str:
    """Extract structured requirements from an ingested tender document.

    Returns a JSON-serialised RequirementChecklist. Call this first.
    """
    checklist = await _extract_requirements_logic(tender_id)
    return checklist.model_dump_json()


@tool
async def analyze_gaps(company_id: str, tender_id: str) -> str:
    """Analyse gaps between company capabilities and tender requirements.

    Pure logic check against CompanyProfile. Call after extract_requirements.
    Returns a JSON-serialised GapReport.
    """
    report = await _analyze_gaps_logic(company_id, tender_id)
    return report.model_dump_json()


@tool
async def retrieve_clauses(tender_id: str, query: str) -> str:
    """Retrieve relevant tender clauses for a query.

    Returns a JSON array of ProposalCitation objects.
    """
    results = query_tender_docs(tender_id, query, top_k=5)
    citations = [
        ProposalCitation(
            tender_id=tender_id,
            locator=r["metadata"].get("locator", f"p.{i + 1}"),
            snippet=r["text"][:300],
        )
        for i, r in enumerate(results)
    ]
    return json.dumps([c.model_dump() for c in citations])


class _DraftSectionInput(BaseModel):
    tender_id: str = Field(description="Tender ID")
    company_id: str = Field(description="Company ID")
    section_title: str = Field(description="Title of the section to draft")
    requirement_ids: list[str] = Field(description="Requirement IDs this section must cover")


@tool(args_schema=_DraftSectionInput)
async def draft_section(
    tender_id: str,
    company_id: str,
    section_title: str,
    requirement_ids: list[str],
) -> str:
    """Draft a cited section of the technical proposal for given requirement IDs.

    MUST cite tender clauses. Returns a JSON-serialised BidDraftSection.
    """
    section = await _draft_section_logic(tender_id, company_id, section_title, requirement_ids)
    return section.model_dump_json()


class _SelfCheckInput(BaseModel):
    section_title: str = Field(description="Title of the drafted section to check")
    tender_id: str = Field(description="Tender ID")
    company_id: str = Field(description="Company ID")


@tool(args_schema=_SelfCheckInput)
async def self_check(section_title: str, tender_id: str, company_id: str) -> str:
    """Validate that a drafted section covers all mandatory requirements.

    Returns JSON: {status: ok|gaps, missing_requirement_ids: [...], notes: str}.
    """
    result = await _self_check_logic(section_title, tender_id, company_id)
    return json.dumps(result)
