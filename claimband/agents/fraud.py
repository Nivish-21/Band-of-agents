import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import openai
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from band import Agent
from band.adapters import LangGraphAdapter
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from band.config import load_agent_config

from claimband.schema import ClaimRecord
from claimband.scoring import score_risk

load_dotenv(override=True)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "fraud.md"
with open(PROMPT_PATH, "r") as f:
    FRAUD_PROMPT = f.read()


class FraudInput(BaseModel):
    claim_record_json: str = Field(
        description="The full JSON string of the current claim record."
    )


@tool("score_risk", args_schema=FraudInput)
def run_score_risk(claim_record_json: str) -> str:
    """Computes risk score and returns the full JSON record with fraud block."""
    try:
        data = json.loads(claim_record_json)
        claim = ClaimRecord.model_validate(data)
        block = score_risk(claim)
        claim.fraud = block
        return claim.model_dump_json()
    except Exception as e:
        return f"Error computing risk score: {str(e)}"


class WrappedChatOpenAI(ChatOpenAI):
    async def _astream(self, *args, **kwargs):
        try:
            async for chunk in super()._astream(*args, **kwargs):
                yield chunk
        except openai.APIError as e:
            print(f"--- Groq APIError Body: {getattr(e, 'body', None)} ---", flush=True)
            raise e

    async def ainvoke(self, *args, **kwargs):
        try:
            return await super().ainvoke(*args, **kwargs)
        except openai.APIError as e:
            print(f"--- Groq APIError Body: {getattr(e, 'body', None)} ---", flush=True)
            raise e


async def main():
    agent_id, api_key = load_agent_config("fraud")

    adapter = LangGraphAdapter(
        llm=WrappedChatOpenAI(
            model="openai/gpt-oss-120b",
            base_url=os.environ["GROQ_BASE_URL"],
            api_key=os.environ["GROQ_API_KEY"],
            temperature=0,
        ),
        checkpointer=InMemorySaver(),
        custom_section=FRAUD_PROMPT,
        additional_tools=[run_score_risk],
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.environ["BAND_WS_URL"],
        rest_url=os.environ["BAND_REST_URL"],
    )

    print("Starting Fraud Agent...")
    try:
        await agent.run()
    except openai.APIError as e:
        print(f"Groq APIError: {e}")
        print(f"Details: {getattr(e, 'body', None)}")


if __name__ == "__main__":
    asyncio.run(main())
