import pytest
from datetime import date
from pydantic import ValidationError
from claimband.schema import ClaimRecord, validate_claim


@pytest.fixture
def clean_claim_dict():
    return {
        "claim_id": "CLM-1001",
        "policy": {
            "policy_id": "POL-552",
            "status": "active",
            "effective_date": "2026-01-01",
            "expiry_date": "2026-12-31",
            "coverage": {
                "collision": True,
                "liability_limit": 50000,
                "deductible": 500,
            },
        },
        "claimant": {
            "name": "Jane Doe",
            "is_policy_holder": True,
            "prior_claims_12mo": 0,
        },
        "incident": {
            "date": "2026-06-10",
            "type": "collision",
            "at_fault": "other_party",
            "police_report": True,
            "description": "Rear-ended at a stop light.",
        },
        "damage": {
            "vehicle": "2021 Honda Civic",
            "estimate_amount": 4200.0,
            "photos_count": 6,
        },
        "amount_claimed": 4200.0,
    }


def test_pydantic_validation_success(clean_claim_dict):
    claim = ClaimRecord.model_validate(clean_claim_dict)
    assert claim.claim_id == "CLM-1001"
    assert claim.policy.policy_id == "POL-552"
    assert claim.policy.effective_date == date(2026, 1, 1)
    assert claim.claimant.is_policy_holder is True
    assert claim.incident.police_report is True
    assert claim.damage.estimate_amount == 4200.0


def test_pydantic_validation_failure(clean_claim_dict):
    bad_dict = clean_claim_dict.copy()
    bad_dict["amount_claimed"] = "not-a-number"
    with pytest.raises(ValidationError):
        ClaimRecord.model_validate(bad_dict)


def test_validate_claim_clean(clean_claim_dict):
    block = validate_claim(clean_claim_dict)
    assert block.is_valid is True
    assert len(block.missing_fields) == 0
    assert len(block.inconsistencies) == 0
    assert block.completeness_score == 100.0


def test_validate_claim_missing_fields(clean_claim_dict):
    incomplete_dict = clean_claim_dict.copy()
    del incomplete_dict["claim_id"]
    del incomplete_dict["policy"]["status"]

    block = validate_claim(incomplete_dict)
    assert block.is_valid is False
    assert "claim_id" in block.missing_fields
    assert "policy.status" in block.missing_fields
    assert block.completeness_score < 100.0


def test_validate_claim_inconsistencies(clean_claim_dict):
    inconsistent_dict = clean_claim_dict.copy()
    inconsistent_dict["amount_claimed"] = 5000.0  # estimate is 4200.0

    block = validate_claim(inconsistent_dict)
    assert block.is_valid is False
    assert any("does not match amount_claimed" in inc for inc in block.inconsistencies)
    assert block.completeness_score == 100.0  # no fields missing
