# Plan — ClaimBand (Band of Agents Hackathon, Track 3)

## Goal
A cross-framework, multi-vendor **insurance claim adjudication** system where **4 agents
collaborate through Band** (the real coordination layer) to triage a claim and produce an
approve / deny / **escalate-to-human** decision. Band's room UI is the demo surface; a human
approves in-room. Submission: public repo + 3-min recording + slide deck + cover image + demo link.

## Resource reality (verified 2026-06-18)
- **Have:** Band Pro (hackathon promo `BANDHACK26`).
- **Gone:** AI/ML API credit (already claimed), Featherless (no free tier). **Partner prizes are off
  the table — we are NOT optimising for them.** Target = main prizes (1st/2nd/3rd).
- **Free, no card, usable now:** Google Gemini (Flash family, 1,500 req/day), Groq (Llama 3.3 70B /
  gpt-oss-120b, ~1,000 req/day, OpenAI-compatible). Mistral free (~1 RPM) = optional 3rd vendor.
- **Total project cost: $0.**

## Why this still wins (without partner prizes)
- **Application of Technology:** genuine handoff + shared context through Band, **3 frameworks, 2-3
  model vendors** — exactly the criterion Band is judged on. Free providers don't weaken this.
- **Originality:** avoids the official ProcureGuard / Codeband examples.
- **Business value:** claims triage is a real, expensive, regulated enterprise workflow.

## Agents, frameworks, vendors (all FREE — verified against SDK source)
| Agent | Role | Framework / adapter | FREE vendor / model |
|---|---|---|---|
| **Intake** | Normalise + validate claim, flag missing fields, hand off | `LangGraphAdapter` + `ChatOpenAI(base_url)` | **Groq** — llama-3.3-70b-versatile |
| **Coverage** | Check claim vs policy terms / limits / exclusions | `GeminiAdapter` (native google-genai) | **Google Gemini** — gemini-2.5-flash |
| **Fraud/Risk** | Anomaly + red-flag scoring → risk score + reasons | `LangGraphAdapter` + `ChatOpenAI(base_url)` | **Groq** — gpt-oss-120b (diff. model family) |
| **Adjudicator** | Synthesise peers' findings → approve / deny / **escalate** | `CrewAIAdapter` (litellm) | **Google Gemini** — gemini/gemini-2.5-flash |

- 3 distinct frameworks: **LangGraph + Gemini SDK + CrewAI**. 2 vendors (Groq + Google); add **Mistral**
  on Fraud as a 3rd vendor only if its 1-RPM limit proves reliable in Phase 0.
- Shared context = the claim JSON record passed and enriched through the Band room.
- Claims are **JSON fixtures** (no OCR/vision — deliberately cut to remove the biggest time sink).

## Confirmed technical facts (verified against SDK source at /tmp/thenvoi-sdk-python)
- `pip install "band-sdk[langgraph,gemini,crewai] @ git+https://github.com/thenvoi/thenvoi-sdk-python.git"`
- `from band import Agent`; `from band.adapters import LangGraphAdapter, GeminiAdapter, CrewAIAdapter`
- Connect: `Agent.create(adapter=..., agent_id=..., api_key=..., ws_url="wss://app.band.ai/api/v1/socket/websocket", rest_url="https://app.band.ai")` then `await agent.run()`.
- `GeminiAdapter(model="gemini-2.5-flash", prompt=...)` reads free AI Studio key from env.
- `CrewAIAdapter(model="gemini/...", role=, goal=, backstory=)` routes via litellm → free providers by env key.
- `LangGraphAdapter(llm=ChatOpenAI(base_url="https://api.groq.com/openai/v1", model=..., api_key=GROQ_KEY))`.

## CREDENTIAL GATES (user must provide — all FREE)
- [ ] Band Pro (`BANDHACK26`); create **4 agents** in band.ai dashboard → 4× `(agent_id, api_key)`
- [ ] Create one shared **room** in Band and add all 4 agents
- [ ] `GEMINI_API_KEY` — free at aistudio.google.com, no card
- [ ] `GROQ_API_KEY` — free at console.groq.com, no card
- [ ] (optional) `MISTRAL_API_KEY` — free, no card

---

## Build order — Tier 1 floor first (always shippable), then Tier 2 layer

### Phase 0 — Setup & verify (~45m)
- [ ] `python3.12 -m venv .venv`; activate; `pip install` band-sdk + extras + langchain-openai + python-dotenv
- [ ] Verify exact entrypoint (`Agent.create`) with a 1-agent hello-world connect to the Band room
- [ ] Smoke-test each free provider (Gemini, Groq) returns a completion before wiring agents
- [ ] `git init`, `.gitignore` (.env, .venv, agent_config.yaml), first commit + push to public GitHub repo
- [ ] `.env.example` + `agent_config.yaml.example`; real `.env` / `agent_config.yaml` (gitignored)

### Phase 1 — Tier 1 floor: 3 agents, end-to-end (~3-4h) → SUBMITTABLE
- [ ] `claims/` JSON fixtures (1 clean approve, 1 deny, 1 fraud-suspect/escalate)
- [ ] Prompts: `prompts/coverage.md`, `prompts/fraud.md`, `prompts/adjudicator.md` (behaviour + handoff protocol)
- [ ] Coverage (Gemini), Fraud (Groq), Adjudicator (CrewAI/Gemini) as runnable processes
- [ ] Run all 3 in the room; verify genuine handoff + shared context + human escalation
- [ ] **Checkpoint: this alone is a valid submission.** Commit + tag.

### Phase 2 — Tier 2 layer: 4th agent, full cross-framework (~2-3h)
- [ ] Add **Intake** agent (LangGraph + Groq Llama) that runs first and hands off the enriched claim
- [ ] Verify the 4-agent, 3-framework room collaborates end-to-end on all 3 fixtures
- [ ] (optional) move Fraud to Mistral for a 3rd vendor if reliable
- [ ] Commit + tag.

### Phase 3 — Submission assets (~2-3h)
- [ ] `README.md` (architecture diagram, agent table, run instructions, cross-framework story)
- [ ] 3-min screen recording of a live claim flowing through the Band room
- [ ] Slide deck outline (problem → architecture → Band-as-coordination-layer → demo → business value)
- [ ] Cover image; demo link = Band room (or tiny Vercel landing if time remains)

## Risks
- **Credential/dashboard gate** — agents can't run until the user creates them in band.ai. Blocks Phase 0 end.
- **SDK entrypoint drift** — workshop used `thenvoi`/`Agent.create`; current pkg is `band`. Phase 0 verifies the real call.
- **Free-tier rate limits** — Gemini 1,500 RPD / Groq 1,000 RPD are ample for dev + demo; Mistral 1 RPM is not, so Mistral stays optional. A 429 mid-demo → re-run; fixtures keep calls low.

## Out of scope (explicitly cut for time / cost)
OCR/PDF vision extraction, custom frontend dashboard (Tier 3 only), auth, persistence beyond fixtures,
any paid model API, partner-prize targeting.

---

# Phase 2 — Agent layer (Gemini's slice) — RESOLVED BAND API CONTRACT

Codex finished the pure-logic floor (schema, coverage, scoring, adjudication, 18 tests green,
3 fixtures verified APPROVE/DENY/ESCALATE). What remains is the Band/agent layer. The Band
messaging API below is **verified against the SDK source** — build to it, do not rediscover.

## Verified Band API (from `band.runtime.tools.AgentTools`)
- **Handoff:** `await tools.send_message(content: str, mentions=["@owner/agent"])`. **mentions are
  REQUIRED (≥1)**; handles are `@<owner-username>/<agent-name>`, e.g. `@nivishnick2k/coverage`.
  (Confirm the exact owner handle in the Band dashboard — agent cards show it; the Intake card read
  `@nivishnick2k/intake`.)
- **Discovery flourish:** `await tools.add_participant("@owner/fraud")` + `await tools.lookup_peers()`.
- These platform tools are **auto-injected into the LLM loop** → handoff is LLM-driven, so prompts
  must be strict ("always hand off, never stop early").
- Custom domain tool: both `GeminiAdapter(additional_tools=[(InputModel, fn)])` and
  `LangGraphAdapter(additional_tools=[...])` accept `additional_tools`; tuple form is
  `(PydanticInputModel, callable)` per the SDK weather example.

## Agent contract (uniform across all 4)
Each agent registers ONE domain tool that wraps the matching pure function. Signature:
`tool(claim_json: str) -> str` → parse to `ClaimRecord`, run the pure fn, set the agent's block,
return the updated claim JSON. The prompt then makes the LLM `send_message` that JSON (in a
```json fenced block) + a one-line human summary, mentioning the next agent.

| Agent | Tool wraps | Hands off to (mention) |
|---|---|---|
| Intake | `validate_claim` | `@owner/coverage` |
| Coverage | `compute_coverage` | `@owner/fraud` |
| Fraud | `score_risk` | `@owner/adjudicator` |
| Adjudicator | `adjudicate_claim` | the human (`@owner`) on ESCALATE; else posts final decision |

**Discovery flourish (Adjudicator):** if `fraud` block is missing OR `risk_score == 40` (the only
non-escalating ambiguous score, since scoring is 20/flag), call `lookup_peers` + `add_participant`
to recruit `@owner/fraud` and `send_message` requesting a re-score before deciding.

## Files for Gemini to create
- [ ] `claimband/band_io.py` — `extract_claim(msg_text)->dict` (parse last ```json block),
      `format_handoff(claim, summary)->str`, `OWNER` + next-agent handle map.
- [ ] `claimband/tools.py` — 4 domain-tool callables + their pydantic input models.
- [ ] `claimband/agents/{intake,coverage,fraud,adjudicator}.py` — `Agent.create(...)` per the
      adapter recipes in `AGENTS.md`, `additional_tools=[(Model, fn)]`, prompt from prompts/.
- [ ] `claimband/prompts/{intake,coverage,fraud,adjudicator}.md` — strict role + handoff protocol.
- [ ] `seed.py` — post a fixture into the room mentioning `@owner/intake`. (Fallback: human pastes
      the claim JSON into the Band room UI mentioning @intake — no code needed.)

## Build order
- [ ] **Phase 0 (smoke):** run ONE agent; confirm it connects to the room and replies. Confirm the
      owner handle + that a single shared chat/room contains all 4 agents **and the user**.
- [ ] **Phase 1b (3-agent floor):** build Coverage→Fraud→Adjudicator + band_io + tools + prompts.
      Seed at Coverage with `clean.json` (pre-fill intake block). Verify APPROVE in the room.
- [ ] **Phase 2 (full relay):** add Intake at the front; seed at Intake. Run all 3 fixtures →
      APPROVE / DENY / ESCALATE visible in the room.
- [ ] **Phase 2b:** wire the discovery flourish.
- [ ] **Phase 3:** README with architecture + run steps.

## Risks / gates (resolve before/within Phase 0)
- **Shared room must exist** with all 4 agents + the user as participants, else mentions fail.
  (Open question — confirm a Band chat/room was created.)
- **JSON fidelity:** LLM must echo the tool's JSON verbatim in a fenced block. Mitigate with strict
  prompts + `extract_claim` taking the LAST ```json block. If unreliable, fall back to keying a
  small in-process store by `claim_id`.
- **Per-adapter tool wiring** differs slightly (Gemini tuple vs LangGraph vs CrewAI) — verify each
  in Phase 0 against the installed package.
- Free-tier 429 (low volume, fine); WebSocket reconnect (SDK handles; agents idempotent on re-post).

## Verification (the 6 acceptance criteria live in `docs/prd.md` §Acceptance)
Run the 3 fixtures live in the room; confirm outcomes, cross-framework/vendor startup logs, and
≥1 genuine discovery event.

---
*Phase 0/1 (Codex pure-logic slice) COMPLETE. Above is the remaining Gemini slice.*

# Phase 3 — Fix & Dry Run (the critical 20% that gets the demo to 80%)

Verified 2026-06-18: agents compile + import, pure logic green, BUT the live relay is not wired.
Fix in this exact priority order, then dry-run. Confirm two facts first: **OWNER handle**
(dashboard shows `@nivishnick2k/<agent>`) and the **shared room/chat id** (must contain all 4 agents
+ the user).

## CRITICAL (without these the relay does not run)
- [ ] **F1 — Real handoff.** In every prompt, replace "put `@coverage` in the text" with: call the
      `send_message` platform tool with `content=<full claim JSON + 1-line summary>` and
      `mentions=["@nivishnick2k/<next>"]` (owner-qualified). Escalation mentions the human
      `@nivishnick2k`. The relay is mention-triggered — wrong/absent mentions = dead relay.
- [ ] **F2 — Tools merge the FULL record.** Change all four tool wrappers to take the full claim
      JSON, set their block on the `ClaimRecord`, and return the **full** updated claim JSON (not just
      the block). The LLM then forwards it verbatim instead of merging — removes the biggest failure.
- [ ] **F3 — Wire missing tools.** Add `additional_tools` to `intake.py` (`validate_claim`) and
      `adjudicator.py` (`adjudicate_claim`, CrewAI supports the tuple form). All 4 agents now call
      deterministic logic.
- [ ] **F4 — Fix `seed.py`.** Post the seed via the SDK's real message API
      (`create_agent_chat_message(chat_id, ChatMessageRequest(content, mentions=[intake]))`), with a
      structured mention of `@nivishnick2k/intake` and the room id as an arg. Fallback: manual paste
      of the claim JSON into the room UI mentioning intake.

## F0 — CREATE THE DEMO ROOM (the real blocker; keys are valid, agents are in no chat)
- [ ] Build `setup_room.py` (planner verified the exact API):
  ```python
  # as intake: create chat, add the other 3 agents + the human owner, print ROOM_ID
  import asyncio, yaml, os; from dotenv import load_dotenv; load_dotenv()
  import thenvoi_rest as tr
  from thenvoi_rest import ChatRoomRequest, ParticipantRequest
  cfg = yaml.safe_load(open("agent_config.yaml"))
  HUMAN = "5f4ed8cf-e454-4854-a1cc-d57b1c296d9c"  # owner_uuid from get_agent_me()
  async def go():
      c = tr.AsyncRestClient(api_key=cfg["intake"]["api_key"], base_url=os.environ["BAND_REST_URL"])
      room = await c.agent_api_chats.create_agent_chat(chat=ChatRoomRequest(task_id=None))
      rid = room.data.id
      for r in ["coverage","fraud","adjudicator"]:
          await c.agent_api_participants.add_agent_chat_participant(
              chat_id=rid, participant=ParticipantRequest(participant_id=cfg[r]["agent_id"], role="member"))
      await c.agent_api_participants.add_agent_chat_participant(
          chat_id=rid, participant=ParticipantRequest(participant_id=HUMAN, role="admin"))
      print("BAND_ROOM_ID=", rid)
  asyncio.run(go())
  ```
- [ ] Save the printed id as `BAND_ROOM_ID` in `.env`; `seed.py` reads it (no CLI arg needed).
- [ ] Verify with `list_agent_chat_participants(chat_id)` that all 5 are present.

## DRY RUN (the user explicitly asked for this)
- [ ] **DR1 — Offline:** run the 3 fixtures through the pure pipeline (already green) — keep as a
      sanity gate.
- [ ] **DR2 — Connectivity:** tiny script that (a) pings Groq and Gemini for a 1-token completion,
      (b) starts each agent and confirms it logs a successful WebSocket connect + room join, (c) sends
      one structured test message to the room and confirms it lands. Report PASS/FAIL each.
- [ ] **DR3 — Live relay:** seed `clean.json`, watch Intake→Coverage→Fraud→Adjudicator→decision in
      the room; repeat for `deny.json` and `fraud.json`. Capture room excerpts as evidence.

## Acceptance (same 6 criteria, docs/prd.md §Acceptance) — must show evidence, then fix failures.

## NICE-TO-HAVE (the other 80% of effort, do only if time remains)
- [ ] band_io.py refactor (shared extract/format/handles), discovery-flourish hardening, WebSocket
      reconnect, cross-framework startup banners for criterion 4, README polish.
- [ ] Slide deck + 3-min recording script (planner will produce separately).

## Known code defects to fix in passing
- `schema.py:88` — `Optional[any]` should be `Optional[Any]` (typing import).
- Tool error path returns a string `"Error: ..."` — fine for demo, but the LLM may forward it as a
  claim; have the prompt treat any `Error:` payload as a stop-and-report, not a handoff.

---

# PHASE 5 — DR3 CLOSURE + SUBMISSION (drafted 2026-06-18, awaiting approval)

## Ground truth (verified, not assumed)
- The live room (`dump_room_trail.py`) holds **3 messages: all seed claims, zero agent replies**.
  The relay has **never completed a single hop live**, contradicting learnings.md's "what fixed it".
- Most probable hop-1 cause: agents were running against a **stale `BAND_ROOM_ID`** (launched before
  `create_new_room.py` rewrote `.env`). `load_dotenv(override=True)` fixes future launches only.
- Per-relay LLM load today: **2 Gemini flash-lite calls** (Coverage + Adjudicator) + 2 Groq calls.
  Gemini free tier (~20 req/day) is the hard ceiling; retries exhaust it instantly.

## Decision to ratify (see proposed D12)
- **Move Adjudicator off Gemini → Groq `gpt-oss-120b`** (still CrewAI/LiteLLM). Keeps 3 frameworks +
  2 vendors (prize narrative intact); halves Gemini load per relay (2 → 1). Coverage stays GeminiAdapter.

## Step 1 — Orchestration hygiene (the actual hop-1 fix)
- [ ] Add a one-shot `run_all.py` (or shell script) that launches all 4 agents **in this session's
      current room**, each printing: connect OK, room id joined, "received message", every tool call
      (name + arg length), every `send_message` (target mention). One log per agent.
- [ ] Pre-flight assert: each agent prints the SAME `BAND_ROOM_ID` it joined; abort if mismatch.
- [ ] `check_participants.py` confirms all 5 participants in that exact room before seeding.

## Step 2 — Quota discipline
- [ ] Apply D12 (Adjudicator → Groq). Confirm 1 Gemini call/relay.
- [ ] Add bounded retry w/ backoff on `429` in each agent (catch, sleep, retry once, else post a
      human-readable "rate-limited, retrying" note and stop — never crash the process).
- [ ] Seed fixtures **one at a time** with ≥30s spacing; never concurrent.

## Step 3 — DR3 live, single claim first
- [ ] Launch via Step 1. Seed ONLY `clean.json`. Watch hop-by-hop in logs + room:
      Intake → Coverage → Fraud → Adjudicator → **APPROVE**. If a hop dies, the logs pinpoint it;
      fix the exact failing link (do not re-guess — read the printed tool arg / error).
- [ ] Once `clean.json` produces APPROVE end-to-end and the trail is captured, repeat `deny.json`
      (DENY) and `fraud.json` (ESCALATE), spaced out.
- [ ] Capture the full room trail per fixture via `dump_room_trail.py` → save to
      `docs/evidence/dr3-<fixture>.txt` as proof for the 6 acceptance criteria.

## Step 4 — Acceptance + planner cold-verify
- [ ] Map captured trails to the 6 criteria in `docs/prd.md §Acceptance` (esp. criterion 5 = a real
      discovery/handoff event, not a checkmark). Planner reads the actual messages, not a report.

## Step 5 — Submission assets (full set, per D7)
- [ ] Slide deck (pptx skill): problem, architecture diagram, cross-framework/vendor story, live demo
      stills, decision rules, "regulated/high-stakes" framing.
- [ ] 3-min recording script: seed → watch 4 agents relay → human-in-loop on ESCALATE → decision.
- [ ] Cover image. README final polish + run instructions verified from clean clone.

## Fallback if quota fully blocks a clean live capture before deadline
- [ ] Record the BEST available partial live relay + show the offline pipeline (18 tests green) as the
      deterministic logic proof. Narrate the quota constraint honestly in the deck. The architecture
      and Band integration are the scored story; a quota wall is a known free-tier limitation, not a
      design flaw. (Decide only if Step 3 cannot land within the time box.)

## Out of scope (do not start)
- band_io.py refactor, WebSocket reconnect hardening, multimodal/OCR, custom dashboard.
