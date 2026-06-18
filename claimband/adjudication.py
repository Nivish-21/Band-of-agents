from claimband.schema import ClaimRecord, DecisionBlock


def adjudicate_claim(claim: ClaimRecord) -> DecisionBlock:
    """
    Synthesizes the findings from Intake, Coverage, and Fraud blocks, and applies the
    deterministic adjudication rules to output a DecisionBlock.
    """
    # Safeguard check: make sure required previous blocks exist
    if not claim.intake:
        return DecisionBlock(
            status="DENY",
            reason="Intake block missing from claim record.",
            final_amount=0.0,
        )
    if not claim.intake.is_valid:
        return DecisionBlock(
            status="DENY",
            reason=f"Claim failed intake validation. Inconsistencies: {claim.intake.inconsistencies}",
            final_amount=0.0,
        )
    if not claim.coverage:
        return DecisionBlock(
            status="DENY",
            reason="Coverage block missing from claim record.",
            final_amount=0.0,
        )
    if not claim.fraud:
        return DecisionBlock(
            status="DENY",
            reason="Fraud/Risk evaluation block missing from claim record.",
            final_amount=0.0,
        )

    # 1. Check Policy Active & Peril Covered
    if not claim.coverage.policy_active:
        return DecisionBlock(
            status="DENY",
            reason=f"Policy is inactive at incident date. Reasons: {'; '.join(claim.coverage.reasons)}",
            final_amount=0.0,
        )

    if not claim.coverage.peril_covered:
        return DecisionBlock(
            status="DENY",
            reason=f"Peril is not covered under the policy. Reasons: {'; '.join(claim.coverage.reasons)}",
            final_amount=0.0,
        )

    # 2. Check Risk Score and Covered Amount limits for Escalation
    risk_score = claim.fraud.risk_score
    covered_amount = claim.coverage.covered_amount

    if risk_score >= 60:
        return DecisionBlock(
            status="ESCALATE",
            reason=f"High risk score detected ({risk_score} >= 60). Red flags: {'; '.join(claim.fraud.red_flags)}",
            final_amount=covered_amount,
        )

    if covered_amount > 10000.0:
        return DecisionBlock(
            status="ESCALATE",
            reason=f"High covered amount detected (${covered_amount:,.2f} > $10,000.00). Requires human approval.",
            final_amount=covered_amount,
        )

    # 3. Otherwise Approve
    return DecisionBlock(
        status="APPROVE",
        reason="Claim approved automatically based on policy coverage and low risk score.",
        final_amount=covered_amount,
    )
