# ClaimBand — Executable Spec (PRD)

Generated via gstack `/spec`. Line: **Auto insurance**. Orchestration: **deterministic relay + one real discovery event**. File-only (no git repo yet).

## Context
Auto-claims teams triage every claim by hand: check the policy, judge the damage, sniff for fraud, decide. ClaimBand shows four specialist AI agents — each on a different framework and model vendor — doing that triage by talking to each other inside one Band room, with a human approving anything risky. Band is the coordination layer: the agents hand off a shared claim record, append their findings, and recruit each other. Built for the Band of Agents hackathon (Track 3). Deadline 19 Jun 2026 20:30 IST.

## Current State
Greenfield. Decisions locked in `docs/decisions.md`. SDK verified at `/tmp/thenvoi-sdk-python`: `band-sdk`, `Agent.create(adapter, agent_id, api_key, ws_url, rest_url)`, adapters `LangGraphAdapter / GeminiAdapter / CrewAIAdapter`. 4 remote agents created in Band (creds in hand). Free Gemini + Groq keys in hand.

## Proposed Change — the system

### Agents (role → framework → free vendor → output)
| Agent | Job | Framework | Vendor / model | Emits |
|---|---|---|---|---|
| **Intake** | Validate required fields, normalise, flag missing/inconsistent data, score completeness | LangGraph | Groq `llama-3.3-70b-versatile` | `intake` block + handoff to Coverage |
| **Coverage** | Policy active at incident date? peril covered? within limits? apply deductible → `covered_amount` | Gemini SDK | Gemini `2.5-flash` | `coverage` block + handoff to Fraud |
| **Fraud/Risk** | Red-flag scan → `risk_score` 0-100 + reasons | LangGraph | Groq `openai/gpt-oss-120b` | `fraud` block + handoff to Adjudicator |
| **Adjudicator** | Synthesise → `APPROVE / DENY / ESCALATE`; @mention human on escalate | CrewAI | Gemini `2.5-flash` | final `decision` block |

### Shared claim record (the structured context passed through Band)
```json
{
  "claim_id": "CLM-1001",
  "policy": {
    "policy_id": "POL-552", "status": "active",
    "effective_date": "2026-01-01", "expiry_date": "2026-12-31",
    "coverage": {"collision": true, "liability_limit": 50000, "deductible": 500}
  },
  "claimant": {"name": "Jane Doe", "is_policy_holder": true, "prior_claims_12mo": 0},
  "incident": {
    "date": "2026-06-10", "type": "collision", "at_fault": "other_party",
    "police_report": true, "description": "Rear-ended at a stop light."
  },
  "damage": {"vehicle": "2021 Honda Civic", "estimate_amount": 4200, "photos_count": 6},
  "amount_claimed": 4200,
  "intake": null, "coverage": null, "fraud": null, "decision": null
}
```
Each agent fills its own block and re-posts the record; downstream agents read the accumulated context. Band carries it.

### Handoff protocol (deterministic relay)
1. A claim is posted to the room (seed script or human paste).
2. Intake validates → posts `intake` block → `@coverage`.
3. Coverage computes `covered_amount` → `@fraud`.
4. Fraud scores risk → `@adjudicator`.
5. Adjudicator decides. **Discovery flourish:** if the `fraud` block is missing or `risk_score` is in the ambiguous band (40–60), Adjudicator uses Band peer discovery to recruit the Fraud agent for a second pass before deciding — a genuine, conditional recruitment event, not a scripted call.
6. ESCALATE → Adjudicator `@mention`s the human in the room.

### Decision rules (Adjudicator)
- Not covered (policy inactive at incident date OR peril not in coverage) → **DENY** (reason).
- `risk_score >= 60` OR `covered_amount > 10000` → **ESCALATE** to human.
- Else → **APPROVE** with `covered_amount = min(estimate, limit) - deductible`.

## Acceptance Criteria (pass/fail)
1. Posting `CLM-CLEAN` runs Intake→Coverage→Fraud→Adjudicator and ends in **APPROVE** with correct `covered_amount`, all steps visible in the Band room.
2. `CLM-DENY` (expired policy or uncovered peril) ends in **DENY** with the specific reason.
3. `CLM-FRAUD` (≥3 red flags) yields `risk_score >= 60` and ends in **ESCALATE** with a human @mention.
4. The four agents demonstrably run different frameworks AND vendors (shown in startup logs).
5. At least one genuine Band peer-discovery/recruitment event fires on the ambiguous-risk path.
6. A full 3-claim run completes with no agent crash; WebSocket reconnect handled.

## Testing Plan
| Layer | What | Count |
|---|---|---|
| Unit (TDD) | `validate_claim()`, `compute_coverage()`, `score_risk()` — pure functions, all branches | +9 |
| Integration | post fixture → assert relay order + each block populated (BandLink stubbed) | +3 |
| E2E | live room run on the 3 fixtures, manual verify against criteria 1-6 | 3 runs |

## Files Reference
| File | Purpose |
|---|---|
| `claimband/schema.py` | pydantic `ClaimRecord` + block models |
| `claimband/coverage.py` | `compute_coverage()` pure fn |
| `claimband/scoring.py` | `score_risk()` pure fn (red-flag rules) |
| `claimband/agents/{intake,coverage,fraud,adjudicator}.py` | one runnable agent each |
| `claimband/prompts/*.md` | per-agent system prompt + handoff protocol |
| `claims/{clean,deny,fraud}.json` | 3 fixtures |
| `tests/test_*.py` | unit + integration |
| `agent_config.yaml`, `.env` | creds (gitignored) |
| `README.md` | architecture + run steps |

## Out of Scope
OCR/PDF vision, custom dashboard, database/persistence, auth, real payouts, multi-line support, partner-prize providers.

## Effort
~2h schema+pure logic+TDD · ~3h four agents · ~2h wiring + live room · ~2h README/deck/recording. ~9h.

## Rollback / risk
Pure functions + fixtures, no external writes beyond LLM calls. Demo risk = free-tier 429 (mitigate: low call count, re-run) and WebSocket drop (mitigate: SDK reconnect, agents idempotent on re-post).
