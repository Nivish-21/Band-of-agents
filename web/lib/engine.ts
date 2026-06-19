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

  if (est !== amt) {
    inconsistencies.push(
      `Damage estimate_amount (${est}) does not match amount_claimed (${amt})`,
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
  reasons.push(
    statusActive
      ? "Policy status is active."
      : `Policy status is '${claim.policy.status}' (expected 'active').`,
  );

  const dateInRange =
    claim.policy.effective_date <= claim.incident.date &&
    claim.incident.date <= claim.policy.expiry_date;
  reasons.push(
    dateInRange
      ? `Incident date ${claim.incident.date} is within the policy period (${claim.policy.effective_date} to ${claim.policy.expiry_date}).`
      : `Incident date ${claim.incident.date} falls outside the policy period (${claim.policy.effective_date} to ${claim.policy.expiry_date}).`,
  );

  const policy_active = statusActive && dateInRange;

  const cov = claim.policy.coverage as unknown as Record<string, unknown>;
  const perilType = claim.incident.type.toLowerCase();
  let peril_covered = false;
  if (perilType in cov && typeof cov[perilType] === "boolean") {
    peril_covered = Boolean(cov[perilType]);
    reasons.push(
      peril_covered
        ? `Peril '${claim.incident.type}' is explicitly covered under the policy.`
        : `Peril '${claim.incident.type}' is excluded (set to False) in policy coverage.`,
    );
  } else {
    reasons.push(
      `Peril '${claim.incident.type}' is not recognized or supported by the policy coverage schema.`,
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
        `Damage estimate (${usd(estimate)}) exceeds liability limit (${usd(limit)}). Limit will apply.`,
      );
    }
    if (baseCovered <= deductible) {
      reasons.push(
        `Covered amount before deductible (${usd(baseCovered)}) is less than or equal to the deductible (${usd(deductible)}). Net covered amount is $0.00.`,
      );
      covered_amount = 0;
      deductible_applied = Math.trunc(baseCovered);
    } else {
      covered_amount = baseCovered - deductible;
      deductible_applied = deductible;
      reasons.push(
        `Deductible of ${usd(deductible)} applied. Covered amount: ${usd(covered_amount)} (min(Estimate, Limit) - Deductible).`,
      );
    }
  } else {
    reasons.push("Claim coverage check failed; covered amount set to $0.00.");
  }

  return { policy_active, peril_covered, deductible_applied, covered_amount, reasons };
}

// claimband/scoring.py :: score_risk
export function scoreRisk(claim: ClaimRecord): NonNullable<FraudBlock> {
  const red_flags: string[] = [];
  const reasons: string[] = [];

  if (!claim.incident.police_report) {
    red_flags.push("No police report filed for the incident.");
  }
  if (claim.claimant.prior_claims_12mo > 0) {
    red_flags.push(
      `Claimant has ${claim.claimant.prior_claims_12mo} prior claim(s) in the last 12 months.`,
    );
  }
  if (claim.damage.photos_count < MIN_PHOTOS) {
    red_flags.push(
      `Low photo count (${claim.damage.photos_count} photos provided, minimum of ${MIN_PHOTOS} expected).`,
    );
  }
  if (!claim.claimant.is_policy_holder) {
    red_flags.push(
      `Claimant '${claim.claimant.name}' is not the primary policy holder.`,
    );
  }
  if (claim.amount_claimed > HIGH_AMOUNT) {
    red_flags.push(
      `High claim amount requested (${usd(claim.amount_claimed)} exceeds threshold of ${usd(HIGH_AMOUNT)}).`,
    );
  }
  const daysSinceStart = daysBetween(
    claim.policy.effective_date,
    claim.incident.date,
  );
  if (daysSinceStart >= 0 && daysSinceStart <= 30) {
    red_flags.push(
      `Incident occurred ${daysSinceStart} day(s) after policy activation (within 30-day window).`,
    );
  }

  const risk_score = Math.min(100, red_flags.length * 20);
  reasons.push(
    `Calculated risk score: ${risk_score} based on ${red_flags.length} triggered red flag(s).`,
  );

  return { risk_score, red_flags, reasons };
}

// claimband/adjudication.py :: adjudicate_claim
export function adjudicate(record: ClaimRecord): NonNullable<DecisionBlock> {
  const intake = record.intake;
  const coverage = record.coverage;
  const fraud = record.fraud;

  if (!intake) {
    return { status: "DENY", reason: "Intake block missing from claim record.", final_amount: 0 };
  }
  if (!intake.is_valid) {
    return {
      status: "DENY",
      reason: `Claim failed intake validation. Inconsistencies: ${intake.inconsistencies.join(", ")}`,
      final_amount: 0,
    };
  }
  if (!coverage) {
    return { status: "DENY", reason: "Coverage block missing from claim record.", final_amount: 0 };
  }
  if (!fraud) {
    return { status: "DENY", reason: "Fraud/Risk evaluation block missing from claim record.", final_amount: 0 };
  }
  if (!coverage.policy_active) {
    return {
      status: "DENY",
      reason: `Policy is inactive at incident date. Reasons: ${coverage.reasons.join("; ")}`,
      final_amount: 0,
    };
  }
  if (!coverage.peril_covered) {
    return {
      status: "DENY",
      reason: `Peril is not covered under the policy. Reasons: ${coverage.reasons.join("; ")}`,
      final_amount: 0,
    };
  }
  if (fraud.risk_score >= ESCALATE_RISK) {
    return {
      status: "ESCALATE",
      reason: `High risk score detected (${fraud.risk_score} >= ${ESCALATE_RISK}). Red flags: ${fraud.red_flags.join("; ")}`,
      final_amount: coverage.covered_amount,
    };
  }
  if (coverage.covered_amount > ESCALATE_AMOUNT) {
    return {
      status: "ESCALATE",
      reason: `High covered amount detected (${usd(coverage.covered_amount)} > ${usd(ESCALATE_AMOUNT)}). Requires human approval.`,
      final_amount: coverage.covered_amount,
    };
  }
  return {
    status: "APPROVE",
    reason: "Claim approved automatically based on policy coverage and low risk score.",
    final_amount: coverage.covered_amount,
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
