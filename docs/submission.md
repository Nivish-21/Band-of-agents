# ClaimBand — lablab.ai submission fields

Copy-paste source for the Band of Agents Hackathon submission form. Track 3
(Regulated & High-Stakes Workflows).

---

## Project Title
ClaimBand

## Short Description
ClaimBand is a cross-framework, multi-agent auto-insurance claim adjudicator: four
specialist AI agents — each on a different framework and model vendor — collaborate inside
one Band room to triage a claim and decide APPROVE, DENY, or ESCALATE-to-human.

## Long Description
Auto-insurance teams triage every claim by hand: check the policy, judge the damage, sniff
for fraud, then decide. ClaimBand turns that into a collaborative multi-agent workflow on Band.

Four remote agents work a shared claim record inside a single Band room, each enriching it and
handing off to the next via `@mention`:

- **Intake** (LangGraph + Groq) — validates required fields and flags missing data or
  inconsistencies (e.g. estimate ≠ amount claimed).
- **Coverage** (Gemini SDK + Gemini) — checks policy status, dates, and peril, then computes the
  covered amount = min(estimate, limit) − deductible.
- **Fraud** (LangGraph + Groq) — scores risk 0–100 from six red-flag heuristics (no police
  report, prior claims, low photo count, non-policyholder, high amount, incident near policy start).
- **Adjudicator** (CrewAI + Groq) — synthesizes the record into the final verdict and, on an
  escalation, broadcasts it to the band and **@mentions a human reviewer**.

That's **3 frameworks and 2 vendors collaborating through one Band room**. Band is the actual
coordination layer: agents exchange a structured claim record as shared room context, route work
with mentions, and broadcast the verdict to the whole band — not a thin wrapper or a final
notification channel.

**Why a deterministic relay (design decision D13):** free-tier models cannot reliably copy a full
claim JSON hop-to-hop without corrupting it, so the *data* flows through Band's shared context as
fenced JSON (deterministically copied and pydantic-validated), while the LLM produces only a
one-line human-readable note. The data path never depends on a model call — which also makes the
relay resilient: when Gemini's free tier returns HTTP 429, Coverage falls back to a template note
and the relay still completes end-to-end.

**Decision rules.** Not covered (inactive policy / uncovered peril) → DENY. risk_score ≥ 60 or
covered_amount > $10,000 → ESCALATE + human @mention. Otherwise APPROVE.

**Verified live (evidence in `docs/evidence/`).** Three fixtures run end-to-end in fresh Band rooms:
`clean` → APPROVE $3,700; `deny` → DENY (policy expired); `fraud` → ESCALATE (risk 60, human
@mentioned). A one-command runner (`demo.py`) reproduces any case. 38 automated tests pass.

**Honest scope.** 5 of 6 internal acceptance criteria pass; Band peer-discovery/recruitment on the
ambiguous-risk path is designed but not yet demonstrated. No frontend — the live Band room is the
demo surface.

## Technology & Category Tags
`multi-agent` `Band` `cross-framework` `LangGraph` `CrewAI` `Gemini` `Groq` `pydantic`
`insurance` `claims-adjudication` `regulated-workflows` `human-in-the-loop` `Track-3`

---

## Asset checklist (for the form)
| Field | Asset | Status |
|---|---|---|
| Cover Image | `docs/cover.png` (1200×630, exported from `cover.svg`) | ready |
| Slide Presentation | `docs/slides.pdf` (rendered from `slides.md`) | ready |
| Video Presentation | script at `docs/recording-script.md` — **needs recording** | TODO (you) |
| Public GitHub Repo | `github.com/Nivish-21/Band-of-agents` — **confirm it is public** + push latest | TODO (you) |
| Application URL / Demo Platform | no frontend — see note below | DECISION NEEDED |

## Note on "Application URL / Demo Application Platform"
ClaimBand has no frontend by design; the demo surface is the live Band room. Options, safest first:
1. Use the **video** as the demo (record the live Band-room relay) and put the **GitHub repo URL**
   as the application link, if the form allows a repo/video in place of a hosted app.
2. If a working Band room link is acceptable, share the demo room URL on band.ai.
3. Only if lablab *hard-requires* a hosted, clickable web app: that means building and deploying a
   small frontend (claim submit form + live room/trail view) — real additional scope, not started.
