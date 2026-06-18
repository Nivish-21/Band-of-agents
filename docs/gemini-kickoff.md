# Gemini kickoff prompt — ClaimBand agent layer

Launch Gemini CLI in the project root (`/Users/nivish/development/Band-of-agents`) and paste the prompt below.

```
You are the lead builder for ClaimBand. Build the entire Band/agent layer NOW, fast, using
parallel sub-agents. This is a hackathon — prioritise a working live demo over polish; do NOT
over-engineer or optimise for scale. Strict typing + black formatting still apply.

STEP 0 — Read, in order: GEMINI.md, AGENTS.md, docs/prd.md, docs/plan.md (the "Phase 2 — Agent
layer" section has the RESOLVED Band API contract), docs/status.md. The Python pure-logic floor
is DONE by Codex — do NOT touch or rebuild claimband/schema.py, coverage.py, scoring.py,
adjudication.py, or tests/ (18 tests pass). Activate the venv: `source .venv/bin/activate`.

CONTRACT (verified against the SDK — build to it, don't rediscover):
- Handoff: `await tools.send_message(content, mentions=["@OWNER/agent"])`. Mentions REQUIRED.
  Handles are `@<owner>/<agent>`; confirm OWNER from the Band dashboard (likely "nivishnick2k").
- Discovery: `tools.add_participant("@OWNER/fraud")`, `tools.lookup_peers()`.
- Each agent registers ONE domain tool via `additional_tools=[(PydanticInputModel, fn)]` wrapping a
  Codex pure function. Tool signature: `tool(claim_json: str) -> str` (parse to ClaimRecord, run the
  pure fn, set the agent's block, return updated claim JSON). Prompt makes the LLM send_message that
  JSON in a ```json fenced block + a one-line summary, mentioning the next agent.
- Relay: Intake→@coverage, Coverage→@fraud, Fraud→@adjudicator, Adjudicator→@OWNER (human) on
  ESCALATE else posts final decision. Discovery flourish: Adjudicator, if fraud block missing OR
  risk_score==40, recruits @OWNER/fraud via add_participant + send_message before deciding.
- Adapter recipes are in AGENTS.md (Intake=LangGraph/Groq llama-3.3-70b, Coverage=Gemini 2.5-flash,
  Fraud=LangGraph/Groq gpt-oss-120b, Adjudicator=CrewAI gemini/gemini-2.5-flash). Verify each
  adapter's constructor arg names against the installed band-sdk before relying on them.

BUILD PLAN with sub-agents:
1. FOUNDATION (do this FIRST, single-threaded, then freeze it): build claimband/band_io.py
   (`extract_claim(text)->dict` = parse LAST ```json block; `format_handoff(claim, summary)->str`;
   `OWNER` constant + next-agent handle map) and claimband/tools.py (4 domain-tool callables +
   pydantic input models, importing the existing pure functions). Also write the 4 prompt files
   claimband/prompts/{intake,coverage,fraud,adjudicator}.md (strict: "call your tool, then
   send_message the returned JSON in a ```json block, mention @OWNER/<next>; NEVER skip handoff").
2. PARALLEL SUB-AGENTS (only after step 1 is frozen): dispatch one sub-agent per file, in parallel:
   claimband/agents/intake.py, coverage.py, fraud.py, adjudicator.py, and seed.py. Each imports
   band_io + tools, calls `Agent.create(adapter=..., agent_id/api_key from load_agent_config(role),
   ws_url/rest_url from env)` then `await agent.run()`. seed.py posts a chosen fixture into the room
   mentioning @OWNER/intake.
3. VERIFIER SUB-AGENT (after build): 
   a. Phase 0 smoke — run one agent, confirm it connects to the room and replies. Confirm a single
      Band chat/room contains all 4 agents AND the user (mentions fail otherwise — if missing, STOP
      and report; the user must create the room).
   b. Live run all 3 fixtures (clean→APPROVE, deny→DENY, fraud→ESCALATE) through the full relay.
   c. Confirm the 6 acceptance criteria in docs/prd.md, including: 4 agents on different
      frameworks+vendors (startup logs) and ≥1 genuine Band discovery event.
   d. Report PASS/FAIL per criterion with evidence (room message excerpts / logs). Fix failures.

RULES: don't commit secrets (.env, agent_config.yaml are gitignored); no OCR/dashboard/DB/auth;
update docs/status.md and docs/changelog.md when done. If blocked (e.g. no shared room, bad handle,
adapter arg mismatch), STOP and report exactly what's needed — don't guess past a hard blocker.
```

## Launch command
```bash
cd /Users/nivish/development/Band-of-agents && gemini
```
Then paste the prompt above. (If your Gemini CLI uses a flag for sub-agents/parallel tasks, enable it.)
