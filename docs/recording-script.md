# ClaimBand Hackathon Demo Script (3:00)

## Pre-flight Checklist

Before recording, confirm:
- [ ] Band.ai room created and ID set in relay.py (BAND_ROOM_ID)
- [ ] Four agents connected: intake_agent, coverage_agent, fraud_agent, adjudicator_agent
- [ ] PYTHONPATH includes Band SDK and all agent frameworks (LangGraph, Gemini, CrewAI)
- [ ] Groq and Gemini API keys set (.env)
- [ ] Test data files ready: clean.json, fraud.json, deny.json
- [ ] Band room UI visible on screen (zoom 100%, contrast high for visibility)

---

## Beat 1: Hook + Problem (0:00–0:20) [20 seconds]

**ON SCREEN:** Title slide: "ClaimBand — Four Remote Agents, One Band Room"

**NARRATION:**
Insurance claims are high-stakes. An incorrect decision — approved when it should be denied, or delayed when it should be approved — costs both claimant and company. Every decision must be auditable: who reviewed it, why it was approved, rejected, or escalated. That's not easy when multiple systems are involved. Today we're showing how four independent remote agents — built on different frameworks and different LLM vendors — collaborate in one Band room to make decisions that are fast, transparent, and explainable.

---

## Beat 2: Architecture (0:20–0:50) [30 seconds]

**ON SCREEN:** Architecture diagram: Intake (LangGraph/Groq) → Coverage (Gemini-native) → Fraud (LangGraph/Groq) → Adjudicator (CrewAI/Groq), all funnelling into ONE Band room. Show data flow as fenced JSON. Highlight "deterministic relay" with a checkmark.

**NARRATION:**
Four agents, three frameworks. Intake uses LangGraph with Groq. Coverage runs Gemini's native SDK. Fraud is LangGraph again, also Groq. Adjudicator is CrewAI on Groq. They don't share code. They don't share memory. What they share is a single Band room and a deterministic relay protocol. The claim data flows as fenced JSON — structure guaranteed, schema validated, never lost. Each agent reads the latest state, adds its analysis, and hands off. The LLM only writes a one-line narrative note. We do this because free-tier LLMs can't reliably shuttle JSON over network hops. This architecture does. Let's see it in action.

---

## Beat 3: Demo 1 — Clean Claim (0:50–1:30) [40 seconds]

**ON SCREEN:** Terminal or UI showing Band room context. Initially empty or minimal. Begin demo by posting clean.json (CLM-CLEAN).

**FILE DETAILS FROM EVIDENCE:**
- Claimant: Jane Doe (policy holder)
- Policy: POL-552, active 2026-01-01 to 2026-12-31
- Incident: 2026-06-10, collision, rear-ended, police report filed, 6 photos
- Estimate: $4,200
- Expected decision: APPROVE $3,700 (min($4200, $50000 limit) - $500 deductible)

**NARRATION:**
Here's claim CLM-CLEAN. Jane Doe, policy holder, rear-ended at a stop light. Police report, six photos, clear case. We post it to the Band room. Watch what happens next.

*[Pause for visual: first relay step appears in Band room]*

Intake Agent goes first. It validates the intake — all fields present, no inconsistencies. It narrates: "Claim intake is valid with no missing fields or inconsistencies." and hands off to Coverage.

*[Pause for second message]*

Coverage Agent runs the policy logic. Policy is active, collision is covered, deductible applies. It narrates: "Policy is active, peril covered, $500 deductible applied, resulting in a $3,700.00 covered amount."

*[Pause for third message]*

Fraud Agent now checks for risk flags. No missing police report, claimant has zero prior claims in the past year, six photos submitted. Risk score: zero. Narration: "Claim appears legitimate with a risk score of 0 and no red flags."

*[Pause for final Adjudicator message — the emotional peak]*

And finally, Adjudicator synthesizes all three signals. No coverage issues, no fraud risk. Final decision: APPROVE $3700. The entire relay completes in seconds. All messages are in the Band room — auditable, timestamped, decision logic transparent.

---

## Beat 4: Demo 2 — Fraud Case with Escalation (1:30–2:10) [40 seconds]

**ON SCREEN:** Clear Band room. Now post fraud.json (CLM-FRAUD).

**FILE DETAILS FROM EVIDENCE:**
- Claimant: Jane Doe, now with 3 prior claims in last 12 months
- Incident: 2026-06-10, collision, self-inflicted (at_fault: self), no police report
- Damage: 1 photo only
- Expected decision: ESCALATE (risk_score = 60, which equals threshold)
- Human escalation: @nivishnick2k (from evidence message)

**NARRATION:**
Now a riskier case. CLM-FRAUD. Same claimant, but this time self-inflicted collision, no police report, only one photo, and she's had three claims in the past year. Same relay structure. Intake validates — data is complete, it passes through. Coverage calculates — peril covered, $3,700 payable. But then Fraud Agent runs its checks.

*[Pause for Fraud Agent message showing risk_score: 60]*

Three red flags triggered: no police report, three prior claims, insufficient photos. Risk score climbs to 60. That equals our threshold. Adjudicator reads the full state and makes the call: ESCALATE.

*[Highlight the final Adjudicator message with the @mention]*

Look at this line: "@nivishnick2k this claim is ESCALATED for human review." The system identified high fraud risk and called in a human expert by name. That's human-in-the-loop. The data is ready, the LLM's reasoning is logged, and a real person now makes the final call. No guesswork. No secret scoring. Complete transparency.

---

## Beat 5: Quick Third Case + Resilience (2:10–2:40) [30 seconds]

**ON SCREEN:** Clear room. Post deny.json (CLM-DENY).

**FILE DETAILS FROM EVIDENCE:**
- Policy: POL-552, status "expired" (effective 2025-01-01 to 2025-12-31)
- Incident: 2026-06-10 (one year later — well outside coverage window)
- Expected decision: DENY (policy expired before incident)

**NARRATION:**
One more case to show the system's breadth. CLM-DENY. Same car, same claimant, but the policy expired six months before this incident. Intake passes it through. Coverage checks the policy dates — expired, incident is outside the coverage window. Narration: "Policy expired before incident date; no coverage despite peril being covered." Fraud scores it as legitimate but irrelevant. Adjudicator's decision: DENY. Policy was not active. Coverage terminated.

*[Brief pause]*

One more thing: Gemini's free tier has a 429 rate limit. If the relay hits that cap during Coverage's call, the relay falls back to a template note — still completes, still auditable, still makes a decision. No crashes. That's resilience by design.

---

## Beat 6: Close (2:40–3:00) [20 seconds]

**ON SCREEN:** Show final Band room with all three demo cases logged (CLM-CLEAN: APPROVE, CLM-FRAUD: ESCALATE, CLM-DENY: DENY). Fade to title: "Band of Agents Hackathon — Track 3"

**NARRATION:**
Three cases, three outcomes: approve, escalate, deny. Each one moved through four independent remote agents built on different frameworks and different LLM vendors. Each one stayed auditable. Each one stayed fast. The insight is simple: put the data in a shared, deterministic context; let each agent add its view; keep the LLM as a narrator, not a data router. Band makes that possible. Agents orchestrate. Decisions stick.

Band of Agents Hackathon — Track 3. Thank you.

---

## Timing Breakdown

| Beat | Time | Duration | Content |
|------|------|----------|---------|
| 1. Hook + Problem | 0:00–0:20 | 20s | Why claims are hard; audit trail required |
| 2. Architecture | 0:20–0:50 | 30s | Four agents, three frameworks, two vendors; why deterministic relay |
| 3. Demo 1 (Clean) | 0:50–1:30 | 40s | CLM-CLEAN relay: Intake → Coverage → Fraud → Adjudicator APPROVE |
| 4. Demo 2 (Fraud Escalation) | 1:30–2:10 | 40s | CLM-FRAUD relay: risk_score 60 → ESCALATE + @human mention |
| 5. Demo 3 + Resilience | 2:10–2:40 | 30s | CLM-DENY (expired policy) → DENY; note on 429 fallback |
| 6. Close | 2:40–3:00 | 20s | Recap; title slide; thank you |
| **TOTAL** | **0:00–3:00** | **180s** | **Exactly 3 minutes** |

---

## Presenter Notes

- **Pacing:** Each beat assumes natural narrator pauses while visuals update. Do not rush the Band room transitions — let the audience see each agent's message appear.
- **Emotional peak:** Beat 4 (Escalation). Emphasize the @mention. This is the human-in-the-loop moment — the system's most distinctive feature.
- **Visual cues:** Keep Band room chat visible at all times. Use color or highlight to show which agent is "speaking" in each step.
- **Tone:** Confident, concrete. British English. No jargon without context (explain "deterministic relay" once, then use it).
- **Safety:** Have all three JSON files pre-posted in a test room. If live demo stutters, cut to the recorded replay. No apologies; just move forward.
