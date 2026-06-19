# Gemini — Phase 6 (finish the relay + submission)

The planner (Claude) took over bring-up while you were stalled, built and **live-verified** the
deterministic relay, then handed execution back to you. Read in order: `docs/decisions.md` (esp.
**D13, D14**) → `docs/plan.md` (PHASE 6) → this file. Do not re-architect — build on what works.

## What is already DONE and verified (do not redo)
- **Deterministic relay** (`claimband/relay.py`): each agent reads the claim from the inbound Band
  message (shared room context) via a fenced-JSON parser, runs the tested pure function, and hands off
  with an @mention. The LLM is NOT on the data path (it only writes a one-line note). This fixed the
  `missing properties: 'claim_record_json'` failure for good.
- **Agents** (`claimband/agents/*.py`): each builds its framework adapter (LangGraph/Gemini/CrewAI),
  overrides `on_event` with the relay handler, and runs under `relay.serve()` (reconnect supervisor).
- **Notes** (`claimband/notes.py`): Groq notes use `llama-3.3-70b-versatile`; Gemini note is best-effort
  (currently 429'd by the 20/day free cap → template fallback; that's fine, by design).
- **Tests**: `tests/test_relay.py` (5) + existing 18 = **23 pass**. Keep them green; keep `black` clean.
- **Live PASS**: `clean.json → APPROVE $3,700`, `deny.json → DENY`. Full 4-agent relays, verdict
  broadcast to the band.

## Key SDK/operational facts (verified — don't re-discover)
- Adapters implement `on_event(inp: AgentInput)`. `inp.msg.content`, `inp.tools.send_message(content,
  mentions: list[str])`. send_message **requires ≥1 mention**; handles like `nivishnick2k/coverage`.
- The preprocessor does self-message filtering but **NO mention gating** → the relay gates itself.
- `list_agent_messages` is **mention-scoped** (only messages the agent sent-to/was-mentioned-in). The
  final verdict is visible in trails ONLY because it is broadcast to all agents (D14.3).
- Background launches: run `run_all.py` as a **directly-tracked** process. If you background it with
  `&` inside a wrapper shell, the harness reaps the orphan after ~30s and the agents die silently.
- Current `BAND_ROOM_ID=34cd5ad4-14be-47b1-bb3e-0fd2ee2d6fdb`. Orphan rooms `38dc6e6c…`, `2e7e1b59…`.

## Your steps (report after EACH; do not batch silently)
1. **S1 — ESCALATE**: launch `run_all.py`, confirm 4× connect + PRE-FLIGHT OK, then
   `python seed.py fraud.json`. Confirm the relay ends in **ESCALATE** mentioning the human
   `nivishnick2k` (acceptance criterion 5). Paste the room trail.
2. **S2 — Evidence**: save merged room trails to `docs/evidence/dr3-{clean,deny,fraud}.txt`; map to the
   6 criteria in `docs/prd.md §Acceptance`.
3. **S3 — Room hygiene**: pick one demo room, delete the orphans (CONFIRM with the user first — it's
   destructive). Fix/delete the buggy `clear_room.py`.
4. **S4 — Submission assets**: slide deck, 3-min recording script, cover image, README polish.
5. Update `docs/status.md` + `docs/changelog.md`. Keep black clean and 23 tests green.

## HARD RULES (this is why the planner had to take over)
- **Plan-first.** Any new architectural decision → STOP, write a plan block in `docs/plan.md`, get the
  user's approval BEFORE coding. Do not free-wheel a cascade of fixes.
- Do NOT guess the SDK API. If unsure, read the installed source under
  `.venv/lib/python3.12/site-packages/band/` (that's how the real interface was found).
- Touch only `claimband/*`, `run_all.py`, `docs/*`, housekeeping scripts. Secrets stay gitignored.
- Report raw errors; don't re-diagnose from vibes.

## Launch
```bash
cd /Users/nivish/development/Band-of-agents && gemini
```
