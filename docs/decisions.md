# Decisions

## D1 — Track 3 / ClaimBand over Codeband-style (Track 2)
**Chosen:** Insurance claim adjudication.
**Alternatives:** Track 2 software pipeline (Codeband-style), Track 1 onboarding, Track 3 contract review.
**Reasoning:** Track 2 is crowded and mirrors the official reference repo (low originality). ClaimBand
scores higher on originality + business value, is easy to demo with sample claims, and naturally
justifies multiple model vendors. Contract review rejected: legal correctness hard to demo in 24h.

## D2 — Tier 2 scope, Tier 1 built first
**Chosen:** Tier 2 (4 agents, multi-vendor) with Tier 1 (3 agents, single vendor) as the safety floor.
**Alternatives:** Tier 1 only (zero risk, no partner prizes); Tier 3 (multimodal + dashboard, high risk).
**Reasoning:** <24h left and "must finish what we start." Building the floor first guarantees a valid
submission at every checkpoint; Tier 2 is additive and stops at a clean boundary if time runs out.

## D3 — JSON claim fixtures, no OCR/vision
**Reasoning:** Document extraction is the biggest time sink and adds nothing to the collaboration
story judges score. Fixtures let us focus effort on genuine Band handoff + shared context.

## D4 — Band room UI as the demo surface
**Reasoning:** Band's own room renders the multi-agent conversation. Using it removes nearly all
frontend work; a custom dashboard is Tier 3 only.

## D5 — Free model providers; drop partner-prize targeting
**Context:** AI/ML API credit already claimed, Featherless has no permanent free tier. Both partner
prizes are therefore unreachable.
**Chosen:** Power agents with **Google Gemini (free)** + **Groq (free)**, optionally **Mistral (free)**.
3 frameworks (LangGraph, Gemini SDK, CrewAI), 2-3 vendors, $0 cost.
**Reasoning:** The cross-framework / multi-vendor story that the *main* prizes are judged on
(Application of Technology, Originality) is fully achievable on free tiers. Free providers do not
weaken that narrative. Rate limits (Gemini 1,500/day, Groq 1,000/day) are ample for fixture-driven
demos; Mistral's 1-RPM cap keeps it optional only.

## D6 — Remote agents, not Internal agents
**Context:** Band's dashboard offers "Create Internal Agent" (Band-hosted, model+provider key set in
UI) and "Connect Remote Agent" (agent brings its own reasoning loop, connected via SDK).
**Chosen:** **Connect Remote Agent** for all 4 agents. Band mints identity only (agent_id + api_key);
model keys (Gemini/Groq) live in our project `.env`.
**Reasoning:** Remote agents ARE the cross-framework approach — they let each agent run a different
SDK (LangGraph, Gemini, CrewAI), which is the differentiating story for this hackathon. Internal
agents would all run Band's single runtime and forfeit that. **Personal Registry Access must stay ON**
per agent so agents can discover/recruit each other in the room.

## D7 — Full rigor + full submission assets (user choice 2026-06-18)
**Chosen:** PRD + agent-prompt design + formal plan + **TDD** + verification/review, plus README,
slide deck, and 3-min recording script. Skill pipeline: `prp-prd` → `multi-agent-prompt-builder`
→ `prp-plan`/`writing-plans` → `test-driven-development` (build) → `verification-before-completion`
+ `code-review` → `pptx` (deck).
**Trade-off accepted:** ~3h more than the lean path, tight against the 8:30 PM IST 19 Jun deadline.
**Safeguard:** a 3-agent floor must be RUNNING in the Band room before the heavy TDD pass, so there
is always a working demo. TDD targets pure logic (schema, scoring, parsing); WebSocket glue gets
integration smoke tests only.
**Note:** gstack is NOT installed locally (`~/.claude/skills/` has only impeccable, learned); the
named skills are the actually-available ones via the Skill tool.

## D8 — Claude plans only; Gemini + Codex build (user choice 2026-06-18)
**Chosen:** The planner (Claude) produces specs/plans/handoffs only and does NOT write app code.
The build is executed by **Gemini CLI** and **Codex** reading `AGENTS.md` (canonical) and `GEMINI.md`.
**Spec produced via gstack `/spec`:** auto-insurance line, deterministic relay + one conditional
Band peer-discovery event. Full spec in `docs/prd.md`.
**Build split:** Codex → `schema.py`/`coverage.py`/`scoring.py`/`tests` (TDD); Gemini → `agents/*`,
`prompts/*`, fixtures, `seed.py`. Coordinate via `docs/status.md`.
**Note:** real credentials live in gitignored `.env` + `agent_config.yaml` so builders run immediately.

## D9 — Build the agent layer all-at-once via Gemini sub-agents; hackathon-grade (2026-06-18)
**Chosen:** Gemini dispatches parallel sub-agents to build the whole Band/agent layer in one pass,
then a verifier sub-agent runs the live demo and checks the 6 acceptance criteria. No phase-by-phase
gating. Deliberately NOT optimising for scale — judges reward idea + execution, not large-scale impl.
**Collision guard:** `band_io.py` + `tools.py` (the shared handoff contract) are built and frozen
FIRST; the 4 agent entrypoints are built in parallel against that frozen contract.
**Rigor note:** TDD already covers the pure logic (Codex, 18 tests). The agent layer gets live
integration verification, not exhaustive unit tests — appropriate for a WebSocket/LLM relay.

## D10 — DR3 crash root cause: llama-3.3-70b tool-calling, not a platform bug (2026-06-18)
**Symptom:** Intake agent crashes live with Groq `openai.APIError: Failed to call a function … see
'failed_generation'`. Gemini blamed "Groq/LangGraph incompatibility."
**Planner forensics (ruled out):** isolated llama tool calls work (incl. big JSON args + 8 tools, 5/5);
LangGraph correctly expects LangChain `@tool` objects (Intake wiring is fine); default AdapterFeatures
inject no extra tools. So none of those are the cause.
**Actual cause:** only Intake runs `llama-3.3-70b-versatile` (the weakest tool-caller); it mis-emits a
tool call against the live SDK toolset (the real `send_message` has a union-typed `mentions` schema →
`anyOf`), which Groq rejects as a malformed function call. Fraud already uses `openai/gpt-oss-120b`
and never got to run.
**Fix:** swap Intake's model `llama-3.3-70b-versatile` → `openai/gpt-oss-120b` (one line in
`claimband/agents/intake.py`). Preserves cross-framework (LangGraph) + cross-vendor (Groq+Google).
Add `failed_generation` capture + per-turn error handling as a safety net.

## D11 — Tuple-tool callables must take the InputModel instance (planner-fixed, 2026-06-18)
**Symptom (DR3 v2):** Coverage agent errored "expects a string … but receives a 'CoverageInput'
object"; Adjudicator same shape; then Gemini hit 429 from the error-retry storm.
**Cause:** the SDK's `execute_custom_tool` calls `func(validated_model_instance)` for tuple tools
`(InputModel, fn)` (confirmed vs the canonical `async def get_weather(args: WeatherInput)`). Gemini
wrote `def run_compute_coverage(claim_record_json: str)` — so it received the model object, not the
string. Applies to the GEMINI + CREWAI adapters (tuple form). LangGraph `@tool` tools (Intake, Fraud)
take unpacked kwargs and were already correct.
**Fix (applied by planner):** `coverage.py` + `adjudicator.py` tool signatures → `def fn(args: XInput)`
using `args.claim_record_json`. Set `temperature=0` on the two LangGraph/Groq agents for tool-call
determinism. Verified offline via the SDK invocation path; black + 18 tests green.
**Remaining for Gemini:** Intake "missing properties" = gpt-oss omitting the big JSON arg → tighten
prompt to force verbatim copy; mitigate Gemini free-tier 429 (spread load / gemini-2.5-flash-lite);
re-run DR3.

## D12 — Adjudicator moves off Gemini → Groq gpt-oss-120b (user-ratified, 2026-06-18)
**Context (ground truth):** the live room shows 3 messages — all seed claims, ZERO agent replies.
The relay has never completed a single hop despite learnings.md's "fixed it" claims. Two blockers:
(1) probable stale `BAND_ROOM_ID` at launch (hop-1 never fired); (2) per-relay LLM load was **2 Gemini
flash-lite calls** (Coverage + Adjudicator) against a ~20 req/day free cap — retries exhaust it.
**Chosen:** Adjudicator switches from `gemini/gemini-2.5-flash-lite` → Groq `openai/gpt-oss-120b`
(still CrewAIAdapter via LiteLLM, model string `groq/openai/gpt-oss-120b`, GROQ_API_KEY in env).
Coverage stays on GeminiAdapter as the genuine Gemini showcase.
**Alternatives:** keep both on Gemini (rejected: doubles the scarcest quota); move Coverage too
(rejected: would drop the Gemini vendor entirely, weakening the multi-vendor prize story).
**Reasoning:** preserves the scored narrative — **3 frameworks** (LangGraph, Gemini SDK, CrewAI) and
**2 vendors** (Groq + Gemini) — while cutting Gemini load per relay 2 → 1, roughly doubling daily
relay headroom. The cross-framework story does not require every agent on a different vendor.

## D13 — Deterministic relay over Band shared context; LLM as reasoning narrator (user-ratified, 2026-06-19)
**Context:** the pure-LLM relay never completed a single hop across many attempts. Confirmed root cause
(Gemini's own log): `Tool call validation failed: missing properties: 'claim_record_json'`. The design
forced each free-tier model to copy the entire claim JSON into a tool argument AND again into the
handoff message at all 4 hops; `gpt-oss-120b` drops the large argument. Prompt-tightening did not and
will not reliably fix this on small models. (Also found: `fraud.py` was syntactically corrupted and
`logger_wrapper.py` wrapped non-existent SDK methods — symptoms of the builder guessing the API.)
**SDK facts verified in source:** adapters implement `on_event(inp: AgentInput)` (not `on_message`);
`inp.tools.send_message(content, mentions: list[str])` resolves handles against room participants and
**requires ≥1 mention**; `DefaultPreprocessor` does **self-message filtering but NO mention-gating**,
and loads history **only on session bootstrap** (later events arrive with empty history). Live room
participants/handles captured: human `nivishnick2k`, agents `nivishnick2k/{intake,coverage,fraud,adjudicator}`.
**Chosen:** a deterministic relay engine (`claimband/relay.py`). Each agent keeps its framework adapter
(LangGraph/Gemini/CrewAI — transport + identity), but its `on_event` is overridden with a handler that:
(1) gates on whether THIS agent is mentioned in the inbound message (enforces relay order regardless of
delivery breadth); (2) extracts the latest claim record deterministically from the message content via a
fenced-JSON parser (no LLM copying); (3) runs the tested pure function; (4) optionally calls the agent's
own vendor LLM for a one-line reasoning note (best-effort, templated fallback on error/429); (5) posts
the updated full record + the note, mentioning the next agent — adjudicator mentions the human on ESCALATE.
**Alternatives:** keep fighting the pure-LLM relay (rejected: structurally unreliable on free models,
0/N success, deadline today); a fully custom adapter with no framework (rejected: guts the cross-framework
story). **Reasoning:** guarantees a working, quota-light end-to-end demo today; showcases Band's shared
room context (its actual value prop) rather than fragile point-to-point JSON shuttling; preserves the
3-framework / 2-vendor narrative because the LLM still reasons per hop and each agent is built on a
distinct framework adapter. **Trade-off accepted:** the data path is deterministic, not LLM-improvised —
correct for a regulated/high-stakes domain where deterministic decisioning is a feature, not a weakness.

## D14 — Relay hardening decisions made during live bring-up (planner, 2026-06-19)
**Process note:** these four were decided reactively while debugging the live relay, NOT pre-planned.
Recording them after the fact (the lapse is logged in lessons.md). All are in the code and live-verified
for `clean.json → APPROVE` and `deny.json → DENY`.
1. **Supervisor reconnect (`relay.serve`)** — the platform issues a *terminal* WS close (idle/replaced)
   after which the SDK disables auto-reconnect and `agent.run()` returns. `serve()` rebuilds a fresh
   agent and reconnects with a 3s backoff so a drop can't end the agent. Alternative (patch SDK
   reconnect internals) rejected as a deadline rabbit hole.
2. **Idempotency guard (`block_attr`)** — each agent skips if the ClaimRecord field it populates is
   already set. Makes the relay safe against backlog re-delivery and the broadcast (below). Without it,
   a redelivered/echoed record restarts the chain → infinite loop.
3. **Broadcast final verdict** — the adjudicator's terminal message mentions human + all 3 peer agents
   (not just the human). Reason: `list_agent_messages` is **mention-scoped**, so a human-only mention is
   invisible to agent-key queries (the decision couldn't be captured in the trail). Broadcasting makes
   the verdict visible to the whole band and the evidence tooling; the idempotency guard stops it
   re-triggering the relay. **This is also a nicer demo** (the band sees the verdict).
4. **CrewAI `on_started` no-op (adjudicator)** — since `on_event` is overridden, the crew LLM is never
   used; its `on_started` tried to build `LLM(groq/openai/gpt-oss-120b)` which needs `litellm` (absent)
   and crashed. No-op'd it — the adapter is only Band identity/transport here.
**Note:** the note model for Groq agents is `llama-3.3-70b-versatile` (D-note), because `gpt-oss-120b`
is a reasoning model that returns empty visible content for tiny note prompts. Gemini notes currently
hit the free-tier 20/day cap → template fallback (relay unaffected — proves the D13 resilience).
**Operational debt to clean up:** three throwaway rooms were created during bring-up
(`38dc6e6c…`, `2e7e1b59…`, `34cd5ad4…`); current `BAND_ROOM_ID` is `34cd5ad4…`. `clear_room.py` is buggy
(mishandles the list response). Pick ONE demo room and delete the orphans (or leave them — harmless).

## D15 — Hybrid: deterministic guardrails + real LLM narrative judgment (2026-06-19)
**Decision:** Reintroduce the LLM to the decision path, but only as a *bounded judgment on top of*
deterministic guardrails — not as the data carrier. The Fraud agent calls Groq (`groq_narrative_risk`)
to read the free-text incident narrative and return `narrative_risk` (0–40) + a one-line rationale,
folded into `risk_score = min(100, rule_risk + narrative_risk)`.
**Why:** D13 took the LLM off the path for reliability, but the side effect was that the agents made
no real decisions — the pure functions decided everything, and the JS showcase made that glaring. For a
hackathon judged on genuine agent decision-making, that was the core weakness. D15 lets the model decide
what rules can't (narrative/contextual fraud the field checks miss) while keeping the data flow
deterministic and adding a rules-only fallback — so reliability (the D13 concern) is preserved.
**Alternatives rejected (time/infra):** live serverless LLM in Vercel (needs keys + 429 handling under
deadline); live-through-Band on judge inputs (needs an always-on agent host the user doesn't have).
Chosen path = capture real Groq reasoning + replay, which needs no backend and can't fail at judging.
**Guardrail discipline:** the LLM never overrides hard rules (can't approve an expired policy); it only
adds risk/nuance within the deterministic floor. Vendor = Groq (reliable, not the Gemini free-tier cap).
