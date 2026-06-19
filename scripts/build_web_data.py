"""Extract the real captured runs into web/data/scenarios.json for the showcase.

Source of truth: docs/evidence/dr3-{clean,deny,fraud}.txt — the live Band-room
trails. We parse the per-message dump, humanise the @[[uuid]] mentions, and pull
the final fully-populated ClaimRecord (the adjudicator's broadcast) so the UI can
render each agent's block and the verdict from genuine data — never a mock.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "docs" / "evidence"
OUT = ROOT / "web" / "data" / "scenarios.json"

# Participant UUID -> display handle (from create_new_room.py + relay HANDLES).
MENTION_MAP = {
    "8f6c3c7d-bf66-4b2c-8c52-69254772fb3e": "@intake",
    "c356072b-5f06-40a0-a3b5-ce562520fff2": "@coverage",
    "bf900eb2-2bd5-41e2-b764-a74c94d07362": "@fraud",
    "c90a5d2b-7974-49c6-bb13-59457bd9e1a0": "@adjudicator",
    "5f4ed8cf-e454-4854-a1cc-d57b1c296d9c": "@nivishnick2k (human)",
}

AGENTS = [
    {
        "key": "intake",
        "name": "Intake",
        "framework": "LangGraph",
        "vendor": "Groq",
        "produces": "intake",
    },
    {
        "key": "coverage",
        "name": "Coverage",
        "framework": "Gemini SDK",
        "vendor": "Gemini",
        "produces": "coverage",
    },
    {
        "key": "fraud",
        "name": "Fraud",
        "framework": "LangGraph",
        "vendor": "Groq",
        "produces": "fraud",
    },
    {
        "key": "adjudicator",
        "name": "Adjudicator",
        "framework": "CrewAI",
        "vendor": "Groq",
        "produces": "decision",
    },
]

SCENARIOS = {
    "clean": {
        "file": "dr3-clean.txt",
        "label": "Clean claim",
        "blurb": "A valid, low-risk collision claim.",
    },
    "deny": {
        "file": "dr3-deny.txt",
        "label": "Expired policy",
        "blurb": "Policy lapsed before the incident date.",
    },
    "fraud": {
        "file": "dr3-fraud.txt",
        "label": "Fraud signals",
        "blurb": "Multiple red flags trip the risk threshold.",
    },
    "ambiguous": {
        "file": "dr3-ambiguous.txt",
        "label": "Ambiguous risk",
        "blurb": "Moderate risk triggers Band peer-discovery for a second opinion.",
    },
}

_MSG_RE = re.compile(
    r"--- MESSAGE #(\d+) \| Sender: (.*?) \| Time: (.*?) \| ID: (.*?) ---\n(.*?)(?=\n--- MESSAGE #|\Z)",
    re.DOTALL,
)
_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_MENTION_RE = re.compile(r"@\[\[([0-9a-f\-]+)\]\]")


def humanise(text: str) -> str:
    """Make a room message human-readable: resolve mentions, drop the raw JSON
    record block and markdown emphasis, and collapse blank lines. Judges read
    prose, not JSON."""
    text = _MENTION_RE.sub(
        lambda m: MENTION_MAP.get(m.group(1), "@" + m.group(1)[:8]), text
    )
    text = _FENCE_RE.sub("", text)  # strip the embedded claim-record JSON
    text = text.replace("**", "")  # strip markdown bold markers
    text = re.sub(r"\n{2,}", "\n", text)  # collapse blank lines
    return text.strip()


def records_in(text: str) -> list[dict]:
    out = []
    for m in _FENCE_RE.finditer(text):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "claim_id" in data:
            out.append(data)
    return out


def parse_scenario(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    messages = []
    for n, sender, time, mid, body in _MSG_RE.findall(raw):
        messages.append(
            {
                "n": int(n),
                "sender": sender.strip(),
                "time": time.strip(),
                "content": humanise(body),
            }
        )
    all_records = records_in(raw)
    seed = all_records[0] if all_records else {}
    final = next(
        (r for r in reversed(all_records) if r.get("decision")), all_records[-1]
    )
    return {"claim": seed, "record": final, "messages": messages}


def main() -> None:
    scenarios = {}
    for key, meta in SCENARIOS.items():
        parsed = parse_scenario(EVIDENCE / meta["file"])
        decision = parsed["record"].get("decision") or {}
        scenarios[key] = {
            "key": key,
            "label": meta["label"],
            "blurb": meta["blurb"],
            "claim_id": parsed["record"].get("claim_id", ""),
            "outcome": decision.get("status", "UNKNOWN"),
            "reason": decision.get("reason", ""),
            "final_amount": decision.get("final_amount"),
            "claim": parsed["claim"],
            "record": parsed["record"],
            "messages": parsed["messages"],
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"agents": AGENTS, "scenarios": scenarios}, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    for key, sc in scenarios.items():
        print(
            f"  {key}: {sc['claim_id']} -> {sc['outcome']} ({len(sc['messages'])} msgs)"
        )


if __name__ == "__main__":
    main()
