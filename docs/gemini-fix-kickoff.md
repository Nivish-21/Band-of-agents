# Gemini fix + dry-run prompt — ClaimBand

The agent layer compiles but the live relay is NOT wired. Launch Gemini in the project root and paste
the prompt below. It fixes the critical bugs, then dry-runs and reports.

```
You built the ClaimBand agent layer but the live relay is not wired. A cold verification found these
defects. Fix them in THIS priority order, deploy parallel sub-agents where independent, then DRY RUN
and report. Hackathon pace — make the relay actually run end-to-end; do not gold-plate.

FIRST confirm two facts (read the Band dashboard or ask the user; do NOT guess past these):
- OWNER handle: agent cards show "@nivishnick2k/<agent>". Confirm "nivishnick2k" is correct.
- The shared ROOM/CHAT id that contains all 4 agents AND the user. If no such room exists, STOP and
  tell the user to create one (Chats > new > add @nivishnick2k/intake,/coverage,/fraud,/adjudicator).

CRITICAL FIXES (relay is dead without these):
- F1 REAL HANDOFF: In claimband/prompts/*.md, remove "include the text @coverage". Band only routes
  on a structured tool call. Instruct each agent: after running your tool, call the `send_message`
  platform tool with content = the FULL claim JSON (in a ```json block) + a one-line summary, and
  mentions = ["@nivishnick2k/<next>"] (owner-qualified handle). Intake->coverage, coverage->fraud,
  fraud->adjudicator. Adjudicator on ESCALATE mentions the human "@nivishnick2k". The relay is
  mention-triggered: wrong or missing structured mentions = nothing happens.
- F2 TOOLS MERGE FULL RECORD: Change all 4 tool wrappers (run_validate_claim, run_compute_coverage,
  run_score_risk, and a NEW run_adjudicate) to accept the full claim JSON, parse to ClaimRecord, set
  THEIR block on the record (claim.intake/coverage/fraud/decision), and return the FULL updated claim
  JSON string. The LLM then forwards it verbatim instead of re-merging. (validate_claim takes the raw
  dict; build the IntakeBlock then set claim.intake.)
- F3 WIRE MISSING TOOLS: claimband/agents/intake.py has no tool — add additional_tools with
  validate_claim. claimband/agents/adjudicator.py (CrewAI) has no tool — add additional_tools with
  adjudicate_claim (CrewAIAdapter accepts (InputModel, callable) tuples, confirmed). Update intake.md
  and adjudicator.md to tell the LLM to call the tool, never to apply rules by hand.
- F4 FIX seed.py: it uses a fabricated REST endpoint. Rewrite it to post via the SDK's real message
  API the same way agents do (create_agent_chat_message(chat_id=ROOM_ID, message with content +
  mentions=[@nivishnick2k/intake])), taking the room id and fixture name as args. Fallback documented:
  user can paste the claim JSON into the room UI mentioning intake.
- F5 (small) schema.py:88 `Optional[any]` -> `Optional[Any]`. Keep black clean.

DRY RUN (the user explicitly asked — run all three, report PASS/FAIL with evidence):
- DR1 Offline: run the 3 fixtures through the pure pipeline; confirm APPROVE/DENY/ESCALATE.
- DR2 Connectivity: write claimband/dryrun.py that (a) sends a 1-token ping to Groq and to Gemini and
  prints OK/fail, (b) starts each of the 4 agents briefly and confirms each logs a WebSocket connect
  + room join, (c) sends ONE structured test message into the room and confirms it lands. Report each.
- DR3 Live relay: start all 4 agents, seed clean.json, and watch Intake->Coverage->Fraud->Adjudicator
  ->decision appear in the room. Repeat for deny.json (->DENY) and fraud.json (->ESCALATE). Capture
  room message excerpts as evidence.

Then check the 6 acceptance criteria in docs/prd.md. Fix any failures and re-run DR3 until green or
until you hit a hard blocker (no room, bad handle, adapter/API mismatch) — then STOP and report
exactly what is needed. Update docs/status.md and docs/changelog.md with results. Do not commit
secrets. Verify SDK method/arg names against the installed band-sdk before relying on them.

REPORT FORMAT: a table of F1-F5 (done/blocked), DR1-DR3 (pass/fail + evidence), and each acceptance
criterion (pass/fail). List any remaining bugs for the planner to triage.
```

## Launch
```bash
cd /Users/nivish/development/Band-of-agents && gemini
```
```
