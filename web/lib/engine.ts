/**
 * Browser port of ClaimBand's deterministic decision rules — a faithful
 * translation of the Python pure functions (claimband/{schema,coverage,scoring,
 * adjudication}.py). The LLM is never on the data path (design decision D13),
 * so the exact same logic runs client-side: judges can adjudicate their own
 * claims with no backend. This is the rules the four agents run — not the live
 * Band relay (which can't run on static hosting).
 */

import type {
  ClaimRecord,
  CoverageBlock,
  DecisionBlock,
  FraudBlock,
  IntakeBlock,
} from "./data";

const HIGH_AMOUNT = 10000;
const MIN_PHOTOS = 3;
const ESCALATE_RISK = 60;
const ESCALATE_AMOUNT = 10000;

const usd = (n: number): string =>
  `$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const daysBetween = (a: string, b: string): number =>
  Math.round((Date.parse(b) - Date.parse(a)) / 86_400_000);

// claimband/schema.py :: validate_claim
export function validateClaim(claim: ClaimRecord): NonNullable<IntakeBlock> {
  const inconsistencies: string[] = [];
  const est = claim.damage.estimate_amount;
  const amt = claim.amount_claimed;

  if (amt > est) {
    inconsistencies.push(
      `Amount claimed (${amt}) exceeds damage estimate (${est})`,
    );
  }
  if (amt <= 0) {
    inconsistencies.push("amount_claimed must be greater than zero");
  }

  // The form always supplies the 20 required fields, so missing_fields is empty;
  // inconsistencies are what a well-formed but contradictory claim trips.
  const missing_fields: string[] = [];
  const completeness_score = (20 - missing_fields.length) / 20 * 100;

  return {
    is_valid: missing_fields.length === 0 && inconsistencies.length === 0,
    missing_fields,
    inconsistencies,
    completeness_score,
  };
}

// claimband/coverage.py :: compute_coverage
export function computeCoverage(claim: ClaimRecord): NonNullable<CoverageBlock> {
  const reasons: string[] = [];

  const statusActive = claim.policy.status.toLowerCase() === "active";
  const effective = claim.policy.effective_date;
  const expiry = claim.policy.expiry_date;
  const incDate = claim.incident.date;

  reasons.push(
    statusActive
      ? `The policy is active for the incident date (${incDate} falls between ${effective} and ${expiry}).`
      : `The policy status is '${claim.policy.status}', not 'active'. The incident date (${incDate}) falls outside the policy period (${effective} to ${expiry}).`,
  );

  const dateInRange = effective <= incDate && incDate <= expiry;
  const policy_active = statusActive && dateInRange;

  const cov = claim.policy.coverage as unknown as Record<string, unknown>;
  const perilType = claim.incident.type.toLowerCase();
  let peril_covered = false;
  if (perilType in cov && typeof cov[perilType] === "boolean") {
    peril_covered = Boolean(cov[perilType]);
    reasons.push(
      peril_covered
        ? `The incident type is ${claim.incident.type}, which is covered by the policy.`
        : `The incident type ${claim.incident.type} is excluded under the policy coverage.`,
    );
  } else {
    reasons.push(
      `The incident type ${claim.incident.type} is not recognised under this policy.`,
    );
  }

  let covered_amount = 0;
  let deductible_applied = 0;

  if (policy_active && peril_covered) {
    const estimate = claim.damage.estimate_amount;
    const limit = claim.policy.coverage.liability_limit;
    const deductible = claim.policy.coverage.deductible;

    const baseCovered = estimate > limit ? limit : estimate;
    if (estimate > limit) {
      reasons.push(
        `The damage estimate (${usd(estimate)}) exceeds the liability limit (${usd(limit)}). The limit will apply instead.`,
      );
    }
    if (baseCovered <= deductible) {
      covered_amount = 0;
      deductible_applied = Math.trunc(baseCovered);
      reasons.push(
        `The covered amount before deductible (${usd(baseCovered)}) is at or below the deductible (${usd(deductible)}). No payout after applying the deductible.`,
      );
    } else {
      covered_amount = baseCovered - deductible;
      deductible_applied = deductible;
      reasons.push(
        `The coverage amount is calculated as min(estimate, limit) - deductible. min(${usd(estimate)} (estimate), ${usd(limit)} (limit)) = ${usd(baseCovered)}. Subtracting the deductible: ${usd(baseCovered)} - ${usd(deductible)} = ${usd(covered_amount)}.`,
      );
    }
  } else {
    const why = !policy_active
      ? "the policy is not active for this incident date"
      : "the peril is not covered";
    reasons.push(`Coverage check failed because ${why}. Covered amount set to $0.00.`);
  }

  return { policy_active, peril_covered, deductible_applied, covered_amount, reasons };
}

// claimband/scoring.py :: score_risk
export function scoreRisk(claim: ClaimRecord): NonNullable<FraudBlock> {
  const red_flags: string[] = [];
  const reasons: string[] = [];

  const pr = claim.incident.police_report;
  reasons.push(pr ? "Police report was filed." : "No police report — that's a concern.");
  if (!pr) red_flags.push("No police report filed for the incident.");

  const prior = claim.claimant.prior_claims_12mo;
  if (prior > 0) {
    reasons.push(
      `Claimant has ${prior} prior claim${prior > 1 ? "s" : ""} in the last 12 months — elevated risk.`,
    );
    red_flags.push(
      `Claimant has ${prior} prior claim(s) in the last 12 months.`,
    );
  } else {
    reasons.push("Claimant has no prior claims in the last 12 months.");
  }

  const photos = claim.damage.photos_count;
  if (photos < MIN_PHOTOS) {
    reasons.push(
      `Low photo count (${photos} provided, minimum ${MIN_PHOTOS} expected) — insufficient documentation.`,
    );
    red_flags.push(
      `Low photo count (${photos} photos provided, minimum of ${MIN_PHOTOS} expected).`,
    );
  } else {
    reasons.push(`Sufficient photos provided (${photos}).`);
  }

  const holder = claim.claimant.is_policy_holder;
  reasons.push(
    holder
      ? "Claimant is the policy holder."
      : "Claimant is not the primary policy holder.",
  );
  if (!holder) {
    red_flags.push(
      `Claimant '${claim.claimant.name}' is not the primary policy holder.`,
    );
  }

  const amt = claim.amount_claimed;
  if (amt > HIGH_AMOUNT) {
    reasons.push(
      `Claim amount (${usd(amt)}) exceeds the high-risk threshold of ${usd(HIGH_AMOUNT)}.`,
    );
    red_flags.push(
      `High claim amount requested (${usd(amt)} exceeds threshold of ${usd(HIGH_AMOUNT)}).`,
    );
  } else {
    reasons.push(`Claim amount (${usd(amt)}) is below the high-risk threshold.`);
  }

  const daysSinceStart = daysBetween(
    claim.policy.effective_date,
    claim.incident.date,
  );
  if (daysSinceStart >= 0 && daysSinceStart <= 30) {
    reasons.push(
      `Incident occurred only ${daysSinceStart} day${daysSinceStart > 1 ? "s" : ""} after policy activation (within 30-day window) — possible early claim.`,
    );
    red_flags.push(
      `Incident occurred ${daysSinceStart} day(s) after policy activation (within 30-day window).`,
    );
  } else if (daysSinceStart >= 0) {
    reasons.push(
      `Incident occurred ${daysSinceStart} day${daysSinceStart > 1 ? "s" : ""} after policy effective date — outside the early-claim window.`,
    );
  }

  const risk_score = Math.min(100, red_flags.length * 20);
  reasons.push(
    `Calculated risk score: ${risk_score} based on ${red_flags.length} triggered red flag${red_flags.length > 1 ? "s" : ""}.`,
  );

  return { risk_score, red_flags, reasons };
}

// claimband/adjudication.py :: adjudicate_claim
export function adjudicate(record: ClaimRecord): NonNullable<DecisionBlock> {
  const intake = record.intake;
  const coverage = record.coverage;
  const fraud = record.fraud;

  if (!intake) {
    return { status: "DENY", reason: "Intake block is missing from the claim record — cannot proceed without validation.", final_amount: 0 };
  }
  if (!intake.is_valid) {
    return {
      status: "DENY",
      reason: `Intake validation failed. Inconsistencies found: ${intake.inconsistencies.join("; ")}. The claim cannot move forward.`,
      final_amount: 0,
    };
  }
  if (!coverage) {
    return { status: "DENY", reason: "Coverage evaluation is missing — no coverage data to base a decision on.", final_amount: 0 };
  }
  if (!fraud) {
    return { status: "DENY", reason: "Fraud risk evaluation is missing — cannot assess claim without it.", final_amount: 0 };
  }
  if (!coverage.policy_active) {
    return {
      status: "DENY",
      reason: `The policy is not active on the incident date. ${coverage.reasons[0]} Per hard rules, this claim must be denied.`,
      final_amount: 0,
    };
  }
  if (!coverage.peril_covered) {
    return {
      status: "DENY",
      reason: `The claimed peril is not covered. ${coverage.reasons[1]} The policy does not cover this type of incident.`,
      final_amount: 0,
    };
  }
  if (fraud.risk_score >= ESCALATE_RISK) {
    return {
      status: "ESCALATE",
      reason: `Risk score ${fraud.risk_score} exceeds the ${ESCALATE_RISK} threshold. Red flags: ${fraud.red_flags.join("; ")}. Per hard rules, this claim must be escalated for human review.`,
      final_amount: coverage.covered_amount,
    };
  }
  if (coverage.covered_amount > ESCALATE_AMOUNT) {
    return {
      status: "ESCALATE",
      reason: `The covered amount (${usd(coverage.covered_amount)}) exceeds the escalation threshold (${usd(ESCALATE_AMOUNT)}). A human reviewer must approve this payout.`,
      final_amount: coverage.covered_amount,
    };
  }
  const finalAmount = coverage.covered_amount;
  return {
    status: "APPROVE",
    reason: `The policy is active on the incident date, the fraud risk score is low (${fraud.risk_score}) and the covered amount (${usd(finalAmount)}) is well below the escalation threshold. All hard rules point to approval, so the claim is approved for the covered amount.`,
    final_amount: finalAmount,
  };
}

/** Run the full four-agent relay deterministically and return the enriched record. */
export function runRelay(claim: ClaimRecord): ClaimRecord {
  const record: ClaimRecord = structuredClone(claim);
  record.intake = validateClaim(record);
  record.coverage = computeCoverage(record);
  record.fraud = scoreRisk(record);
  record.decision = adjudicate(record);
  return record;
}
