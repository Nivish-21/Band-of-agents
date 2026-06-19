"""Offline tests for the deterministic relay engine (D13).

Runs the full Intake -> Coverage -> Fraud -> Adjudicator chain using
FakeAgentTools, with note_fn disabled (no network / LLM). Asserts each hop
extracts the record, applies its block, and hands off to the right agent.
"""

import asyncio
import json
import re
from types import SimpleNamespace

from band.testing.fake_tools import FakeAgentTools

from claimband.relay import make_relay_handler, HANDLES, extract_latest_record
from claimband.agents import intake, coverage, fraud, adjudicator

_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _make_inp(content: str, tools: FakeAgentTools) -> SimpleNamespace:
    msg = SimpleNamespace(
        content=content, metadata={}, sender_type="Agent", sender_id="seed"
    )
    history = SimpleNamespace(raw=[])
    return SimpleNamespace(msg=msg, history=history, tools=tools)


def _record_from_message(content: str) -> dict:
    match = _FENCE.search(content)
    assert match is not None, f"no JSON block in: {content[:120]}"
    return json.loads(match.group(1))


def _load_fixture(name: str) -> str:
    with open(f"claims/{name}", "r") as handle:
        data = json.load(handle)
    return f"@{HANDLES['intake']} new claim:\n```json\n{json.dumps(data)}\n```"


async def _run_chain(seed_content: str) -> list[dict]:
    """Run all four hops; return the list of messages posted to the room."""
    posted: list[dict] = []
    stages = [
        ("intake", intake, HANDLES["coverage"], "intake"),
        ("coverage", coverage, HANDLES["fraud"], "coverage"),
        ("fraud", fraud, HANDLES["adjudicator"], "fraud"),
        ("adjudicator", adjudicator, HANDLES["human"], "decision"),
    ]
    content = seed_content
    for name, module, expected_mention, block in stages:
        tools = FakeAgentTools()
        handler = make_relay_handler(
            name, f"id-{name}", module.transform, module.summary, block, note_fn=None
        )
        await handler(_make_inp(content, tools))
        assert len(tools.messages_sent) == 1, f"{name} did not post exactly one message"
        sent = tools.messages_sent[0]
        assert (
            expected_mention in sent["mentions"]
        ), f"{name} mentioned {sent['mentions']}, expected {expected_mention}"
        posted.append(sent)
        content = sent["content"]
    return posted


def test_clean_claim_approves():
    posted = asyncio.run(_run_chain(_load_fixture("clean.json")))
    final = _record_from_message(posted[-1]["content"])
    assert final["intake"]["is_valid"] is True
    assert final["coverage"]["policy_active"] is True
    assert final["decision"]["status"] == "APPROVE"


def test_deny_claim_denies():
    posted = asyncio.run(_run_chain(_load_fixture("deny.json")))
    final = _record_from_message(posted[-1]["content"])
    assert final["decision"]["status"] == "DENY"


def test_fraud_claim_escalates():
    posted = asyncio.run(_run_chain(_load_fixture("fraud.json")))
    final = _record_from_message(posted[-1]["content"])
    assert final["decision"]["status"] == "ESCALATE"
    # terminal hop must loop in the human
    assert HANDLES["human"] in posted[-1]["mentions"]


def test_mention_gating_skips_unaddressed():
    async def run() -> FakeAgentTools:
        tools = FakeAgentTools()
        handler = make_relay_handler(
            "coverage",
            "id-coverage",
            coverage.transform,
            coverage.summary,
            "coverage",
            note_fn=None,
        )
        # message addressed to fraud, not coverage -> coverage stays silent
        content = (
            f'@{HANDLES["fraud"]} please review\n```json\n{{"claim_id": "X"}}\n```'
        )
        await handler(_make_inp(content, tools))
        return tools

    tools = asyncio.run(run())
    assert tools.messages_sent == []


def test_extract_latest_record_prefers_newest():
    older = json.dumps({"claim_id": "OLD", "policy": {}})
    newer = json.dumps(
        {
            "claim_id": "NEW",
            "policy": {
                "policy_id": "P",
                "status": "active",
                "effective_date": "2026-01-01",
                "expiry_date": "2026-12-31",
                "coverage": {"collision": True, "liability_limit": 1, "deductible": 0},
            },
            "claimant": {"name": "A", "is_policy_holder": True, "prior_claims_12mo": 0},
            "incident": {
                "date": "2026-06-01",
                "type": "collision",
                "at_fault": "other_party",
                "police_report": True,
                "description": "x",
            },
            "damage": {"vehicle": "car", "estimate_amount": 1.0, "photos_count": 1},
            "amount_claimed": 1.0,
        }
    )
    texts = [f"```json\n{older}\n```", f"```json\n{newer}\n```"]
    record = extract_latest_record(texts)
    assert record is not None
    assert record.claim_id == "NEW"


def test_judge_fn_failure_keeps_rule_result():
    async def run() -> dict:
        tools = FakeAgentTools()

        async def boom(_record: object) -> object:
            raise RuntimeError("judge unavailable")

        handler = make_relay_handler(
            "fraud",
            "id-fraud",
            fraud.transform,
            fraud.summary,
            "fraud",
            note_fn=None,
            judge_fn=boom,
        )
        with open("claims/clean.json", "r") as handle:
            claim = json.load(handle)
        claim["incident"]["police_report"] = False
        content = (
            f'@{HANDLES["fraud"]} please re-score\n'
            f"```json\n{json.dumps(claim)}\n```"
        )
        await handler(_make_inp(content, tools))
        assert len(tools.messages_sent) == 1
        sent = tools.messages_sent[0]
        assert HANDLES["adjudicator"] in sent["mentions"]
        return _record_from_message(sent["content"])

    final = asyncio.run(run())
    assert final["fraud"]["rule_risk"] == 20
    assert final["fraud"]["narrative_risk"] == 0
    assert final["fraud"]["risk_score"] == 20
