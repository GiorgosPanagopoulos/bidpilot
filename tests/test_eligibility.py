"""Stub eligibility tests — full engine in Phase 2."""
import pytest

from app.models.match import EligibilityCheck


def test_eligibility_passed():
    check = EligibilityCheck(passed=True)
    assert check.passed is True
    assert check.failed_criteria == []
    assert check.warnings == []


def test_eligibility_failed():
    check = EligibilityCheck(
        passed=False,
        failed_criteria=["deadline passed", "no CPV overlap"],
        warnings=["budget may exceed capacity"],
    )
    assert check.passed is False
    assert len(check.failed_criteria) == 2
    assert len(check.warnings) == 1


def test_eligibility_partial_pass():
    check = EligibilityCheck(passed=True, warnings=["no NUTS region overlap"])
    assert check.passed is True
    assert check.warnings == ["no NUTS region overlap"]
