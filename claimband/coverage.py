from claimband.schema import ClaimRecord, CoverageBlock


def compute_coverage(claim: ClaimRecord) -> CoverageBlock:
    """
    Computes coverage for a given claim record by checking policy status,
    period validity, peril coverage, and applying limit and deductible.
    """
    reasons = []

    # 1. Policy Status Check
    status_active = claim.policy.status.lower() == "active"
    if status_active:
        reasons.append("Policy status is active.")
    else:
        reasons.append(f"Policy status is '{claim.policy.status}' (expected 'active').")

    # 2. Date Range Check
    date_in_range = (
        claim.policy.effective_date <= claim.incident.date <= claim.policy.expiry_date
    )
    if date_in_range:
        reasons.append(
            f"Incident date {claim.incident.date} is within the policy period "
            f"({claim.policy.effective_date} to {claim.policy.expiry_date})."
        )
    else:
        reasons.append(
            f"Incident date {claim.incident.date} falls outside the policy period "
            f"({claim.policy.effective_date} to {claim.policy.expiry_date})."
        )

    policy_active = status_active and date_in_range

    # 3. Peril (Incident Type) Coverage Check
    peril_type = claim.incident.type.lower()
    peril_covered = False
    if hasattr(claim.policy.coverage, peril_type):
        peril_covered = getattr(claim.policy.coverage, peril_type)
        if peril_covered:
            reasons.append(
                f"Peril '{claim.incident.type}' is explicitly covered under the policy."
            )
        else:
            reasons.append(
                f"Peril '{claim.incident.type}' is excluded (set to False) in policy coverage."
            )
    else:
        reasons.append(
            f"Peril '{claim.incident.type}' is not recognized or supported by the policy coverage schema."
        )

    # 4. Covered Amount Calculation
    covered_amount = 0.0
    deductible_applied = 0

    if policy_active and peril_covered:
        estimate = claim.damage.estimate_amount
        limit = claim.policy.coverage.liability_limit
        deductible = claim.policy.coverage.deductible

        # Limit check
        if estimate > limit:
            reasons.append(
                f"Damage estimate (${estimate:,.2f}) exceeds liability limit (${limit:,.2f}). Limit will apply."
            )
            base_covered = float(limit)
        else:
            base_covered = float(estimate)

        # Deductible check
        if base_covered <= deductible:
            reasons.append(
                f"Covered amount before deductible (${base_covered:,.2f}) is less than or equal to "
                f"the deductible (${deductible:,.2f}). Net covered amount is $0.00."
            )
            covered_amount = 0.0
            deductible_applied = int(
                base_covered
            )  # or full deductible if we want to represent it
        else:
            covered_amount = base_covered - deductible
            deductible_applied = deductible
            reasons.append(
                f"Deductible of ${deductible:,.2f} applied. Covered amount: ${covered_amount:,.2f} "
                f"(min(Estimate, Limit) - Deductible)."
            )
    else:
        reasons.append("Claim coverage check failed; covered amount set to $0.00.")

    return CoverageBlock(
        policy_active=policy_active,
        peril_covered=peril_covered,
        deductible_applied=deductible_applied,
        covered_amount=covered_amount,
        reasons=reasons,
    )
