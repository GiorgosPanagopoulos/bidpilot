from pydantic import BaseModel, Field


class EligibilityCheck(BaseModel):
    passed: bool
    failed_criteria: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rule_version: str = ""


class MatchResult(BaseModel):
    tender_id: str
    company_id: str
    score: float
    semantic_score: float
    rule_score: float
    reasons: list[str] = Field(default_factory=list)
    eligibility: EligibilityCheck
