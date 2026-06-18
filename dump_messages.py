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

    resp = await client.agent_api_messages.list_agent_messages(
        chat_id=room_id, status="all", page_size=100
    )
    if not resp.data:
        print("NO MESSAGES RETURNED.")
        return

    # Sort chronologically by inserted_at
    messages = sorted(resp.data, key=lambda x: x.inserted_at)

    print(f"Total messages: {len(messages)}")
    for idx, m in enumerate(messages):
        sender = m.sender_name or m.sender_type or "Unknown"
        print(f"--- MESSAGE #{idx+1} | Sender: {sender} | Time: {m.inserted_at} ---")
        print(m.content)
        print()


if __name__ == "__main__":
    asyncio.run(main())
