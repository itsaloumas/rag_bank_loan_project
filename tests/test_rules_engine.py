"""
Unit tests for the deterministic rules engine (rules_engine.py).

These pin the hard-rule, soft-score and decision-threshold behaviour defined in bank_data/bank-rules.pdf.
The rules engine is pure Python with no external dependencies, so these tests need no API key, network or vector store.
"""
import pytest

import rules_engine


# Helpers

def _factor_points(breakdown, factor):
    # Return the points awarded to a named factor within a soft-score breakdown
    return next(item["points"] for item in breakdown if item["factor"] == factor)


def _base_applicant(**overrides):
    #A fully-qualifying applicant.

    applicant = {
        "name_app": "Test Applicant",
        "age": 40,
        "income": 70000,
        "credit_score": 800,
        "delinquencies": 0,
        "employment_years": 10,
        "loan_amount": 10000,
        "account_balance": 50000,
        "collateral": True,
    }
    applicant.update(overrides)
    return applicant


# Hard rules

def test_clean_applicant_passes_hard_rules():
    passed, failures = rules_engine.check_hard_rules(_base_applicant())
    assert passed is True
    assert failures == []


def test_age_below_minimum_fails():
    passed, failures = rules_engine.check_hard_rules(_base_applicant(age=20))
    assert passed is False
    assert any("Age" in f for f in failures)


def test_age_above_maximum_fails():
    passed, _ = rules_engine.check_hard_rules(_base_applicant(age=66))
    assert passed is False


def test_age_boundaries_are_inclusive():
    assert rules_engine.check_hard_rules(_base_applicant(age=21))[0] is True
    assert rules_engine.check_hard_rules(_base_applicant(age=65))[0] is True


def test_insufficient_employment_fails():
    passed, failures = rules_engine.check_hard_rules(_base_applicant(employment_years=0))
    assert passed is False
    assert any("Employment" in f for f in failures)


def test_delinquency_limit():
    assert rules_engine.check_hard_rules(_base_applicant(delinquencies=2))[0] is True # 2 allowed
    assert rules_engine.check_hard_rules(_base_applicant(delinquencies=3))[0] is False # 3 rejected


def test_credit_score_minimum():
    assert rules_engine.check_hard_rules(_base_applicant(credit_score=550))[0] is True
    assert rules_engine.check_hard_rules(_base_applicant(credit_score=549))[0] is False


def test_high_dti_fails():
    # loan 60000 / 60 = 1000 monthly payment and income 24000 / 12 = 2000 monthly DTI 0.50 > 0.40
    passed, failures = rules_engine.check_hard_rules(_base_applicant(income=24000, loan_amount=60000))
    assert passed is False
    assert any("DTI" in f for f in failures)


def test_multiple_hard_failures_accumulate():
    passed, failures = R.check_hard_rules(
        _base_applicant(age=18, credit_score=400, employment_years=0)
    )
    assert passed is False
    assert len(failures) >= 3


# Soft score

@pytest.mark.parametrize("score,expected", [
    (800, 50), (750, 50),
    (749, 40), (700, 40),
    (699, 20), (650, 20),
    (649, 5), (550, 5),
    (549, 0), (300, 0),
])
def test_credit_score_bands(score, expected):
    _, breakdown = rules_engine.calculate_soft_score(_base_applicant(credit_score=score))
    assert _factor_points(breakdown, "Credit Score") == expected


def test_collateral_points():
    _, secured = rules_engine.calculate_soft_score(_base_applicant(collateral=True))
    _, unsecured = rules_engine.calculate_soft_score(_base_applicant(collateral=False))
    assert _factor_points(secured, "Collateral") == 20
    assert _factor_points(unsecured, "Collateral") == 0


def test_perfect_applicant_scores_max_220():
    total, breakdown = rules_engine.calculate_soft_score(_base_applicant())
    assert total == 220
    assert sum(item["points"] for item in breakdown) == 220


def test_zero_income_is_handled_gracefully():
    total, _ = rules_engine.calculate_soft_score(_base_applicant(income=0))
    assert isinstance(total, int)


# Decision thresholds

@pytest.mark.parametrize("score,decision", [
    (220, "APPROVE"),
    (200, "APPROVE"),
    (199, "REFER_FOR_MANUAL_REVIEW"),
    (150, "REFER_FOR_MANUAL_REVIEW"),
    (149, "REJECT"),
    (0, "REJECT"),
])
def test_decision_thresholds(score, decision):
    assert rules_engine.get_deterministic_decision(score) == decision


# Full evaluation pipeline

def test_full_evaluation_hard_fail_short_circuits():
    result = rules_engine.full_evaluation(_base_applicant(age=18))
    assert result["hard_passed"] is False
    assert result["decision"] == "REJECT"
    assert result["soft_score"] == 0
    assert result["soft_breakdown"] == []
    assert result["hard_failures"]


def test_full_evaluation_strong_applicant_approves():
    result = rules_engine.full_evaluation(_base_applicant())
    assert result["hard_passed"] is True
    assert result["decision"] == "APPROVE"
    assert result["soft_score"] == 220


def test_full_evaluation_result_has_expected_keys():
    result = rules_engine.full_evaluation(_base_applicant())
    for key in ("hard_passed", "hard_failures", "soft_score",
                "soft_breakdown", "decision", "reason"):
        assert key in result
