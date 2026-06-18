# Learnings and Resolution Report (DR3 Re-run)

## The Bottleneck and The Loop
The core issue blocking the final DR3 live relay was a compounding sequence of **Tool Argument Omissions** interacting with **Hard API Rate Limits**:
1. **The Loop:** When the `gpt-oss-120b` (Intake/Fraud) or `gemini` models were invoked, they often emitted a tool call to their respective tools (e.g., `validate_claim` or `compute_coverage`) but failed to include the required `claim_record_json` argument, or passed an incomplete payload. 
2. **The Resulting Crash:** This caused a Pydantic validation error (`missing properties: 'claim_record_json'`) or a type mismatch.
3. **The Retry Storm:** The `band-sdk` adapter naturally attempted to retry the failed generation/tool-call. Because the prompt wasn't strict enough to force the LLM to provide the correct payload on retry, it would fail again, burning tokens.
4. **The Rate Limit Wall:** The rapid retries and the high token cost of passing the full claim JSON back and forth quickly exhausted the strict free-tier rate limits. Specifically:
   - **Groq:** Hit TPM (Tokens Per Minute) limits (`429 Rate limit reached... Limit 8000, Used 7134`).
   - **Gemini:** Hit RPD (Requests Per Day) free tier limits (`429 RESOURCE_EXHAUSTED... limit: 20`).

## What Broke
- **API 429 Exhaustion:** Agents crashed mid-relay because they hit API usage caps.
- **Environment State:** Recreating the chat room using `create_new_room.py` updated the `.env` file with a new `BAND_ROOM_ID`, but the long-running background agents and the `seed.py` script were using cached environment variables from when they were launched, causing them to look for the old, deleted room.
- **Test Suite Imports:** Running `pytest` directly failed with `ModuleNotFoundError: No module named 'claimband'` because the working directory wasn't properly set in the `PYTHONPATH` context.

## What Fixed It
- **Prompt Tightening:** Updated `claimband/prompts/*.md` across all 4 agents to include a `**CRITICAL:**` instruction. We mandated that the tool MUST be called and the `claim_record_json` argument is **REQUIRED** and MUST contain the ENTIRE claim JSON object copied verbatim.
- **Model Downscaling for Limits:** Switched Coverage and Adjudicator agents to use `gemini-2.5-flash-lite` (and `gemini/gemini-2.5-flash-lite` via LiteLLM for CrewAI) which has more forgiving limits than the standard/latest models.
- **Environment Refreshing:** Added `load_dotenv(override=True)` to the top of all agent scripts (`intake.py`, `coverage.py`, `fraud.py`, `adjudicator.py`) and `seed.py`. This ensures that anytime the scripts are run, they pull the freshest `BAND_ROOM_ID` from the `.env` file.
- **PYTHONPATH Fix:** Prepended `PYTHONPATH=.` when executing the agents and tests (`PYTHONPATH=. ./.venv/bin/python ...`) to ensure local imports resolve correctly.
- **Artificial Throttling:** Implemented manual delays (`sleep 30`) between seeding the different claim fixtures (`clean.json`, `deny.json`, `fraud.json`) to give the free-tier APIs time to cool down and recover their TPM buckets.

## What Needs to be Changed / Can be Fixed
- **Automated Throttling in Seed:** `seed.py` could be updated to accept multiple fixtures and automatically apply an `asyncio.sleep()` between dispatches.
- **Robust Room Management:** A script like `clear_room.py` should be finalized to allow wiping an existing room's messages instead of constantly creating new rooms (which leaves orphaned rooms in the workspace).
- **Agent Resiliency:** Agents could catch `429` errors and implement a local exponential backoff or hibernation state before crashing the process completely.

## What Cannot be Fixed Right Now
- **Hard Free-Tier Quotas:** The Gemini `RESOURCE_EXHAUSTED` (20 requests per day limit for flash-lite on the free tier) and the Groq `on_demand` TPM limits are hard caps imposed by the vendors. Without upgrading the billing tier or providing paid API keys, the system cannot process claims rapidly or concurrently. The only mitigation is extreme throttling (waiting between claims).
