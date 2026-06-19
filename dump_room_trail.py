import os
import asyncio
from dotenv import load_dotenv
from band.config import load_agent_config
from band.client.rest import AsyncRestClient

load_dotenv()


async def get_agent_messages(agent_name, room_id):
    try:
        agent_id, api_key = load_agent_config(agent_name)
        rest_url = os.environ.get("BAND_REST_URL").rstrip("/")
        client = AsyncRestClient(api_key=api_key, base_url=rest_url)
        resp = await client.agent_api_messages.list_agent_messages(
            chat_id=room_id, status="all", page_size=100
        )
        return resp.data or []
    except Exception as e:
        print(f"Error fetching for {agent_name}: {e}")
        return []


async def build_trail(room_id: str) -> str:
    """Return the merged, de-duplicated, time-sorted room trail as a string.

    Unions every agent key's view of the room (the verdict is only visible
    because it is broadcast to all agents) and dedupes by message id.
    """
    agents = ["intake", "coverage", "fraud", "adjudicator"]

    tasks = [get_agent_messages(name, room_id) for name in agents]
    results = await asyncio.gather(*tasks)

    all_messages = {}
    for name, msg_list in zip(agents, results):
        for m in msg_list:
            all_messages[m.id] = m

    sorted_messages = sorted(all_messages.values(), key=lambda x: x.inserted_at)

    lines = [f"Total unique messages found across all agents: {len(sorted_messages)}"]
    for idx, m in enumerate(sorted_messages):
        sender = m.sender_name or m.sender_type or "Unknown"
        lines.append(
            f"\n--- MESSAGE #{idx+1} | Sender: {sender} | Time: {m.inserted_at} | ID: {m.id} ---"
        )
        lines.append(m.content)
    return "\n".join(lines)


async def main() -> None:
    room_id = os.environ.get("BAND_ROOM_ID")
    if not room_id:
        print("Error: BAND_ROOM_ID environment variable not set.")
        return
    print(await build_trail(room_id))


if __name__ == "__main__":
    asyncio.run(main())
