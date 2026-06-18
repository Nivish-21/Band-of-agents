import os
import asyncio
from dotenv import load_dotenv
from google import genai

load_dotenv()


async def main():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    print("Listing models...")
    try:
        response = client.models.list()
        for m in response:
            print(f"Model Name: {m.name}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
