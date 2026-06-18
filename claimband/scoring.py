from claimband.schema import ClaimRecord, FraudBlock


def score_risk(claim: ClaimRecord) -> FraudBlock:
    """
    Scans a claim record for potential fraud red flags, computes a risk score from 0 to 100,
    and returns a FraudBlock.
    """
    red_flags = []
    reasons = []

    # 1. Police Report Check
    if not claim.incident.police_report:
        flag = "No police report filed for the incident."
        red_flags.append(flag)
        reasons.append(f"Red Flag Triggered: {flag}")
    else:
        reasons.append("Police report was filed.")

    # 2. Prior Claims Check
    if claim.claimant.prior_claims_12mo > 0:
        flag = f"Claimant has {claim.claimant.prior_claims_12mo} prior claim(s) in the last 12 months."
        red_flags.append(flag)
        reasons.append(f"Red Flag Triggered: {flag}")
    else:
        reasons.append("Claimant has no prior claims in the last 12 months.")

    # 3. Photo Count Check
    if claim.damage.photos_count < 3:
        flag = f"Low photo count ({claim.damage.photos_count} photos provided, minimum of 3 expected)."
        red_flags.append(flag)
        reasons.append(f"Red Flag Triggered: {flag}")
    else:
        reasons.append(f"Sufficient photos provided ({claim.damage.photos_count}).")

    # 4. Policy Holder Check
    if not claim.claimant.is_policy_holder:
        flag = f"Claimant '{claim.claimant.name}' is not the primary policy holder."
        red_flags.append(flag)
        reasons.append(f"Red Flag Triggered: {flag}")
    else:
        reasons.append("Claimant is the policy holder.")

    # 5. High Claim Amount Check
    if claim.amount_claimed > 10000.0:
        flag = f"High claim amount requested (${claim.amount_claimed:,.2f} exceeds threshold of $10,000.00)."
        red_flags.append(flag)
        reasons.append(f"Red Flag Triggered: {flag}")
    else:
        reasons.append(
            f"Claim amount (${claim.amount_claimed:,.2f}) is below the high-risk threshold."
        )

    # 6. Policy Activation Proximity Check
    days_since_start = (claim.incident.date - claim.policy.effective_date).days
    if 0 <= days_since_start <= 30:
        flag = f"Incident occurred {days_since_start} day(s) after policy activation (within 30-day window)."
        red_flags.append(flag)
        reasons.append(f"Red Flag Triggered: {flag}")
    else:
        reasons.append(
            f"Incident occurred {days_since_start} day(s) after policy effective date."
        )

    # Calculate score: 20 points per red flag, capped at 100
    risk_score = min(100, len(red_flags) * 20)

    reasons.append(
        f"Calculated risk score: {risk_score} based on {len(red_flags)} triggered red flag(s)."
    )

    return FraudBlock(risk_score=risk_score, red_flags=red_flags, reasons=reasons)
