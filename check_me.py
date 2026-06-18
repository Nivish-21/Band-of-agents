import asyncio, os
from dotenv import load_dotenv
from band.config import load_agent_config
from band.client.rest import AsyncRestClient

load_dotenv()


async def main():
    agent_id, api_key = load_agent_config("intake")
    rest_url = os.environ.get("BAND_REST_URL").rstrip("/")
    client = AsyncRestClient(api_key=api_key, base_url=rest_url)
    me = await client.agent_api_identity.get_agent_me()
    print("Dict:", getattr(me, "__dict__", {}))
    print("Dir:", dir(me))
    print("agent_id:", getattr(me, "agent_id", None))


if __name__ == "__main__":
    asyncio.run(main())
