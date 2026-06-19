import scenariosJson from "../data/scenarios.json";

export type Agent = {
  key: string;
  name: string;
  framework: string;
  vendor: string;
  produces: string;
};

export type IntakeBlock = {
  is_valid: boolean;
  missing_fields: string[];
  inconsistencies: string[];
  completeness_score: number;
} | null;

export type CoverageBlock = {
  policy_active: boolean;
  peril_covered: boolean;
  deductible_applied: number;
  covered_amount: number;
  reasons: string[];
} | null;

export type FraudBlock = {
  risk_score: number;
  red_flags: string[];
  reasons: string[];
  rule_risk?: number;
  narrative_risk?: number;
  narrative_rationale?: string;
} | null;

export type DecisionBlock = {
  status: "APPROVE" | "DENY" | "ESCALATE" | string;
  reason: string;
  final_amount: number | null;
} | null;

export type ClaimRecord = {
  claim_id: string;
  policy: {
    policy_id: string;
    status: string;
    effective_date: string;
    expiry_date: string;
    coverage: { collision: boolean; liability_limit: number; deductible: number };
  };
  claimant: { name: string; is_policy_holder: boolean; prior_claims_12mo: number };
  incident: {
    date: string;
    type: string;
    at_fault: string;
    police_report: boolean;
    description: string;
  };
  damage: { vehicle: string; estimate_amount: number; photos_count: number };
  amount_claimed: number;
  intake: IntakeBlock;
  coverage: CoverageBlock;
  fraud: FraudBlock;
  decision: DecisionBlock;
};

export type Message = { n: number; sender: string; time: string; content: string };

export type Scenario = {
  key: "clean" | "deny" | "fraud" | string;
  label: string;
  blurb: string;
  claim_id: string;
  outcome: "APPROVE" | "DENY" | "ESCALATE" | string;
  reason: string;
  final_amount: number | null;
  claim: ClaimRecord;
  record: ClaimRecord;
  messages: Message[];
};

export type ShowcaseData = {
  agents: Agent[];
  scenarios: Record<string, Scenario>;
};

export const data = scenariosJson as unknown as ShowcaseData;
export const agents = data.agents;
export const scenarioOrder = ["clean", "deny", "fraud"] as const;
export const scenarios = scenarioOrder.map((k) => data.scenarios[k]);
