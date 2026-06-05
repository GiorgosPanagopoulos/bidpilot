from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from app.models.company import CompanyProfile
from app.models.match import EligibilityCheck
from app.models.tender import Tender

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "eligibility_rules.yaml"

_DEFAULTS: dict[str, Any] = {
    "min_turnover_ratio": 1.0,
    "min_lead_days": 3,
    "technical_coverage_threshold": 0.5,
    "rule_version": "1.0.0",
}


class EligibilityEngine:
    def __init__(self, config_path: Path = _DEFAULT_CONFIG_PATH) -> None:
        self._config_path = config_path
        self._config: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        try:
            with open(self._config_path) as f:
                loaded = yaml.safe_load(f) or {}
            self._config = {**_DEFAULTS, **loaded}
        except FileNotFoundError:
            logger.warning("eligibility config not found at %s, using defaults", self._config_path)
            self._config = dict(_DEFAULTS)
        logger.debug("eligibility rules loaded: version=%s", self._config.get("rule_version"))

    @property
    def rule_version(self) -> str:
        return str(self._config.get("rule_version", _DEFAULTS["rule_version"]))

    def check(self, company: CompanyProfile, tender: Tender) -> EligibilityCheck:
        failed: list[str] = []
        warnings: list[str] = []

        # EXCLUSION (hard)
        flag_overlap = set(company.exclusion_flags) & set(tender.exclusion_flags)
        if flag_overlap:
            failed.append(f"exclusion flag overlap: {', '.join(sorted(flag_overlap))}")

        # FINANCIAL (hard)
        if tender.budget is not None:
            ratio = Decimal(str(self._config["min_turnover_ratio"]))
            required = tender.budget * ratio
            if company.annual_turnover < required:
                failed.append(
                    f"annual turnover {company.annual_turnover} below required {required}"
                )

        # DEADLINE (hard)
        min_lead_days: int = int(self._config["min_lead_days"])
        deadline = tender.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        cutoff = datetime.now(UTC) + timedelta(days=min_lead_days)
        if deadline <= cutoff:
            failed.append(
                f"deadline {deadline.date()} within {min_lead_days}-day lead window"
            )

        # TECHNICAL (soft)
        threshold: float = float(self._config["technical_coverage_threshold"])
        if company.capacity_tags:
            description_lower = tender.description.lower()
            matched = [tag for tag in company.capacity_tags if tag.lower() in description_lower]
            coverage = len(matched) / len(company.capacity_tags)
            if coverage < threshold:
                warnings.append(
                    f"technical coverage {coverage:.0%} below {threshold:.0%} threshold"
                )

        return EligibilityCheck(
            passed=len(failed) == 0,
            failed_criteria=failed,
            warnings=warnings,
            rule_version=self.rule_version,
        )


engine = EligibilityEngine()
