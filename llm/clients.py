from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic

from app.core.settings import settings


def get_drafting_llm(**kwargs: Any) -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.agent_model,
        api_key=settings.anthropic_api_key,  # type: ignore[arg-type]
        **kwargs,
    )
