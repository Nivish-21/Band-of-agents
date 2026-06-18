import os
import asyncio
import requests
from dotenv import load_dotenv
from band.config import load_agent_config

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from band.client.rest import AsyncRestClient

load_dotenv()


async def test_llm_ping():
    print("\n--- Testing LLM Connectivity ---")
    try:
        groq = ChatOpenAI(
            model="llama-3.3-70b-versatile",
            base_url=os.environ["GROQ_BASE_URL"],
            api_key=os.environ["GROQ_API_KEY"],
            max_tokens=1,
        )
        groq.invoke([HumanMessage(content="Hello")])
        print("Groq (Llama): OK")
    except Exception as e:
        print(f"Groq: FAIL - {e}")

    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            print("Gemini API: OK")
        else:
            print(f"Gemini API: FAIL - Status {resp.status_code}")
    except Exception as e:
        print(f"Gemini API: FAIL - {e}")


async def test_agent_connectivity():
    print("\n--- Testing Agent Connectivity ---")
    roles = ["intake", "coverage", "fraud", "adjudicator"]
    for role in roles:
        try:
            agent_id, api_key = load_agent_config(role)
            rest_url = os.environ.get("BAND_REST_URL", "https://app.band.ai").rstrip(
                "/"
            )
            client = AsyncRestClient(api_key=api_key, base_url=rest_url)

            me = await client.agent_api_identity.get_agent_me()
            print(f"Agent {role}: CONNECTED as {me.data.id} / handle: {me.data.handle}")
        except Exception as e:
            print(f"Agent {role}: FAIL - {e}")


if __name__ == "__main__":
    asyncio.run(test_llm_ping())
    asyncio.run(test_agent_connectivity())
