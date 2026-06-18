import os
import asyncio
from dotenv import load_dotenv
from band.config import load_agent_config
from band.client.rest import AsyncRestClient

load_dotenv()


async def main():
    room_id = os.environ.get("BAND_ROOM_ID")
    if not room_id:
        print("Error: BAND_ROOM_ID environment variable not set.")
        return

    try:
        _, api_key = load_agent_config("coverage")
    except Exception as e:
        print(f"Error loading agent config: {e}")
        return

    rest_url = os.environ.get("BAND_REST_URL", "https://app.band.ai").rstrip("/")
    client = AsyncRestClient(api_key=api_key, base_url=rest_url)

    try:
        messages = await client.agent_api_messages.list_agent_messages(chat_id=room_id)
        for message in messages:
            await client.agent_api_messages.delete_agent_chat_message(
                chat_id=room_id, message_id=message.id
            )
        print(f"Cleared {len(messages)} messages from room {room_id}")
    except Exception as e:
        print(f"Failed to clear room. Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
