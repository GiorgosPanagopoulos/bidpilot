from __future__ import annotations

from dataclasses import dataclass

_INPUT_COST_PER_M: dict[str, float] = {
    "claude-sonnet-4-6": 3.0,
    "claude-opus-4-8": 15.0,
    "claude-haiku-4-5-20251001": 0.25,
}
_OUTPUT_COST_PER_M: dict[str, float] = {
    "claude-sonnet-4-6": 15.0,
    "claude-opus-4-8": 75.0,
    "claude-haiku-4-5-20251001": 1.25,
}
_DEFAULT_INPUT = 3.0
_DEFAULT_OUTPUT = 15.0


@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    model: str

    @property
    def cost_usd(self) -> float:
        in_rate = _INPUT_COST_PER_M.get(self.model, _DEFAULT_INPUT)
        out_rate = _OUTPUT_COST_PER_M.get(self.model, _DEFAULT_OUTPUT)
        return (self.input_tokens * in_rate + self.output_tokens * out_rate) / 1_000_000
