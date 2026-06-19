# GEMINI.md — Build handoff for ClaimBand (Gemini CLI)

You (Gemini CLI) are a **builder** on this project. Planning is done by the planner; your job is to build. **`AGENTS.md` is the canonical, complete build spec — read it in full.** This file is the Gemini-facing entry point and repeats the essentials so you can start cold.

## Read first (source of truth, in order)
1. `AGENTS.md` — full build spec (SDK API, adapter recipes, file layout, standards).
2. `docs/prd.md` — claim schema, decision rules, acceptance criteria. Authoritative.
3. `docs/decisions.md` — locked decisions (do not re-open).
4. `docs/plan.md`, `docs/status.md` — plan + current state.

## What you are building
**ClaimBand**: 4 remote agents adjudicate an **auto-insurance** claim by collaborating in one **Band** room (band.ai). A claim JSON is posted and handed off, each agent enriching a shared record: **Intake → Coverage → Fraud → Adjudicator** (APPROVE / DENY / ESCALATE-to-human). Each agent uses a different framework + free model vendor. Demo = the live Band room; no frontend.

## Your recommended slice (Codex takes the rest)
Per the split in `AGENTS.md`:
- **Gemini (you):** `claimband/agents/*.py`, `claimband/prompts/*.md`, `claims/{clean,deny,fraud}.json`, `seed.py`.
- **Codex:** `schema.py`, `coverage.py`, `scoring.py`, `tests/`.
Coordinate through `docs/status.md`. Import the pure functions Codex writes (`compute_coverage`, `score_risk`) and expose them as agent tools — do not reimplement them.

## Essentials to start (full detail in AGENTS.md)
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install "band-sdk[langgraph,gemini,crewai] @ git+https://github.com/thenvoi/thenvoi-sdk-python.git" \
            langchain-openai python-dotenv pydantic pytest
```
- `from band import Agent`; `from band.adapters import LangGraphAdapter, GeminiAdapter, CrewAIAdapter`; `from band.config import load_agent_config`.
- `Agent.create(adapter=..., agent_id=..., api_key=..., ws_url=BAND_WS_URL, rest_url=BAND_REST_URL)` then `await agent.run()`.
- Creds already in gitignored `.env` + `agent_config.yaml`. `load_agent_config("intake")` → `(agent_id, api_key)`.
- Adapter recipes (Intake=LangGraph/Groq, Coverage=Gemini native, Fraud=LangGraph/Groq, Adjudicator=CrewAI/Gemini): copy from `AGENTS.md` §"Adapter recipes" verbatim; verify arg names against the installed package.

## Handoff + decision rules (exact)
- Relay: each agent fills its block, re-posts the claim record, `@mention`s the next. Intake→Coverage→Fraud→Adjudicator→(human on ESCALATE).
- Adjudicator: not covered → DENY; `risk_score>=60` or `covered_amount>10000` → ESCALATE + @human; else APPROVE with `covered_amount = min(estimate, limit) - deductible`.
- Discovery flourish: Adjudicator recruits Fraud via Band peer-discovery only when `risk_score` is 40–60 or missing.

## Standards (non-negotiable — same as AGENTS.md)
Strict typing, explicit errors, immutable data, imports at top, pydantic validation at the claim boundary, **Black** formatting, lint clean. Build Phase 0 (connect smoke test) → Phase 1 (3-agent floor on `clean.json`) → Phase 2 (add Intake = 4 agents) → Phase 3 (README). Verify all 6 acceptance criteria in `docs/prd.md`.

## Do NOT
Commit secrets; add OCR / dashboard / DB / auth; re-decide settled choices; mark done before tests + lint pass and `docs/status.md` is updated.

## ⚠️ UNATTENDED / AUTONOMOUS MODE — HARD GUARDRAILS (read this)
You are running with auto-approval (YOLO): no human will confirm your commands. That trust is
conditional. **NEVER do anything irreversible or outward-facing without a human present.** Specifically:

**FORBIDDEN while unattended (do not run, ever, without explicit human go-ahead):**
- `git push`, `gh pr ...`, `gh issue ...`, any publish to GitHub or a remote. Local commits are fine.
- Deleting or overwriting anything you did not create this session: Band **rooms/messages**, files,
  branches. The Phase 6 "delete orphan rooms" step is **DEFERRED** — leave the orphan rooms for the
  user; do NOT delete them, and do NOT run/repair `clear_room.py` unattended.
- `pip install` / `npm i -g` / any global or outside-`.venv` install. Use the existing `.venv` only:
  run Python as `PYTHONPATH=. ./.venv/bin/python ...`.
- `rm -rf`, `git reset --hard`, `git clean -fd`, or any bulk delete.
- Sending project data anywhere except the app's own APIs (Band, Groq, Gemini). No new `curl`/`wget`
  POSTs to other hosts. Never echo or commit `.env` / `agent_config.yaml` contents.
- Editing anything outside `/Users/nivish/development/Band-of-agents`.

**ALLOWED (this is the whole point of autonomy):** run the venv Python, `run_all.py`, `seed.py`,
`pytest`, `black`, the dump/inspect scripts; create/edit files under the project; write `docs/*`.

**When you hit something forbidden or are genuinely unsure about an irreversible step:** STOP, write
the open question + your recommendation into `docs/status.md` under a "BLOCKED — needs human" heading,
and move on to other allowed work. Do not guess your way through an irreversible action.

**Reporting honesty:** do not mark a step "complete" or "verified" unless you have the actual evidence
(the real room messages / passing test output) in hand and saved to `docs/evidence/`. Earlier reports
claimed success that the room did not show — the planner cold-verifies against `docs/evidence/*`, so a
false "done" will be caught. State what actually happened, including failures and skips.
