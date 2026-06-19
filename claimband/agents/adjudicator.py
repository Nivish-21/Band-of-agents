"""Adjudicator agent — CrewAI adapter + Groq (groq/openai/gpt-oss-120b, see D12).

Produces the final APPROVE / DENY / ESCALATE decision and routes to the human.
Deterministic relay (D13): terminal hop, mentions the human (esp. on ESCALATE).
"""

import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from band import Agent
from band.adapters import CrewAIAdapter
from band.config import load_agent_config

from claimband.schema import ClaimRecord
from claimband.adjudication import adjudicate_claim
from claimband.notes import groq_note
from claimband.relay import make_relay_handler, serve

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "adjudicator.md"
with open(PROMPT_PATH, "r") as f:
    ADJUDICATOR_BACKSTORY = f.read()

AGENT_NAME = "adjudicator"


def transform(record: ClaimRecord) -> ClaimRecord:
    record.decision = adjudicate_claim(record)
    return record


def summary(record: ClaimRecord) -> str:
    block = record.decision
    if block is None:
        return f"No decision reached for claim {record.claim_id}."
    if block.status == "APPROVE":
        return f"APPROVE — ${block.final_amount:,.0f} payable. {block.reason}"
    return f"{block.status} — {block.reason}"


async def note_fn(record: ClaimRecord) -> str:
    return await groq_note(
        f"Adjudication decision: {record.decision.model_dump_json()}"
    )


async def _skip_crew_init(*_args, **_kwargs) -> None:
    # The deterministic relay overrides on_event, so the CrewAI crew/LLM is
    # never invoked. Skip its on_started LLM init (which needs litellm for
    # groq/* models) — we only use this adapter for Band identity + transport.
    return None


def _make_agent() -> Agent:
    agent_id, api_key = load_agent_config(AGENT_NAME)
    adapter = CrewAIAdapter(
        model="groq/openai/gpt-oss-120b",
        role="Claims Adjudicator",
        goal="Decide APPROVE/DENY/ESCALATE from peer findings",
        backstory=ADJUDICATOR_BACKSTORY,
    )
    adapter.on_event = make_relay_handler(
        AGENT_NAME, agent_id, transform, summary, "decision", note_fn
    )
    adapter.on_started = _skip_crew_init
    return Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.environ["BAND_WS_URL"],
        rest_url=os.environ["BAND_REST_URL"],
    )


async def main() -> None:
    room_id = os.environ.get("BAND_ROOM_ID", "UNKNOWN")
    print("[Adjudicator] framework=CrewAI vendor=Groq", flush=True)
    print(f"[Adjudicator] connect OK - Room ID: {room_id}", flush=True)
    print("Starting Adjudicator Agent...", flush=True)
    await serve(AGENT_NAME, _make_agent)


if __name__ == "__main__":
    asyncio.run(main())
