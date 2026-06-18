# Status

## Current state
**Phase 1, 2, and 3 complete (TDD green and Agents built).**
- Codex slice implemented: `claimband/schema.py`, `claimband/coverage.py`, `claimband/scoring.py`, `claimband/adjudication.py`.
- Gemini slice implemented: `claimband/agents/` scripts, `claimband/prompts/` instructions, and `seed.py`.
- **(HOTFIX)** Fixed F1-F5 defects: Switched prompts to use `send_message` with mentions, updated tools to parse and merge full records, wired missing tools, and rewrote `seed.py` to use SDK REST API.
- Automated test coverage built: 18 passing tests under `tests/` (`test_schema.py`, `test_coverage.py`, `test_scoring.py`, `test_integration.py`).
- 3 JSON fixtures added: `claims/clean.json`, `claims/deny.json`, `claims/fraud.json`.
- `README.md` added with architecture diagrams and run instructions.
- Project formatting verified clean via `black`.
- **BLOCKER**: DR3 Live Relay failed on all fixtures (`clean.json`, `deny.json`, `fraud.json`). Intake Agent (swapped to `openai/gpt-oss-120b`) failed with `Tool call validation failed: missing properties: 'claim_record_json'`. Coverage Agent (Gemini) misbehaved, outputting: "The `coverage` tool is consistently returning an error, stating it expects a string, bytes, or bytearray for the `claim_record_json` argument but receives a 'CoverageInput' object." before hitting a `429 RESOURCE_EXHAUSTED` API limit.

## Build handoff — for Gemini + Codex
- Read order: `AGENTS.md` → `docs/prd.md` → `docs/decisions.md` → `docs/plan.md`.
- Line: auto insurance. Orchestration: deterministic relay + conditional Band discovery.
- Split: Codex = schema/coverage/scoring/tests (TDD); Gemini = agents/prompts/fixtures/seed.
- Build order: Phase 0 connect smoke test → Phase 1 3-agent floor → Phase 2 add Intake → Phase 3 README.

## Decisions locked
- Project: **ClaimBand** — insurance claim adjudication (Track 3, regulated/high-stakes).
- Scope: **Tier 2** — build Tier 1 (3 Anthropic agents) end-to-end first, then layer the
  4th agent + multi-vendor (AI/ML API + Featherless + Anthropic) for both partner prizes.
- SDK: `band-sdk` (formerly `thenvoi`), `from band import Agent`, WebSocket rooms.
- Discovery: Hardcoded for primary flow, dynamic `BandClient` search on ESCALATE edge case.
- Testing: Pure functions for logic (TDD). Agents just wrap them.

## CORRECTED DIAGNOSIS (planner, 2026-06-18) — Gemini's blocker was wrong
- **Keys are VALID.** `agent_api_identity.get_agent_me()` via the SDK succeeds for the keys in
  `agent_config.yaml`. intake → handle `nivishnick2k/intake`, owner_uuid `5f4ed8cf-e454-4854-a1cc-d57b1c296d9c`.
  Gemini's HTTP 404/401 came from a fabricated REST path (`/api/v1/agents/me`), not bad keys.
- **REAL blocker: no room.** `agent_api_chats.list_agent_chats()` returns `[]` — the agents are in
  no chat, so there is nothing to relay in. seed.py has no room to post to.
- **Unblock is programmatic (API verified):** `create_agent_chat(ChatRoomRequest(task_id=None))` then
  `add_agent_chat_participant(chat_id, ParticipantRequest(participant_id=<id>, role=...))` for the 3
  other agents (by agent_id) + the human (by owner_uuid). Then `create_agent_chat_message(chat_id,
  ChatMessageRequest(content, mentions=[intake]))` to seed. No manual UI room needed.

## ROOM CREATED (planner, 2026-06-18) — blocker cleared
- `BAND_ROOM_ID=100b711f-2db9-4d7a-bb4f-fe71d09914f8` (saved in `.env`). 5 participants confirmed:
  nivishnick2k (human/admin) + intake/coverage/fraud/adjudicator (members).

## DR3 status (2026-06-18): DR1+DR2 PASS, DR3 crashes on hop 1 (Intake)
- Root cause (planner-verified, see D10): Intake's `llama-3.3-70b-versatile` mis-emits a tool call
  against the live SDK toolset → Groq `failed_generation`. NOT a platform incompatibility.
- **One-line fix:** in `claimband/agents/intake.py` swap model `llama-3.3-70b-versatile` →
  `openai/gpt-oss-120b` (the model Fraud already uses reliably).

## DR3 v2 failures fixed by planner (2026-06-18, see D11)
- Coverage + Adjudicator tuple-tool signatures fixed (`def fn(args: XInput)`); verified offline via the
  SDK invocation path. temperature=0 set on Intake + Fraud. black + 18 tests green.

## Learnings and Resolutions
- A full breakdown of the compounding 429 rate limit errors (the "loop"), prompt tightening, environment fixes, and unresolvable API tier constraints has been documented in `docs/learnings.md`.

## GROUND TRUTH (planner-verified 2026-06-18 via dump_room_trail.py)
- Live room holds **3 messages: all seed claims, ZERO agent replies.** The relay has **never
  completed a single hop live.** learnings.md's "what fixed it" is unproven against the room.
- Probable hop-1 cause: agents launched against a **stale BAND_ROOM_ID** (pre-`create_new_room.py`).
- Per-relay LLM load was 2 Gemini calls; D12 cuts it to 1 (Adjudicator → Groq gpt-oss-120b).

## Next steps (Gemini — PHASE 5, see docs/gemini-phase5-kickoff.md)
1. **Orchestration hygiene:** per-message logging in all 4 agents + `run_all.py` that asserts all 4
   join the SAME current room before any seed. This is the real hop-1 fix.
2. **Apply D12:** Adjudicator → `groq/openai/gpt-oss-120b` (CrewAI/LiteLLM). Add 429 backoff
   (retry once, then post a note and stay alive — no crash, no infinite loop).
3. **DR3 live, clean.json FIRST**, hop-by-hop; then deny/fraud spaced ≥30s. Capture trails to
   `docs/evidence/dr3-*.txt`. Paste raw errors to planner — no re-guessing.
4. Map trails to the 6 acceptance criteria. **Planner cold-verifies the actual messages**, not a report.
5. Then submission assets (deck, 3-min script, cover image) — planner-led.
