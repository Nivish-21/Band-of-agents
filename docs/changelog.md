# Changelog

## 2026-06-18 — Project kickoff & planning
- Researched Band platform; confirmed it is a real product (Team8-backed, `band-sdk` Python SDK,
  WebSocket rooms, framework adapters). Verified SDK API against source.
- Decided project (ClaimBand, Track 3) and scope (Tier 2). See `decisions.md`.
- Created `docs/`: `plan.md`, `status.md`, `decisions.md`, `changelog.md`.
- No production code written — awaiting approval.

## 2026-06-18 — Spec + build handoff (planner role finalized)
- Ran gstack `/spec`: locked auto-insurance line + deterministic-relay orchestration. Wrote `docs/prd.md` (executable spec: claim schema, decision rules, acceptance criteria, testing plan).
- Decision D8: Claude plans only; Gemini + Codex build.
- Created build handoffs: `AGENTS.md` (canonical) + `GEMINI.md`.
- Created credential scaffolding: `.gitignore`, `.env(.example)`, `agent_config.yaml(.example)` — real keys gitignored.

## 2026-06-18 — Codex slice implemented (Phase 0 & 1 TDD green)
- Setup Python 3.12 virtual environment and installed all dependencies (`band-sdk`, `langchain-openai`, etc.).
- Verified `band-sdk` imports and adapters (`GeminiAdapter`, `LangGraphAdapter`, `CrewAIAdapter`).
- Created `claimband/schema.py` defining Pydantic V2 models for the ClaimRecord and agent blocks. Added `validate_claim` pure function.
- Created `claimband/coverage.py` containing the `compute_coverage` pure function.
- Created `claimband/scoring.py` containing the `score_risk` pure function.
- Created `claimband/adjudication.py` containing the `adjudicate_claim` pure function mapping the exact decision rules.
- Created three JSON fixtures under `claims/` (`clean.json`, `deny.json`, `fraud.json`).
- Wrote 18 unit and integration tests across `tests/` (`test_schema.py`, `test_coverage.py`, `test_scoring.py`, `test_integration.py`).
## 2026-06-18 — Gemini slice implemented (Phase 2 & 3)
- Wrote system prompts for Intake, Coverage, Fraud, and Adjudicator agents in `claimband/prompts/`.
- Created agent runtime scripts `claimband/agents/*.py` hooking up LangGraphAdapter, GeminiAdapter, and CrewAIAdapter.
- Bound `compute_coverage` and `score_risk` pure functions as tools to Coverage and Fraud agents respectively.
- Developed `seed.py` orchestration script to automatically load fixtures and post claims to the Band room.
- Documented project architecture and run instructions in `README.md`.

## 2026-06-18 — Gemini Hotfix & Dry Run (Phase 4)
- Fixed F1: Updated all prompts to use the `send_message` tool with structured mentions (`@nivishnick2k/<agent>`).
- Fixed F2: Modified all tool wrappers to parse, inject their specific blocks, and return the full updated JSON.
- Fixed F3: Wired `validate_claim` tool to Intake agent and `adjudicate_claim` tool to Adjudicator agent.
- Fixed F4: Rewrote `seed.py` to use `thenvoi_client_rest` and `create_agent_chat_message` for SDK API compatibility.
- Fixed F5: Corrected `Optional[any]` to `Optional[Any]` in `schema.py` and imported `Any`.
- Passed DR1: Offline tests ran successfully via `pytest`.
- Passed DR2: Connectivity tests passed. LLMs (Groq, Gemini) pinged successfully. All 4 Agents successfully connected and joined the Band room `BAND_ROOM_ID`.
- Blocked DR3 (Re-run): Live relay failed on all fixtures. Swapping Intake Agent to `gpt-oss-120b` resulted in a new error: `Tool call validation failed: missing properties: 'claim_record_json'`. Additionally, the Coverage Agent (Gemini) misbehaved, outputting a chat message complaining about `CoverageInput` type mismatch, before hitting a `429 RESOURCE_EXHAUSTED` API limit.

