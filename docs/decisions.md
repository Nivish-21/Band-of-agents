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
