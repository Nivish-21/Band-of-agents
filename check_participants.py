import os
import asyncio
from dotenv import load_dotenv
from band.config import load_agent_config
from band.client.rest import AsyncRestClient

load_dotenv()


async def main():
    room_id = os.environ.get("BAND_ROOM_ID")
    if not room_id:
        print("BAND_ROOM_ID is not set.")
        return
    agent_id, api_key = load_agent_config("intake")
    rest_url = os.environ.get("BAND_REST_URL").rstrip("/")
    client = AsyncRestClient(api_key=api_key, base_url=rest_url)

    participants = await client.agent_api_participants.list_agent_chat_participants(
        chat_id=room_id
    )
    print(f"Participants in Room {room_id}:")
    for p in participants:
        print(f" - {p}")


if __name__ == "__main__":
    asyncio.run(main())
