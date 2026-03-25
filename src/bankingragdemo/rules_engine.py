"""
rules_engine.py
Deterministic hard-rule checks and soft-rule scoring based on bank-rules.pdf.
Runs BEFORE the LLM call to catch obvious rejects and provide a transparent score breakdown.
"""


def check_hard_rules(applicant):
    """Return (passed: bool, failures: list[str])."""
    failures = []
    age = applicant.get("age", 0)
    if age < 21 or age > 65:
        failures.append(f"Age {age} is outside the allowed range (21-65)")

    employment_years = applicant.get("employment_years", 0)
    if employment_years < 1:
        failures.append(f"Employment {employment_years} years is below minimum (1 year)")

    delinquencies = applicant.get("delinquencies", 0)
    if delinquencies > 2:
        failures.append(f"Delinquencies ({delinquencies}) exceed maximum allowed (2)")

    credit_score = applicant.get("credit_score", 0)
    if credit_score < 550:
        failures.append(f"Credit score {credit_score} is below minimum (550)")

    # DTI check — only if both income and loan_amount are available
    income = applicant.get("income", 0)
    loan_amount = applicant.get("loan_amount", 0)
    if income > 0:
        # Approximate monthly debt payment (5-year term, ~6% rate)
        monthly_payment = loan_amount / 60
        monthly_income = income / 12
        dti = monthly_payment / monthly_income if monthly_income > 0 else 999
        if dti > 0.40:
            failures.append(f"DTI ratio {dti:.2f} exceeds maximum (0.40)")

    passed = len(failures) == 0
    return passed, failures


def calculate_soft_score(applicant):
    """Return (total_score: int, breakdown: list[dict]) based on bank-rules.pdf soft rules."""
    breakdown = []

    # Credit Score
    cs = applicant.get("credit_score", 0)
    if cs >= 750:
        breakdown.append({"factor": "Credit Score", "condition": f"{cs} (750+)", "points": 50})
    elif cs >= 700:
        breakdown.append({"factor": "Credit Score", "condition": f"{cs} (700-749)", "points": 40})
    elif cs >= 650:
        breakdown.append({"factor": "Credit Score", "condition": f"{cs} (650-699)", "points": 20})
    elif cs >= 550:
        breakdown.append({"factor": "Credit Score", "condition": f"{cs} (550-649)", "points": 5})
    else:
        breakdown.append({"factor": "Credit Score", "condition": f"{cs} (<550)", "points": 0})

    # Income Level
    income = applicant.get("income", 0)
    if income >= 60000:
        breakdown.append({"factor": "Income Level", "condition": f"\u20ac{income:,.0f} (\u226560K)", "points": 30})
    elif income >= 40000:
        breakdown.append({"factor": "Income Level", "condition": f"\u20ac{income:,.0f} (40-59K)", "points": 20})
    elif income >= 25000:
        breakdown.append({"factor": "Income Level", "condition": f"\u20ac{income:,.0f} (25-39K)", "points": 10})
    else:
        breakdown.append({"factor": "Income Level", "condition": f"\u20ac{income:,.0f} (<25K)", "points": 0})

    # DTI
    loan_amount = applicant.get("loan_amount", 0)
    if income > 0:
        monthly_payment = loan_amount / 60
        monthly_income = income / 12
        dti = monthly_payment / monthly_income if monthly_income > 0 else 999
    else:
        dti = 999
    if dti <= 0.20:
        breakdown.append({"factor": "DTI Ratio", "condition": f"{dti:.2f} (\u22640.20)", "points": 30})
    elif dti <= 0.30:
        breakdown.append({"factor": "DTI Ratio", "condition": f"{dti:.2f} (0.21-0.30)", "points": 20})
    elif dti <= 0.40:
        breakdown.append({"factor": "DTI Ratio", "condition": f"{dti:.2f} (0.31-0.40)", "points": 10})
    else:
        breakdown.append({"factor": "DTI Ratio", "condition": f"{dti:.2f} (>0.40)", "points": 0})

    # Account Balance (>= 6 months of loan payments)
    balance = applicant.get("account_balance", 0)
    monthly_payment = loan_amount / 60 if loan_amount > 0 else 0
    if monthly_payment > 0:
        months_covered = balance / monthly_payment
    else:
        months_covered = 999
    if months_covered >= 6:
        breakdown.append({"factor": "Account Balance", "condition": f"\u20ac{balance:,.0f} (\u22656 months)", "points": 20})
    elif months_covered >= 3:
        breakdown.append({"factor": "Account Balance", "condition": f"\u20ac{balance:,.0f} (3-5 months)", "points": 10})
    else:
        breakdown.append({"factor": "Account Balance", "condition": f"\u20ac{balance:,.0f} (<3 months)", "points": 0})

    # Employment Stability
    emp = applicant.get("employment_years", 0)
    if emp >= 5:
        breakdown.append({"factor": "Employment Stability", "condition": f"{emp} years (\u22655)", "points": 20})
    elif emp >= 2:
        breakdown.append({"factor": "Employment Stability", "condition": f"{emp} years (2-4)", "points": 10})
    else:
        breakdown.append({"factor": "Employment Stability", "condition": f"{emp} years (<2)", "points": 0})

    # Delinquency
    delin = applicant.get("delinquencies", 0)
    if delin == 0:
        breakdown.append({"factor": "Delinquency History", "condition": "0 defaults", "points": 20})
    elif delin == 1:
        breakdown.append({"factor": "Delinquency History", "condition": "1 default", "points": 5})
    else:
        breakdown.append({"factor": "Delinquency History", "condition": f"{delin} defaults", "points": 0})

    # Collateral
    collateral = applicant.get("collateral", False)
    if collateral:
        breakdown.append({"factor": "Collateral", "condition": "Secured", "points": 20})
    else:
        breakdown.append({"factor": "Collateral", "condition": "Unsecured", "points": 0})

    # Age (Optimal Range)
    age = applicant.get("age", 0)
    if 25 <= age <= 55:
        breakdown.append({"factor": "Age (Optimal)", "condition": f"{age} (25-55)", "points": 10})
    else:
        breakdown.append({"factor": "Age (Optimal)", "condition": f"{age} (outside 25-55)", "points": 0})

    # Loan Amount vs Income
    if income > 0:
        loan_ratio = loan_amount / income
        if loan_ratio <= 0.30:
            breakdown.append({"factor": "Loan vs Income", "condition": f"{loan_ratio:.0%} (\u226430%)", "points": 20})
        elif loan_ratio <= 0.50:
            breakdown.append({"factor": "Loan vs Income", "condition": f"{loan_ratio:.0%} (\u226450%)", "points": 10})
        else:
            breakdown.append({"factor": "Loan vs Income", "condition": f"{loan_ratio:.0%} (>50%)", "points": 0})
    else:
        breakdown.append({"factor": "Loan vs Income", "condition": "No income", "points": 0})

    total = sum(item["points"] for item in breakdown)
    return total, breakdown


def get_deterministic_decision(total_score):
    """Return decision string based on score thresholds from bank-rules.pdf."""
    if total_score >= 200:
        return "APPROVE"
    elif total_score >= 150:
        return "REFER_FOR_MANUAL_REVIEW"
    else:
        return "REJECT"


def full_evaluation(applicant):
    """Run complete deterministic evaluation. Returns dict with all results."""
    hard_passed, hard_failures = check_hard_rules(applicant)

    if not hard_passed:
        return {
            "hard_passed": False,
            "hard_failures": hard_failures,
            "soft_score": 0,
            "soft_breakdown": [],
            "decision": "REJECT",
            "reason": "Failed hard rule checks",
        }

    total_score, breakdown = calculate_soft_score(applicant)
    decision = get_deterministic_decision(total_score)

    return {
        "hard_passed": True,
        "hard_failures": [],
        "soft_score": total_score,
        "soft_breakdown": breakdown,
        "decision": decision,
        "reason": f"Score: {total_score} points",
    }
