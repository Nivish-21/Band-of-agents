# Gemini fix #2 — DR3 Intake crash (root cause found)

DR1 + DR2 pass. DR3 crashed on the FIRST hop. Planner forensics (docs/decisions.md D10): it is NOT a
Groq/LangGraph incompatibility. Isolated llama tool calls work fine. The real cause: Intake is the only
agent on `llama-3.3-70b-versatile` (the weakest tool-caller), and it mis-emits a tool call against the
live SDK toolset (the real `send_message` has a union-typed `mentions` schema), which Groq rejects as a
malformed function call. Fraud already uses `openai/gpt-oss-120b` reliably.

Paste this to Gemini:

```
DR3 crashed on hop 1 (Intake). Root cause is the model, not the platform. Do exactly this, fast:

1. ONE-LINE FIX: in claimband/agents/intake.py change the ChatOpenAI model from
   "llama-3.3-70b-versatile" to "openai/gpt-oss-120b" (the model the Fraud agent already uses).
   Leave everything else (LangGraph adapter, prompt, tool) unchanged — we keep cross-framework
   (LangGraph) and cross-vendor (Groq + Google).

2. SAFETY NET: in each LangGraph/Groq agent, wrap the agent run so a Groq APIError prints the real
   detail instead of crashing blind — catch openai.APIError and log e.body (which contains
   'failed_generation'), so if a malformed tool call recurs we see the exact bad call.

3. RE-RUN DR3: start all 4 agents, then `python seed.py clean.json`. Watch the room for
   Intake->Coverage->Fraud->Adjudicator->decision = APPROVE. Repeat deny.json (->DENY) and
   fraud.json (->ESCALATE). Capture the message trail via
   AsyncRestClient(...).agent_api_messages.list_agent_messages(chat_id=BAND_ROOM_ID).

4. If a LATER hop crashes with the same failed_generation error, swap THAT agent's Groq model to
   openai/gpt-oss-120b too and re-run. If a Gemini-based agent (Coverage/Adjudicator) misbehaves,
   print its error and report — do not guess.

5. Report: DR3 result per fixture (APPROVE/DENY/ESCALATE) with room-trail evidence, plus the 6
   acceptance criteria. Update docs/status.md and docs/changelog.md. Keep black clean.
```

## Launch
```bash
cd /Users/nivish/development/Band-of-agents && gemini
```
```
