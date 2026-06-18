# Gemini fix #3 — DR3 re-run (tuple-tool bug already fixed by planner)

The planner found and fixed the real DR3 v2 bug: Coverage + Adjudicator tuple tools were declared
`def fn(claim_record_json: str)` but the SDK passes the InputModel INSTANCE, so they received a
`CoverageInput` object (the "type mismatch" error), which caused the retry storm → Gemini 429.
Fixed to `def fn(args: XInput)` and verified offline. temperature=0 added to Intake + Fraud.

Two things remain; paste this to Gemini:

```
The tuple-tool signature bug (Coverage/Adjudicator) is already fixed and verified offline. Do this:

1. PROMPT TIGHTENING (fixes Intake gpt-oss "missing properties: claim_record_json"): in
   claimband/prompts/*.md, make the tool-call instruction explicit and unmissable, e.g.:
   "Call your tool. The `claim_record_json` argument MUST be the ENTIRE claim JSON object you
   received, copied verbatim as a JSON string — never call the tool with empty or partial
   arguments." Keep the handoff instruction (send_message with mentions=["nivishnick2k/<next>"]).

2. RATE LIMIT (Gemini free tier 429): switch Coverage and Adjudicator to "gemini-2.5-flash-lite"
   (higher RPM) OR add a short asyncio.sleep between Gemini calls. The tuple-tool fix already stops
   the error-retry storm that mainly caused the 429.

3. RE-RUN DR3: start all 4 agents (each prints connect + room join), then `python seed.py clean.json`.
   Watch the room: Intake->Coverage->Fraud->Adjudicator->decision = APPROVE. Repeat deny.json (DENY)
   and fraud.json (ESCALATE). Capture the trail via
   AsyncRestClient(api_key=<any agent>, base_url=BAND_REST_URL)
     .agent_api_messages.list_agent_messages(chat_id=os.environ["BAND_ROOM_ID"]).

4. If any agent still errors, the error capture now prints e.body — paste the exact failed_generation /
   error for the planner. Do NOT re-guess root causes; report the raw error.

5. Report: DR3 per fixture (status + room-trail evidence) and the 6 acceptance criteria. Update
   docs/status.md + docs/changelog.md. Keep black clean; do not break the 18 tests.
```

## Launch
```bash
cd /Users/nivish/development/Band-of-agents && gemini
```
```
