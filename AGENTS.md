# AGENTS.md — Build handoff for ClaimBand

You (Codex / any coding agent) are the **builder**. The planning is done. Build the system described here. A sibling `GEMINI.md` carries the same instructions for Gemini CLI; this file is canonical.

## Read these first (source of truth)
1. `docs/prd.md` — the executable spec (claim schema, agents, decision rules, acceptance criteria). **Authoritative.**
2. `docs/plan.md` — phased build plan with checkboxes.
3. `docs/decisions.md` — why each choice was made (do not re-litigate).
4. `docs/status.md` — current state.

## What you are building (one paragraph)
**ClaimBand**: 4 remote AI agents adjudicate an **auto-insurance** claim by collaborating in one **Band** room (band.ai) over WebSocket. A claim JSON is posted; agents hand off a shared, progressively-enriched claim record: **Intake** (validate) → **Coverage** (compute covered amount) → **Fraud** (risk score) → **Adjudicator** (APPROVE / DENY / ESCALATE-to-human). Each agent runs a different framework AND model vendor. Demo surface is the live Band room — no frontend.

## Tech stack (verified — do not rediscover)
- Python 3.12, venv.
- SDK: `band-sdk` (formerly `thenvoi`). Install:
  ```bash
  python3.12 -m venv .venv && source .venv/bin/activate
  pip install "band-sdk[langgraph,gemini,crewai] @ git+https://github.com/thenvoi/thenvoi-sdk-python.git" \
              langchain-openai python-dotenv pydantic pytest
  ```
  (`langgraph` extra bundles `langchain-openai`; `gemini` bundles `google-genai`; `crewai` bundles CrewAI.)
- Imports: `from band import Agent`; `from band.adapters import LangGraphAdapter, GeminiAdapter, CrewAIAdapter`; `from band.config import load_agent_config`; `from band.core.types import AdapterFeatures, Emit`.
- Connect (all agents):
  ```python
  agent = Agent.create(adapter=adapter, agent_id=AID, api_key=KEY,
                       ws_url=os.environ["BAND_WS_URL"], rest_url=os.environ["BAND_REST_URL"])
  await agent.run()
  ```
- `agent_id, api_key = load_agent_config("intake")` (keys: intake/coverage/fraud/adjudicator). Creds in gitignored `agent_config.yaml` + `.env` (already populated).

### Adapter recipes (the cross-framework, cross-vendor core)
```python
# Intake — LangGraph + Groq Llama 3.3 70B
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
adapter = LangGraphAdapter(
    llm=ChatOpenAI(model="llama-3.3-70b-versatile",
                   base_url=os.environ["GROQ_BASE_URL"], api_key=os.environ["GROQ_API_KEY"]),
    checkpointer=InMemorySaver(), custom_section=INTAKE_PROMPT)

# Coverage — Gemini 2.5 Flash (native). Expose compute_coverage() as a tool.
adapter = GeminiAdapter(model="gemini-2.5-flash", prompt=COVERAGE_PROMPT,
                        additional_tools=[(CoverageInput, compute_coverage)],
                        features=AdapterFeatures(emit={Emit.EXECUTION}))

# Fraud — LangGraph + Groq gpt-oss-120b. Expose score_risk() as a tool.
adapter = LangGraphAdapter(
    llm=ChatOpenAI(model="openai/gpt-oss-120b",
                   base_url=os.environ["GROQ_BASE_URL"], api_key=os.environ["GROQ_API_KEY"]),
    checkpointer=InMemorySaver(), custom_section=FRAUD_PROMPT)

# Adjudicator — CrewAI routed to Gemini via litellm (needs GEMINI_API_KEY in env)
adapter = CrewAIAdapter(model="gemini/gemini-2.5-flash", role="Claims Adjudicator",
                        goal="Decide APPROVE/DENY/ESCALATE from peer findings",
                        backstory=ADJUDICATOR_BACKSTORY)
```
Verify each constructor against the installed package (`python -c "import band.adapters as a; help(a.GeminiAdapter)"`) — patch arg names if the SDK differs.

## File layout to create
```
claimband/schema.py          # pydantic ClaimRecord + block models (docs/prd.md schema)
claimband/coverage.py        # compute_coverage() — PURE
claimband/scoring.py         # score_risk() — PURE
claimband/agents/intake.py coverage.py fraud.py adjudicator.py
claimband/prompts/*.md       # system prompt + handoff protocol per agent
claims/clean.json deny.json fraud.json   # 3 fixtures
tests/test_schema.py test_coverage.py test_scoring.py test_integration.py
seed.py                      # posts a claim fixture into the Band room
README.md
```

## Build order (TDD — full rigor was chosen)
- **Phase 0:** venv + install (above). Smoke test: one agent connects to the room and posts "hello". Verify Gemini and Groq each return a completion.
- **Phase 1 (TDD pure logic):** RED→GREEN for `validate_claim`, `compute_coverage`, `score_risk` per the decision rules in `docs/prd.md`. Then build Coverage + Fraud + Adjudicator agents and get a **3-agent relay running in the room** on `clean.json`. This is the shippable floor — stop and verify before Phase 2.
- **Phase 2:** add the **Intake** agent at the front (full 4-agent relay). Implement the **discovery flourish**: Adjudicator recruits Fraud via Band peer-discovery only when `risk_score` is 40–60 or missing.
- **Phase 3:** README + run instructions. (Slide deck / recording handled separately.)

## Handoff protocol
Each agent fills its block in the claim record (`intake`/`coverage`/`fraud`/`decision`), re-posts the full record to the room, and `@mention`s the next agent. Relay: Intake→Coverage→Fraud→Adjudicator→(human on ESCALATE). Read prompts from `claimband/prompts/<role>.md`.

## Decision rules (Adjudicator) — exact
- Policy inactive at incident date OR peril not covered → **DENY** (state reason).
- `risk_score >= 60` OR `covered_amount > 10000` → **ESCALATE** + @mention human.
- Else → **APPROVE**, `covered_amount = min(estimate_amount, liability_limit) - deductible`.

## Acceptance criteria (must all pass — see docs/prd.md §Acceptance)
1. `clean.json` → APPROVE with correct covered amount, full relay visible in room.
2. `deny.json` → DENY with the specific reason.
3. `fraud.json` → risk_score≥60 → ESCALATE + human @mention.
4. 4 agents demonstrably on different frameworks + vendors (startup logs).
5. ≥1 genuine Band peer-discovery event on the ambiguous path.
6. Full 3-claim run, no crashes; WebSocket reconnect handled.

## Coding standards (non-negotiable)
- Strict typing on every function. Explicit params, no magic defaults.
- Raise errors explicitly; never swallow. Immutable data (new objects, no mutation).
- Imports at top. Validate external input (claim JSON) at the boundary via pydantic.
- Format with **Black**; lint clean before declaring done. 80%+ test coverage on pure logic.
- Read a file before editing it. Search for existing helpers before writing new ones.

## Recommended split (parallelize Codex + Gemini, no collisions)
- **Codex:** `schema.py`, `coverage.py`, `scoring.py`, and all of `tests/` (TDD, rigor).
- **Gemini:** `agents/*.py`, `prompts/*.md`, `claims/*.json` fixtures, `seed.py`.
- Integration test + live-room verification: whoever finishes first; coordinate via `docs/status.md`.

## Do NOT
- Commit secrets (`.env`, `agent_config.yaml` are gitignored — keep it that way).
- Add OCR, a frontend dashboard, a database, or auth (explicitly out of scope).
- Re-decide settled choices in `docs/decisions.md`.
- Mark a task done before tests + lint pass and `docs/status.md` + `docs/changelog.md` are updated.
