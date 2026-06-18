import pytest
from datetime import date
from claimband.schema import ClaimRecord
from claimband.coverage import compute_coverage


@pytest.fixture
def base_claim():
    return ClaimRecord.model_validate(
        {
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
    )


def test_coverage_success(base_claim):
    block = compute_coverage(base_claim)
    assert block.policy_active is True
    assert block.peril_covered is True
    assert block.deductible_applied == 500
    assert block.covered_amount == 3700.0  # 4200 - 500
    assert any("Deductible of $500.00 applied" in r for r in block.reasons)


def test_coverage_inactive_policy(base_claim):
    base_claim.policy.status = "suspended"
    block = compute_coverage(base_claim)
    assert block.policy_active is False
    assert block.covered_amount == 0.0
    assert any("Policy status is 'suspended'" in r for r in block.reasons)


def test_coverage_out_of_bounds_date(base_claim):
    base_claim.incident.date = date(2027, 1, 15)
    block = compute_coverage(base_claim)
    assert block.policy_active is False
    assert block.covered_amount == 0.0
    assert any("falls outside the policy period" in r for r in block.reasons)


def test_coverage_uncovered_peril(base_claim):
    base_claim.incident.type = "comprehensive"
    block = compute_coverage(base_claim)
    assert block.peril_covered is False
    assert block.covered_amount == 0.0
    assert any("Peril 'comprehensive' is not recognized" in r for r in block.reasons)


def test_coverage_limit_capping(base_claim):
    base_claim.damage.estimate_amount = 60000.0
    base_claim.amount_claimed = 60000.0
    block = compute_coverage(base_claim)
    assert block.policy_active is True
    assert block.peril_covered is True
    assert block.deductible_applied == 500
    assert block.covered_amount == 49500.0  # 50000 limit - 500 deductible
    assert any("exceeds liability limit" in r for r in block.reasons)


def test_coverage_below_deductible(base_claim):
    base_claim.damage.estimate_amount = 400.0
    base_claim.amount_claimed = 400.0
    block = compute_coverage(base_claim)
    assert block.policy_active is True
    assert block.peril_covered is True
    assert block.covered_amount == 0.0
    assert any("is less than or equal to the deductible" in r for r in block.reasons)
