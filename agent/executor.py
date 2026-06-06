from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from agent.prompt import prompt_loader
from agent.tools import (
    _checklist_cache,
    _gap_report_cache,
    _section_cache,
    analyze_gaps,
    draft_section,
    extract_requirements,
    retrieve_clauses,
    self_check,
)
from app.core.context import current_tenant
from app.core.exceptions import DraftingError
from app.core.settings import settings
from app.models.draft import BidDraft
from app.repositories.audit import fire_and_forget
from app.repositories.drafts import save_trace, upsert_draft
from app.vectorstore.tender_docs import has_tender_docs
from llm.callbacks import TokenCostCallback
from llm.clients import get_drafting_llm

logger = logging.getLogger(__name__)


def _build_trace(messages: list[Any]) -> list[dict[str, Any]]:
    """Convert a LangGraph messages list into a thought/action/observation trace."""
    from langchain_core.messages import AIMessage, ToolMessage

    trace: list[dict[str, Any]] = []
    pending: dict[str, dict[str, Any]] = {}

    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            thought = msg.content if isinstance(msg.content, str) else ""
            for tc in msg.tool_calls:
                step: dict[str, Any] = {
                    "thought": thought,
                    "action": tc["name"],
                    "action_input": tc["args"],
                    "observation": "",
                }
                trace.append(step)
                pending[tc["id"]] = step
        elif isinstance(msg, ToolMessage):
            step_ref = pending.pop(msg.tool_call_id, None)
            if step_ref is not None:
                step_ref["observation"] = str(msg.content)

    return trace


async def run_drafting_agent(company_id: str, tender_id: str) -> BidDraft:
    """Run the ReAct drafting agent and return a BidDraft with status needs_review.

    Raises DraftingError if the tender has no ingested document or the agent fails.
    """
    if not has_tender_docs(tender_id):
        raise DraftingError(
            f"tender {tender_id} has no ingested document; "
            f"POST /tenders/{tender_id}/ingest-doc first"
        )

    callback = TokenCostCallback(model=settings.agent_model)
    llm = get_drafting_llm(callbacks=[callback])

    tools = [extract_requirements, analyze_gaps, retrieve_clauses, draft_section, self_check]

    system_prompt_text = prompt_loader.load("system")

    agent = create_react_agent(llm, tools, prompt=system_prompt_text)

    input_text = (
        f"Draft a complete bid proposal for company_id={company_id} on tender_id={tender_id}. "
        "Follow the workflow exactly: "
        "1) call extract_requirements, "
        "2) call analyze_gaps, "
        "3) plan sections, "
        "4) call draft_section for each section, "
        "5) call self_check for each drafted section."
    )

    try:
        result: dict[str, Any] = await agent.ainvoke(
            {"messages": [HumanMessage(content=input_text)]}
        )
    except Exception as exc:
        raise DraftingError(f"agent execution failed: {exc}") from exc

    messages: list[Any] = result.get("messages", [])
    trace = _build_trace(messages)

    session_key = f"{company_id}:{tender_id}"
    checklist = _checklist_cache.get(tender_id)
    gap_report = _gap_report_cache.get(session_key)
    sections = _section_cache.get(session_key, [])

    if checklist is None or gap_report is None or not sections:
        _checklist_cache.pop(tender_id, None)
        _gap_report_cache.pop(session_key, None)
        _section_cache.pop(session_key, None)
        raise DraftingError(
            "agent did not complete all required steps "
            "(extract_requirements, analyze_gaps, and at least one draft_section)"
        )

    draft = BidDraft(
        company_id=company_id,
        tender_id=tender_id,
        sections=sections,
        checklist=checklist,
        gap_report=gap_report,
        status="needs_review",
        prompt_version=checklist.prompt_version,
    )

    await upsert_draft(draft)
    await save_trace(draft.id, trace)

    usage = callback.usage
    fire_and_forget(
        "drafts.agent_run",
        {
            "tenant": current_tenant.get(),
            "company_id": company_id,
            "tender_id": tender_id,
            "draft_id": draft.id,
            "prompt_version": draft.prompt_version,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cost_usd": usage.cost_usd,
        },
    )

    _checklist_cache.pop(tender_id, None)
    _gap_report_cache.pop(session_key, None)
    _section_cache.pop(session_key, None)

    return draft
