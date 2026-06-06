from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic

from app.core.settings import settings


def _is_model_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in ("model", "invalid", "not found", "unavailable", "unknown"))


class _GuardedChatAnthropic(ChatAnthropic):
    """ChatAnthropic subclass that converts model-name API errors to DraftingError."""

    async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        try:
            return await super().ainvoke(input, config=config, **kwargs)
        except Exception as exc:
            if _is_model_error(exc):
                from app.core.exceptions import DraftingError

                raise DraftingError(
                    f"Invalid or unavailable AGENT_MODEL '{settings.agent_model}': {exc}"
                ) from exc
            raise


def get_drafting_llm(**kwargs: Any) -> ChatAnthropic:
    return _GuardedChatAnthropic(
        model=settings.agent_model,
        api_key=settings.anthropic_api_key,  # type: ignore[arg-type]
        **kwargs,
    )
