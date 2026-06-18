# Gemini — Phase 5 build (DR3 closure + submission)

You are the builder. Read `AGENTS.md` → `docs/prd.md` → `docs/decisions.md` (esp. **D11, D12**) →
`docs/plan.md` (PHASE 5) before touching code. The planner has verified the ground truth below — do
not re-diagnose from learnings.md, which overstates progress.

## GROUND TRUTH (verified by planner via `dump_room_trail.py`)
- The live room (`BAND_ROOM_ID` in `.env`) holds **3 messages: all seed claims, ZERO agent replies.**
  The relay has **never completed a single hop live.** learnings.md's "what fixed it" is unproven.
- Most probable hop-1 cause: agents were launched against a **stale `BAND_ROOM_ID`** (before
  `create_new_room.py` rewrote `.env`). The seed lands in the current room; agents sit elsewhere.
- The tuple-tool signature bug (Coverage/Adjudicator) is ALREADY fixed (D11). Don't touch those tool
  signatures — they read `args.claim_record_json` and that is correct.

## WHAT TO BUILD — do these in order. Report after each step. Do NOT batch silently.

### Step 1 — Orchestration hygiene (this is the real hop-1 fix)
1. **Per-message logging in all 4 agents.** Each agent must log, with its name as prefix:
   - on startup: `connect OK` + the exact `BAND_ROOM_ID` it will operate in;
   - every inbound message it receives (sender + first 80 chars);
   - every tool call it makes (tool name + `len(claim_record_json)` of the arg it passed);
   - every `send_message` it emits (the target mention handle).
   Use the existing `logging` setup (see `coverage.py`). If the SDK exposes hooks/callbacks for
   received messages and tool calls, use them; otherwise log inside the tool callables + add a thin
   wrapper. Keep it minimal — this is instrumentation, not a refactor.
2. **`run_all.py`** — one script that launches all 4 agents concurrently (asyncio tasks /
   subprocess), each loading `.env` with `override=True`, and **asserts all 4 print the SAME
   `BAND_ROOM_ID`**; abort loudly if any differ or if `BAND_ROOM_ID` is unset.
3. Confirm via `check_participants.py` that all 5 participants are in **that exact room** before any
   seed. If not, fix participants (don't create a new room unless the planner authorizes it).

### Step 2 — Apply D12 + quota discipline
4. **Adjudicator → Groq.** In `claimband/agents/adjudicator.py`, change the CrewAIAdapter model from
   `gemini/gemini-2.5-flash-lite` → `groq/openai/gpt-oss-120b` (LiteLLM reads `GROQ_API_KEY` from env;
   it's already in `.env`). Leave Coverage on `gemini-2.5-flash-lite` (GeminiAdapter). This keeps
   3 frameworks + 2 vendors and cuts Gemini load to **1 call per relay**.
5. **429 resilience.** In each agent, catch rate-limit / quota errors, sleep with a short backoff,
   retry **once**, and if it still fails post a plain in-room note ("rate-limited, retrying later")
   and keep the process alive — never crash. Do not add infinite retry loops (that caused the storm).
6. Seeding is **one fixture at a time, ≥30s apart.** Never seed concurrently.

### Step 3 — DR3 live, single claim FIRST
7. `python run_all.py` (all 4 agents up, same room confirmed). Then `python seed.py clean.json`.
   Watch the logs + room hop-by-hop: **Intake → Coverage → Fraud → Adjudicator → APPROVE.**
8. If a hop dies: the logs now show exactly where (which agent, what tool arg length, what error).
   Fix that exact link. **Paste the raw error to the planner — do not guess the root cause.**
9. Once `clean.json` produces APPROVE end-to-end, repeat `deny.json` (expect **DENY**) and
   `fraud.json` (expect **ESCALATE**), spaced ≥30s.
10. Capture each full trail: `python dump_room_trail.py > docs/evidence/dr3-clean.txt` (and
    `-deny`, `-fraud`). Create `docs/evidence/` if missing.

## REPORT BACK (to the planner, who will cold-verify the actual messages)
- Per fixture: final decision + the saved trail path.
- The 6 acceptance criteria (`docs/prd.md §Acceptance`), each PASS/FAIL with the message that proves
  it — especially **criterion 5** (a real discovery/handoff event, not just "it relayed").
- Update `docs/status.md` + `docs/changelog.md`. Keep `black` clean; do not break the 18 tests
  (`PYTHONPATH=. ./.venv/bin/python -m pytest`).

## HARD CONSTRAINTS
- Touch only: the 4 `claimband/agents/*.py`, `run_all.py` (new), prompts only if a hop proves a prompt
  bug, `docs/*`. Do NOT refactor `band_io`, add OCR, or build a dashboard — out of scope (plan PHASE 5).
- Do NOT create new Band rooms or delete messages without planner authorization.
- If quota fully blocks a clean 3-fixture capture, stop and report — there is a documented fallback
  in the plan (best partial live relay + offline-pipeline proof). Do not improvise around it.

## Launch
```bash
cd /Users/nivish/development/Band-of-agents && gemini
```
