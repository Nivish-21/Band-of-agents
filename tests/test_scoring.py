import pytest
from datetime import date
from claimband.schema import ClaimRecord
from claimband.scoring import score_risk


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
                "date": "2026-06-10",  # ~160 days after policy start (Jan 1)
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


def test_score_risk_clean(base_claim):
    block = score_risk(base_claim)
    assert block.risk_score == 0
    assert len(block.red_flags) == 0
    assert any("no prior claims" in r for r in block.reasons)


def test_score_risk_one_flag(base_claim):
    # Insufficient photos (< 3)
    base_claim.damage.photos_count = 2
    block = score_risk(base_claim)
    assert block.risk_score == 20
    assert len(block.red_flags) == 1
    assert "Low photo count" in block.red_flags[0]


def test_score_risk_three_flags(base_claim):
    # No police report, prior claims, insufficient photos
    base_claim.incident.police_report = False
    base_claim.claimant.prior_claims_12mo = 2
    base_claim.damage.photos_count = 1

    block = score_risk(base_claim)
    assert block.risk_score == 60
    assert len(block.red_flags) == 3
    assert any("No police report" in f for f in block.red_flags)
    assert any("prior claim" in f for f in block.red_flags)
    assert any("Low photo count" in f for f in block.red_flags)


def test_score_risk_proximity(base_claim):
    # Incident date within 30 days of policy effective date (Jan 1)
    base_claim.incident.date = date(2026, 1, 15)  # 14 days after Jan 1
    block = score_risk(base_claim)
    assert block.risk_score == 20
    assert len(block.red_flags) == 1
    assert "Incident occurred 14 day(s) after policy activation" in block.red_flags[0]
