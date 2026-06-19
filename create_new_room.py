import os
import asyncio
from dotenv import load_dotenv
from band.config import load_agent_config
from band.client.rest import AsyncRestClient
from thenvoi_rest import ChatRoomRequest, ParticipantRequest

load_dotenv()


async def main() -> str:
    agent_id, api_key = load_agent_config("intake")
    rest_url = os.environ.get("BAND_REST_URL").rstrip("/")
    client = AsyncRestClient(api_key=api_key, base_url=rest_url)

    print("Creating new chat room...")
    room_resp = await client.agent_api_chats.create_agent_chat(
        chat=ChatRoomRequest(title="DR3 Fresh Run Room")
    )
    room_id = room_resp.data.id
    print(f"Created chat room ID: {room_id}")

    # Participants to add: Coverage, Fraud, Adjudicator, and Owner
    # IDs gathered from check_participants.py
    participants = [
        ("Owner", "5f4ed8cf-e454-4854-a1cc-d57b1c296d9c"),
        ("Coverage", "c356072b-5f06-40a0-a3b5-ce562520fff2"),
        ("Fraud", "bf900eb2-2bd5-41e2-b764-a74c94d07362"),
        ("Adjudicator", "c90a5d2b-7974-49c6-bb13-59457bd9e1a0"),
    ]

    for name, pid in participants:
        print(f"Adding participant {name} ({pid})...")
        try:
            await client.agent_api_participants.add_agent_chat_participant(
                chat_id=room_id, participant=ParticipantRequest(participant_id=pid)
            )
            print(f"Added {name} successfully.")
        except Exception as e:
            print(f"Failed to add {name}: {e}")

    # Update the room ID in the .env file
    env_path = ".env"
    with open(env_path, "r") as f:
        env_lines = f.readlines()

    new_env_lines = []
    found = False
    for line in env_lines:
        if line.startswith("BAND_ROOM_ID="):
            new_env_lines.append(f"BAND_ROOM_ID={room_id}\n")
            found = True
        else:
            new_env_lines.append(line)
    if not found:
        new_env_lines.append(f"BAND_ROOM_ID={room_id}\n")

    with open(env_path, "w") as f:
        f.writelines(new_env_lines)

    print(f"Successfully updated {env_path} with new room ID: {room_id}")
    return room_id


if __name__ == "__main__":
    asyncio.run(main())
