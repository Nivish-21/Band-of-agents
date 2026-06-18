import os
import sys
import json
import asyncio
from dotenv import load_dotenv
from band.config import load_agent_config
from band.client.rest import AsyncRestClient
from thenvoi_rest.types.chat_message_request import ChatMessageRequest
from thenvoi_rest.types.chat_message_request_mentions_item import (
    ChatMessageRequestMentionsItem,
)

load_dotenv(override=True)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python seed.py <fixture_name>")
        print("Example: python seed.py clean.json")
        sys.exit(1)

    fixture_name = sys.argv[1]
    room_id = os.environ.get("BAND_ROOM_ID")
    if not room_id:
        print("Error: BAND_ROOM_ID environment variable not set.")
        sys.exit(1)

    fixture_path = os.path.join(os.path.dirname(__file__), "claims", fixture_name)
    if not os.path.exists(fixture_path):
        print(f"Error: Fixture {fixture_path} not found.")
        sys.exit(1)

    with open(fixture_path, "r") as f:
        claim_data = json.load(f)

    claim_str = json.dumps(claim_data, indent=2)

    try:
        agent_id, api_key = load_agent_config("coverage")
        intake_id, _ = load_agent_config("intake")
    except Exception as e:
        print(f"Error loading agent config: {e}")
        sys.exit(1)

    rest_url = os.environ.get("BAND_REST_URL", "https://app.band.ai").rstrip("/")

    client = AsyncRestClient(api_key=api_key, base_url=rest_url)

    content = (
        f"New claim submitted for review:\n```json\n{claim_str}\n```\nPlease validate."
    )
    mentions = [
        ChatMessageRequestMentionsItem(id=intake_id, handle="nivishnick2k/intake")
    ]

    try:
        print(f"Posting {fixture_name} to room {room_id}...")
        await client.agent_api_messages.create_agent_chat_message(
            chat_id=room_id,
            message=ChatMessageRequest(content=content, mentions=mentions),
        )
        print("Success! Claim posted to the room.")
    except Exception as e:
        print(f"Failed. Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
