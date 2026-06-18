import os
import sys
import yaml
import requests
from dotenv import load_dotenv

load_dotenv()

with open("agent_config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Get intake api_key
api_key = config["intake"]["api_key"]
rest_url = os.environ.get("BAND_REST_URL", "https://app.band.ai").rstrip("/")

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Get current agent info
resp = requests.get(f"{rest_url}/api/v1/agents/me", headers=headers)
if resp.status_code in (200, 201):
    print("Agent info:", resp.json())
else:
    print(f"Failed to get agent info. Status: {resp.status_code}")
    print(resp.text)

# Get chats
resp = requests.get(f"{rest_url}/api/v1/chats", headers=headers)
if resp.status_code in (200, 201):
    print("Chats:", resp.json())
else:
    print(f"Failed to get chats. Status: {resp.status_code}")
    print(resp.text)
