from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from llm.pricing import TokenUsage

logger = logging.getLogger(__name__)


class TokenCostCallback(BaseCallbackHandler):
    def __init__(self, model: str) -> None:
        super().__init__()
        self.model = model
        self.input_tokens: int = 0
        self.output_tokens: int = 0

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        llm_output: dict[str, Any] = getattr(response, "llm_output", None) or {}
        usage: dict[str, Any] = llm_output.get("usage") or llm_output.get("token_usage") or {}
        self.input_tokens += int(usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0))
        self.output_tokens += int(
            usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
        )

    @property
    def usage(self) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            model=self.model,
        )
