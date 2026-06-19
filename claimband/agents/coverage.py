"""Coverage agent — Gemini SDK adapter + Gemini (gemini-2.5-flash-lite).

Determines policy coverage, then hands off to Fraud. Deterministic relay (D13).
This is the genuine Gemini-vendor agent in the cross-vendor story.
"""

import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from band import Agent
from band.adapters import GeminiAdapter
from band.config import load_agent_config

from claimband.schema import ClaimRecord
from claimband.coverage import compute_coverage
from claimband.notes import gemini_note
from claimband.relay import make_relay_handler, serve

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "coverage.md"
with open(PROMPT_PATH, "r") as f:
    COVERAGE_PROMPT = f.read()

AGENT_NAME = "coverage"


def transform(record: ClaimRecord) -> ClaimRecord:
    record.coverage = compute_coverage(record)
    return record


def summary(record: ClaimRecord) -> str:
    block = record.coverage
    if block is None:
        return f"Coverage check incomplete for claim {record.claim_id}."
    if not block.policy_active:
        return "Policy is not active — claim not covered."
    if not block.peril_covered:
        return "Peril is not covered under this policy."
    return (
        f"Covered: ${block.covered_amount:,.0f} payable after "
        f"${block.deductible_applied:,} deductible."
    )


async def note_fn(record: ClaimRecord) -> str:
    return await gemini_note(
        f"Coverage determination result: {record.coverage.model_dump_json()}"
    )


def _make_agent() -> Agent:
    agent_id, api_key = load_agent_config(AGENT_NAME)
    adapter = GeminiAdapter(
        model="gemini-2.5-flash-lite",
        prompt=COVERAGE_PROMPT,
    )
    adapter.on_event = make_relay_handler(
        AGENT_NAME, agent_id, transform, summary, "coverage", note_fn
    )
    return Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.environ["BAND_WS_URL"],
        rest_url=os.environ["BAND_REST_URL"],
    )


async def main() -> None:
    room_id = os.environ.get("BAND_ROOM_ID", "UNKNOWN")
    print("[Coverage] framework=Gemini-SDK vendor=Gemini", flush=True)
    print(f"[Coverage] connect OK - Room ID: {room_id}", flush=True)
    print("Starting Coverage Agent...", flush=True)
    await serve(AGENT_NAME, _make_agent)


if __name__ == "__main__":
    asyncio.run(main())
