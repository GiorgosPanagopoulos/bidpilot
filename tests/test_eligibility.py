from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.matching.eligibility import EligibilityEngine
from app.models.company import CompanyProfile
from app.models.tender import Tender, TenderStatus


def _company(**kwargs) -> CompanyProfile:
    defaults = dict(
        id="comp-test",
        name="Test Co",
        cpv_codes=["45000000"],
        regions=["EL30"],
        annual_turnover=Decimal("5000000"),
        capacity_tags=["civil engineering", "project management"],
        exclusion_flags=[],
    )
    return CompanyProfile(**{**defaults, **kwargs})


def _tender(**kwargs) -> Tender:
    defaults = dict(
        id="tender-test",
        source="TED",
        title="Test Tender",
        cpv_codes=["45000000"],
        budget=Decimal("2000000"),
        deadline=datetime.now(UTC) + timedelta(days=30),
        nuts=["EL30"],
        description="civil engineering and project management services",
        exclusion_flags=[],
        status=TenderStatus.OPEN,
    )
    return Tender(**{**defaults, **kwargs})


@pytest.fixture()
def default_engine(tmp_path: Path) -> EligibilityEngine:
    cfg = tmp_path / "rules.yaml"
    cfg.write_text(
        "min_turnover_ratio: 1.0\n"
        "min_lead_days: 3\n"
        "technical_coverage_threshold: 0.5\n"
        'rule_version: "1.0.0"\n'
    )
    return EligibilityEngine(config_path=cfg)


def test_exclusion_flag_hard_fail(default_engine):
    company = _company(exclusion_flags=["sanctions"])
    tender = _tender(exclusion_flags=["sanctions", "fraud"])
    result = default_engine.check(company, tender)
    assert result.passed is False
    assert any("exclusion flag" in c for c in result.failed_criteria)


def test_financial_hard_fail(default_engine):
    company = _company(annual_turnover=Decimal("500000"))
    tender = _tender(budget=Decimal("2000000"))
    result = default_engine.check(company, tender)
    assert result.passed is False
    assert any("annual turnover" in c for c in result.failed_criteria)


def test_deadline_hard_fail(default_engine):
    company = _company()
    tender = _tender(deadline=datetime.now(UTC) + timedelta(days=1))
    result = default_engine.check(company, tender)
    assert result.passed is False
    assert any("lead window" in c for c in result.failed_criteria)


def test_technical_soft_warning(default_engine):
    company = _company(capacity_tags=["civil engineering", "nuclear physics", "quantum computing"])
    tender = _tender(description="basic civil engineering work required")
    result = default_engine.check(company, tender)
    assert result.passed is True
    assert any("technical coverage" in w for w in result.warnings)


def test_all_pass(default_engine):
    company = _company()
    tender = _tender()
    result = default_engine.check(company, tender)
    assert result.passed is True
    assert result.failed_criteria == []


def test_rule_version_in_output(default_engine):
    result = default_engine.check(_company(), _tender())
    assert result.rule_version == "1.0.0"


def test_hot_reload(tmp_path: Path):
    cfg = tmp_path / "rules.yaml"
    cfg.write_text(
        "min_turnover_ratio: 1.0\n"
        "min_lead_days: 3\n"
        "technical_coverage_threshold: 0.9\n"
        'rule_version: "1.0.0"\n'
    )
    eng = EligibilityEngine(config_path=cfg)

    company = _company(capacity_tags=["civil engineering", "project management"])
    tender = _tender(description="civil engineering work only")

    result_before = eng.check(company, tender)
    assert any("technical coverage" in w for w in result_before.warnings), (
        "expected warning with 0.9 threshold"
    )

    cfg.write_text(
        "min_turnover_ratio: 1.0\n"
        "min_lead_days: 3\n"
        "technical_coverage_threshold: 0.1\n"
        'rule_version: "1.1.0"\n'
    )
    eng.reload()

    result_after = eng.check(company, tender)
    assert result_after.warnings == [], "expected no warning with 0.1 threshold"
    assert result_after.rule_version == "1.1.0"
