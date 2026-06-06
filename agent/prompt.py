from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPTS_ROOT = Path(__file__).parent.parent / "prompts"


class _PromptLoader:
    """Hot-reloadable file-based versioned prompt loader."""

    def load(self, name: str, version: str = "v1") -> str:
        path = _PROMPTS_ROOT / name / f"{version}.txt"
        return path.read_text(encoding="utf-8")


prompt_loader = _PromptLoader()
