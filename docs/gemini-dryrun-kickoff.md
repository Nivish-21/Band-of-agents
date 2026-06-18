# Gemini dry-run prompt — ClaimBand (room now exists)

Blocker cleared by the planner: the keys are VALID and a shared room exists. Launch Gemini in the
project root and paste the prompt below.

```
The earlier "bad keys" blocker was a misdiagnosis — the Band keys are VALID (verified via the SDK's
agent_api_identity.get_agent_me()). A shared room now exists: BAND_ROOM_ID=100b711f-2db9-4d7a-bb4f-
fe71d09914f8, saved in .env, containing all 4 agents + the human owner (nivishnick2k). Your F1-F5
code fixes are in. Now make the live relay actually run and report. Hackathon pace.

DO FIRST:
- Make claimband seed.py read BAND_ROOM_ID from env (os.environ["BAND_ROOM_ID"]) instead of a CLI arg.
  Post the seed via the SDK: AsyncRestClient(api_key=intake_key, base_url=BAND_REST_URL)
  .agent_api_messages.create_agent_chat_message(chat_id=BAND_ROOM_ID,
   message=ChatMessageRequest(content="<claim JSON in ```json block>",
   mentions=[ChatMessageRequestMentionsItem(id=intake_agent_id, handle="nivishnick2k/intake")])).
- Sanity: re-confirm each agent's send_message handoff uses structured mentions with owner-qualified
  handles "nivishnick2k/<next>" (not plain text).

DRY RUN — run all three, report PASS/FAIL with evidence:
- DR1 Offline: pytest (expect 18 passing) + run the 3 fixtures through the pure pipeline.
- DR2 Connectivity: ping Groq + Gemini for a 1-token completion; start each of the 4 agents
  (python -m claimband.agents.<role>) and confirm each logs a successful WebSocket connect + room
  join for BAND_ROOM_ID. Report each agent PASS/FAIL.
- DR3 Live relay: with all 4 agents running, `python seed.py clean.json`; watch the room for
  Intake->Coverage->Fraud->Adjudicator->decision = APPROVE. Repeat for deny.json (->DENY) and
  fraud.json (->ESCALATE). Use AsyncRestClient.agent_api_messages.list_agent_messages(chat_id=
  BAND_ROOM_ID) to capture the message trail as evidence.

Then check the 6 acceptance criteria in docs/prd.md. Fix any failures (most likely: an agent not
handing off because the LLM didn't call send_message with mentions — tighten the prompt; or JSON
getting mangled across hops — make the tool return the full record and the prompt forward it
verbatim). Loop DR3 until the 3 fixtures pass or you hit a genuine SDK/platform error, then STOP and
report exactly what failed with the error text. Update docs/status.md and docs/changelog.md.

REPORT: table of DR1/DR2/DR3 (pass/fail + evidence) and the 6 criteria, plus any remaining bugs for
the planner to triage.
```

## Launch
```bash
cd /Users/nivish/development/Band-of-agents && gemini
```
```
