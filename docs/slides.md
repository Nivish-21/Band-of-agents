---
marp: true
theme: default
paginate: true
---

# ClaimBand

**4 remote agents adjudicate an auto-insurance claim in one Band room**

Band of Agents Hackathon — Track 3

---

## The Problem

Auto-insurance claim adjudication is regulated and high-stakes.

Decisions must be **auditable** and **reproducible**.

A single LLM making a APPROVE / DENY / ESCALATE decision is a **black box**.

Solution: **multiple agents**, each responsible for one domain (intake, coverage, fraud assessment, adjudication), collaborating through a shared Band room where the claim state is transparent and traceable.

---

## Architecture

Four REMOTE agents in ONE Band room:

- **Intake** — validates form completeness | LangGraph + Groq
- **Coverage** — checks policy status and peril coverage | Gemini SDK + Gemini
- **Fraud** — calculates risk score and flags red flags | LangGraph + Groq
- **Adjudicator** — makes final decision | CrewAI + Groq (groq/openai/gpt-oss-120b)

**Relay order**: Intake → Coverage → Fraud → Adjudicator → (human on ESCALATE)

**Three frameworks** (LangGraph, Gemini SDK, CrewAI). **Two vendors** (Groq, Gemini).

---

## Deterministic Relay Design (Why)

Free models corrupt full JSON round-trip (missing fields, structure drift).

**Design**: claim JSON stays in shared Band room context as fenced code. Python relay layer (Pydantic) copies, validates, and updates the record. **LLM narrates only** a human-readable one-line note (template fallback if vendor fails).

**Why this wins**:
- Data path is deterministic, never through an LLM
- Round-trip payloads exact
- Relay is idempotent (skips if agent block filled)
- Resilient to vendor outage (graceful fallback)

---

## Decision Rules

```
if not policy_active:
  → DENY

elif risk_score >= 60 OR covered_amount > 10000:
  → ESCALATE + @human

else:
  → APPROVE
  final_amount = min(estimate, limit) - deductible
```

---

## Demo: CLM-CLEAN → APPROVE

```
**Adjudicator Agent** — Claim approved for $3700 based on policy coverage and low risk score.

Final decision: **APPROVE**.

{
  "decision": {
    "status": "APPROVE",
    "reason": "Claim approved automatically based on policy coverage and low risk score.",
    "final_amount": 3700.0
  }
}
```

Claim CLM-CLEAN: active policy, collision covered, $0 deductible net ($4200 − $500), low fraud risk → approved for $3700.

---

## Demo: CLM-DENY → DENY

```
**Coverage Agent** — Policy expired before incident date; no coverage despite peril being covered.

"Policy status is 'expired' (expected 'active')."
"Incident date 2026-06-10 falls outside the policy period (2025-01-01 to 2025-12-31)."
```

Policy expired on 2025-12-31; incident occurred 2026-06-10. Outside policy period → covered_amount = $0.00 → **DENY**.

---

## Demo: CLM-FRAUD → ESCALATE

```
@[[5f4ed8cf-e454-4854-a1cc-d57b1c296d9c]] this claim is **ESCALATED** for human review.

{
  "fraud": {
    "risk_score": 60,
    "red_flags": [
      "No police report filed for the incident.",
      "Claimant has 3 prior claim(s) in the last 12 months.",
      "Low photo count (1 photos provided, minimum of 3 expected)."
    ]
  },
  "decision": {
    "status": "ESCALATE",
    "final_amount": 3700.0
  }
}
```

Risk score 60 (threshold hit) with three red flags → escalated to human (5f4ed8cf = nivishnick2k).

---

## Resilience: Free-Tier Fallback

In the CLM-FRAUD run, Gemini hit its free-tier 429 cap (20 requests/day) on Coverage's note call.

Relay fell back to template note: *"Policy active, peril covered, deductible applied."*

**Claim still completed successfully.**

Relay design ensures graceful degradation: data round-trips exactly; LLM narration is best-effort, never on the critical path.

---

## Why This Wins

**Cross-framework, cross-vendor collaboration through ONE Band room.**

Not a monolithic LLM. Not a rigid pipeline. Interop is the competitive point.

- Intake can fail → Adjudicator still sees the record and logs it.
- Coverage vendor (Gemini) can hit rate limits → relay uses fallback.
- Fraud agent (CrewAI) can be swapped for LangGraph without touching others.

Each agent is **replaceable**. Each decision is **auditable**. The Band room is the source of truth.

---

## Status: Acceptance Criteria

✅ **1,2,3,6** — PASS
- Problem well-defined; architecture proven; decisions auditable; three fixtures (CLEAN, DENY, FRAUD) execute end-to-end with real agent outputs

⚠️ **4 (framework/vendor diversity)** — PARTIAL
- Real and proven at runtime (LangGraph + Gemini SDK + CrewAI, Groq + Gemini vendors all present and working)
- Not printed in a banner; observable in code and live runs only

❌ **5 (Band peer-discovery on ambiguous risk band)** — NOT YET
- Deterministic relay uses fixed agent routing
- Peer-discovery on the 40–60 risk band (Band's dynamic feature) not yet demonstrated

Honest assessment: the core innovation (deterministic relay, cross-framework orchestration, Band as audit log) works. The hackathon scope didn't cover dynamic peer-discovery.

---

## Next Steps

- Wire up Band peer-discovery for the 40–60 ambiguous risk band (requires accepting dynamic routing)
- Expand fixture coverage (high-amount claims, complex multi-peril policies)
- Production hardening: retry logic, timeout handling, human-in-the-loop escalation workflow
