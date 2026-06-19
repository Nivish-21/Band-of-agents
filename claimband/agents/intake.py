"""Intake agent — LangGraph adapter + Groq (gpt-oss-120b).

Validates the incoming claim, then hands off to Coverage. Uses the
deterministic relay engine (see D13): the framework adapter provides
identity/transport while ``on_event`` is the relay handler.
"""

import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from band import Agent
from band.adapters import LangGraphAdapter
from band.config import load_agent_config
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from claimband.schema import ClaimRecord, validate_claim
from claimband.notes import groq_note
from claimband.relay import make_relay_handler, serve

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "intake.md"
with open(PROMPT_PATH, "r") as f:
    INTAKE_PROMPT = f.read()

AGENT_NAME = "intake"


def transform(record: ClaimRecord) -> ClaimRecord:
    record.intake = validate_claim(record.model_dump(mode="json"))
    return record


def summary(record: ClaimRecord) -> str:
    block = record.intake
    if block is not None and block.is_valid:
        return (
            f"Claim {record.claim_id} validated — complete and consistent "
            f"({block.completeness_score:.0f}% completeness)."
        )
    issues = (block.missing_fields + block.inconsistencies) if block else []
    return f"Claim {record.claim_id} validated with issues: {', '.join(issues) or 'none recorded'}."


async def note_fn(record: ClaimRecord) -> str:
    return await groq_note(
        f"Intake validation result: {record.intake.model_dump_json()}"
    )


def _make_agent() -> Agent:
    agent_id, api_key = load_agent_config(AGENT_NAME)
    adapter = LangGraphAdapter(
        llm=ChatOpenAI(
            model="openai/gpt-oss-120b",
            base_url=os.environ["GROQ_BASE_URL"],
            api_key=os.environ["GROQ_API_KEY"],
            temperature=0,
        ),
        checkpointer=InMemorySaver(),
        custom_section=INTAKE_PROMPT,
    )
    adapter.on_event = make_relay_handler(
        AGENT_NAME, agent_id, transform, summary, "intake", note_fn
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
    print("[Intake] framework=LangGraph vendor=Groq", flush=True)
    print(f"[Intake] connect OK - Room ID: {room_id}", flush=True)
    print("Starting Intake Agent...", flush=True)
    await serve(AGENT_NAME, _make_agent)


if __name__ == "__main__":
    asyncio.run(main())
