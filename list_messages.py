import os
import asyncio
from dotenv import load_dotenv
from band.config import load_agent_config
from band.client.rest import AsyncRestClient

load_dotenv()


async def main():
    room_id = os.environ.get("BAND_ROOM_ID")
    agent_id, api_key = load_agent_config("intake")
    rest_url = os.environ.get("BAND_REST_URL").rstrip("/")
    client = AsyncRestClient(api_key=api_key, base_url=rest_url)

    resp = await client.agent_api_messages.list_agent_messages(chat_id=room_id)
    if not resp.data:
        print("NO MESSAGES RETURNED.")
    for idx, m in enumerate(resp.data):
        print(f"Message {idx}: {m}")


if __name__ == "__main__":
    asyncio.run(main())
