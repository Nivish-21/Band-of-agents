from typing import List, Optional, Any
from datetime import date
from pydantic import BaseModel, Field


class CoverageDetails(BaseModel):
    collision: bool
    liability_limit: int
    deductible: int


class Policy(BaseModel):
    policy_id: str
    status: str
    effective_date: date
    expiry_date: date
    coverage: CoverageDetails


class Claimant(BaseModel):
    name: str
    is_policy_holder: bool
    prior_claims_12mo: int


class Incident(BaseModel):
    date: date
    type: str
    at_fault: str
    police_report: bool
    description: str


class Damage(BaseModel):
    vehicle: str
    estimate_amount: float
    photos_count: int


class IntakeBlock(BaseModel):
    is_valid: bool
    missing_fields: List[str] = Field(default_factory=list)
    inconsistencies: List[str] = Field(default_factory=list)
    completeness_score: float


class CoverageBlock(BaseModel):
    policy_active: bool
    peril_covered: bool
    deductible_applied: int
    covered_amount: float
    reasons: List[str] = Field(default_factory=list)


class FraudBlock(BaseModel):
    risk_score: int
    red_flags: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)


class DecisionBlock(BaseModel):
    status: str  # "APPROVE", "DENY", "ESCALATE"
    reason: str
    final_amount: float


class ClaimRecord(BaseModel):
    claim_id: str
    policy: Policy
    claimant: Claimant
    incident: Incident
    damage: Damage
    amount_claimed: float
    intake: Optional[IntakeBlock] = None
    coverage: Optional[CoverageBlock] = None
    fraud: Optional[FraudBlock] = None
    decision: Optional[DecisionBlock] = None


def validate_claim(claim_data: dict) -> IntakeBlock:
    """
    Validates a raw claim dictionary, checking for missing fields and inconsistencies,
    and calculating a completeness score.
    """
    missing_fields = []
    inconsistencies = []

    def check_presence(d: dict, path: str) -> Optional[Any]:
        keys = path.split(".")
        curr = d
        for k in keys:
            if not isinstance(curr, dict) or k not in curr:
                missing_fields.append(path)
                return None
            curr = curr[k]
        if curr is None or curr == "":
            missing_fields.append(path)
            return None
        return curr

    # Checklist of fields
    check_presence(claim_data, "claim_id")
    check_presence(claim_data, "policy.policy_id")
    check_presence(claim_data, "policy.status")
    check_presence(claim_data, "policy.effective_date")
    check_presence(claim_data, "policy.expiry_date")
    check_presence(claim_data, "policy.coverage.collision")
    check_presence(claim_data, "policy.coverage.liability_limit")
    check_presence(claim_data, "policy.coverage.deductible")
    check_presence(claim_data, "claimant.name")
    check_presence(claim_data, "claimant.is_policy_holder")
    check_presence(claim_data, "claimant.prior_claims_12mo")
    check_presence(claim_data, "incident.date")
    check_presence(claim_data, "incident.type")
    check_presence(claim_data, "incident.at_fault")
    check_presence(claim_data, "incident.police_report")
    check_presence(claim_data, "incident.description")
    check_presence(claim_data, "damage.vehicle")
    check_presence(claim_data, "damage.estimate_amount")
    check_presence(claim_data, "damage.photos_count")
    check_presence(claim_data, "amount_claimed")

    # Inconsistency checks
    est = (
        claim_data.get("damage", {}).get("estimate_amount")
        if isinstance(claim_data.get("damage"), dict)
        else None
    )
    amt = claim_data.get("amount_claimed")
    if est is not None and amt is not None:
        try:
            if float(est) != float(amt):
                inconsistencies.append(
                    f"Damage estimate_amount ({est}) does not match amount_claimed ({amt})"
                )
        except (ValueError, TypeError):
            inconsistencies.append(
                "Non-numeric values in estimate_amount or amount_claimed"
            )

    # Value range checks
    if amt is not None:
        try:
            if float(amt) <= 0:
                inconsistencies.append("amount_claimed must be greater than zero")
        except (ValueError, TypeError):
            pass

    total_fields = 20
    filled_fields = total_fields - len(missing_fields)
    completeness_score = (filled_fields / total_fields) * 100.0

    is_valid = len(missing_fields) == 0 and len(inconsistencies) == 0

    return IntakeBlock(
        is_valid=is_valid,
        missing_fields=missing_fields,
        inconsistencies=inconsistencies,
        completeness_score=completeness_score,
    )
