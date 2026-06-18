import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from band import Agent
from band.adapters import CrewAIAdapter
from band.config import load_agent_config
import json
from pydantic import BaseModel, Field
from claimband.schema import ClaimRecord
from claimband.adjudication import adjudicate_claim

load_dotenv(override=True)
os.environ["LITELLM_MAX_RETRIES"] = "2"

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "adjudicator.md"
with open(PROMPT_PATH, "r") as f:
    ADJUDICATOR_BACKSTORY = f.read()


class AdjudicatorInput(BaseModel):
    claim_record_json: str = Field(
        description="The full JSON string of the current claim record."
    )


def run_adjudicate(args: AdjudicatorInput) -> str:
    # SDK tuple-tool convention: the callable receives the validated InputModel
    # instance (see band.runtime.custom_tools.execute_custom_tool), not the raw field.
    try:
        data = json.loads(args.claim_record_json)
        claim = ClaimRecord.model_validate(data)
        claim.decision = adjudicate_claim(claim)
        return claim.model_dump_json()
    except Exception as e:
        return f"Error adjudicating claim: {str(e)}"


async def main():
    agent_id, api_key = load_agent_config("adjudicator")

    adapter = CrewAIAdapter(
        model="gemini/gemini-2.5-flash-lite",
        role="Claims Adjudicator",
        goal="Decide APPROVE/DENY/ESCALATE from peer findings",
        backstory=ADJUDICATOR_BACKSTORY,
        additional_tools=[(AdjudicatorInput, run_adjudicate)],
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.environ["BAND_WS_URL"],
        rest_url=os.environ["BAND_REST_URL"],
    )

    print("Starting Adjudicator Agent...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
