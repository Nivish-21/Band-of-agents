import json
from pathlib import Path
from claimband.schema import ClaimRecord, validate_claim
from claimband.coverage import compute_coverage
from claimband.scoring import score_risk
from claimband.adjudication import adjudicate_claim


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).parent.parent / "claims" / name
    with open(fixture_path, "r") as f:
        return json.load(f)


def run_relay_simulation(claim_data: dict) -> ClaimRecord:
    # 1. Intake step
    intake_block = validate_claim(claim_data)
    claim_record = ClaimRecord.model_validate(claim_data)
    claim_record.intake = intake_block

    # If intake says invalid, we might skip other steps or run them.
    # In a normal flow, if it's invalid, Adjudicator will reject it. Let's run all steps:

    # 2. Coverage step
    coverage_block = compute_coverage(claim_record)
    claim_record.coverage = coverage_block

    # 3. Fraud step
    fraud_block = score_risk(claim_record)
    claim_record.fraud = fraud_block

    # 4. Adjudicator step
    decision_block = adjudicate_claim(claim_record)
    claim_record.decision = decision_block

    return claim_record


def test_integration_clean_claim():
    claim_data = load_fixture("clean.json")
    record = run_relay_simulation(claim_data)

    assert record.intake.is_valid is True
    assert record.coverage.policy_active is True
    assert record.coverage.peril_covered is True
    assert record.coverage.covered_amount == 3700.0
    assert record.fraud.risk_score == 0
    assert record.decision.status == "APPROVE"
    assert record.decision.final_amount == 3700.0


def test_integration_deny_claim():
    claim_data = load_fixture("deny.json")
    record = run_relay_simulation(claim_data)

    assert record.intake.is_valid is True
    assert record.coverage.policy_active is False
    assert record.decision.status == "DENY"
    assert "Policy is inactive at incident date" in record.decision.reason
    assert record.decision.final_amount == 0.0


def test_integration_fraud_claim():
    claim_data = load_fixture("fraud.json")
    record = run_relay_simulation(claim_data)

    assert record.intake.is_valid is True
    assert record.coverage.policy_active is True
    assert record.fraud.risk_score == 60
    assert record.decision.status == "ESCALATE"
    assert "High risk score detected" in record.decision.reason
    assert record.decision.final_amount == 3700.0
