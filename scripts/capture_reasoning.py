"""Capture the Fraud agent's REAL Groq narrative judgment for each fixture and
inject it into web/data/scenarios.json.

This runs the exact function the live Fraud agent runs (claimband.notes.
groq_narrative_risk) against each captured claim, so the showcase can display a
genuine model decision — the agent reading the free-text story and adding risk
the deterministic rules can't see — alongside the real Band-room trail.

Run from repo root in the venv (needs GROQ_BASE_URL + GROQ_API_KEY in .env):
    PYTHONPATH=. ./.venv/bin/python scripts/capture_reasoning.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from claimband.notes import groq_narrative_risk

load_dotenv(override=True)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "data" / "scenarios.json"


def claim_summary(record: dict) -> str:
    inc = record["incident"]
    dmg = record["damage"]
    return (
        f"Incident type: {inc['type']}; at fault: {inc['at_fault']}; "
        f"description: \"{inc['description']}\". "
        f"Damage estimate: ${dmg['estimate_amount']:,.0f} on a {dmg['vehicle']}, "
        f"{dmg['photos_count']} photo(s). Amount claimed: ${record['amount_claimed']:,.0f}."
    )


async def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for key, sc in data["scenarios"].items():
        record = sc["record"]
        fraud = record.get("fraud") or {}
        rule_risk = int(fraud.get("risk_score", 0))
        summary = claim_summary(record)
        narrative_risk, rationale = await groq_narrative_risk(summary)
        fraud["rule_risk"] = rule_risk
        fraud["narrative_risk"] = narrative_risk
        fraud["narrative_rationale"] = rationale
        record["fraud"] = fraud
        print(f"  {key}: rule={rule_risk} +narrative={narrative_risk} :: {rationale}")
    DATA.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {DATA}")


if __name__ == "__main__":
    asyncio.run(main())
