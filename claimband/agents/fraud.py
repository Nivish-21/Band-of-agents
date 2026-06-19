"""Fraud agent — LangGraph adapter + Groq (gpt-oss-120b).

Scores fraud risk, then hands off to the Adjudicator. Deterministic relay (D13).
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

from claimband.schema import ClaimRecord
from claimband.scoring import score_risk
from claimband.notes import groq_note, groq_narrative_risk
from claimband.relay import make_relay_handler, serve

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "fraud.md"
with open(PROMPT_PATH, "r") as f:
    FRAUD_PROMPT = f.read()

AGENT_NAME = "fraud"


def transform(record: ClaimRecord) -> ClaimRecord:
    record.fraud = score_risk(record)
    return record


def _claim_summary(record: ClaimRecord) -> str:
    inc = record.incident
    dmg = record.damage
    return (
        f"Incident type: {inc.type}; at fault: {inc.at_fault}; "
        f'description: "{inc.description}". '
        f"Damage estimate: ${dmg.estimate_amount:,.0f} on a {dmg.vehicle}, "
        f"{dmg.photos_count} photo(s). Amount claimed: ${record.amount_claimed:,.0f}."
    )


async def judge(record: ClaimRecord) -> ClaimRecord:
    """Groq reads the free-text narrative and adds risk the rules can't see."""
    if record.fraud is None:
        return record
    narrative_risk, rationale = await groq_narrative_risk(_claim_summary(record))
    record.fraud.narrative_risk = narrative_risk
    record.fraud.narrative_rationale = rationale
    record.fraud.risk_score = min(100, record.fraud.rule_risk + narrative_risk)
    if rationale:
        record.fraud.reasons.append(
            f"LLM narrative judgment (+{narrative_risk}): {rationale}"
        )
    return record


def summary(record: ClaimRecord) -> str:
    block = record.fraud
    if block is None:
        return f"Fraud screen incomplete for claim {record.claim_id}."
    flags = ", ".join(block.red_flags) if block.red_flags else "no red flags"
    return f"Fraud risk score {block.risk_score}/100 — {flags}."


async def note_fn(record: ClaimRecord) -> str:
    return await groq_note(f"Fraud screening result: {record.fraud.model_dump_json()}")


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
        custom_section=FRAUD_PROMPT,
    )
    adapter.on_event = make_relay_handler(
        AGENT_NAME, agent_id, transform, summary, "fraud", note_fn, judge
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
    print("[Fraud] framework=LangGraph vendor=Groq", flush=True)
    print(f"[Fraud] connect OK - Room ID: {room_id}", flush=True)
    print("Starting Fraud Agent...", flush=True)
    await serve(AGENT_NAME, _make_agent)


if __name__ == "__main__":
    asyncio.run(main())
