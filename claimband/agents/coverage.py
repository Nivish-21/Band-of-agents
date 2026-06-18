import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
from pydantic import BaseModel, Field

from band import Agent
from band.adapters import GeminiAdapter
from band.config import load_agent_config
from band.core.types import AdapterFeatures, Emit

from claimband.schema import ClaimRecord
from claimband.coverage import compute_coverage

load_dotenv(override=True)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "coverage.md"
with open(PROMPT_PATH, "r") as f:
    COVERAGE_PROMPT = f.read()


class CoverageInput(BaseModel):
    claim_record_json: str = Field(
        description="The full JSON string of the current claim record."
    )


def run_compute_coverage(args: CoverageInput) -> str:
    # SDK tuple-tool convention: the callable receives the validated InputModel
    # instance (see band.runtime.custom_tools.execute_custom_tool), not the raw field.
    try:
        data = json.loads(args.claim_record_json)
        claim = ClaimRecord.model_validate(data)
        claim.coverage = compute_coverage(claim)
        return claim.model_dump_json()
    except Exception as e:
        return f"Error: {str(e)}"


async def main():
    agent_id, api_key = load_agent_config("coverage")

    adapter = GeminiAdapter(
        model="gemini-2.5-flash-lite",
        prompt=COVERAGE_PROMPT,
        additional_tools=[(CoverageInput, run_compute_coverage)],
        features=AdapterFeatures(emit={Emit.EXECUTION}),
        max_retries=2,
        retry_base_delay_s=3.0,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.environ["BAND_WS_URL"],
        rest_url=os.environ["BAND_REST_URL"],
    )

    print("Starting Coverage Agent...")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
