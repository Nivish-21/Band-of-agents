"""Adjudicator agent — CrewAI adapter + Groq (groq/openai/gpt-oss-120b, see D12).

Produces the final APPROVE / DENY / ESCALATE decision via LLM reasoning over
all three peer findings. Deterministic rules serve as guardrails (not decision-
makers): the LLM decides, but hard constraints (expired policy → DENY,
risk≥60 → ESCALATE) are enforced as overrides.
"""

import json
import os
import asyncio
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from band import Agent
from band.adapters import CrewAIAdapter
from band.config import load_agent_config
from langchain_openai import ChatOpenAI

from claimband.schema import ClaimRecord, DecisionBlock
from claimband.adjudication import adjudicate_claim
from claimband.notes import groq_note
from claimband.relay import HANDLES, make_relay_handler, serve

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "adjudicator.md"
with open(PROMPT_PATH, "r") as f:
    ADJUDICATOR_BACKSTORY = f.read()

AGENT_NAME = "adjudicator"


def transform(record: ClaimRecord) -> ClaimRecord:
    record.decision = adjudicate_claim(record)
    return record


def summary(record: ClaimRecord) -> str:
    block = record.decision
    if block is None:
        return f"No decision reached for claim {record.claim_id}."
    if block.status == "APPROVE":
        return f"APPROVE — ${block.final_amount:,.0f} payable. {block.reason}"
    return f"{block.status} — {block.reason}"


async def note_fn(record: ClaimRecord) -> str:
    return await groq_note(
        f"Adjudication decision: {record.decision.model_dump_json()}"
    )


async def judge(record: ClaimRecord) -> ClaimRecord:
    """Groq reads all three peer findings and decides with reasoning.
    Falls back to deterministic rules on failure.
    """
    peers = []
    if record.intake:
        peers.append(
            f"INTAKE: valid={record.intake.is_valid}, "
            f"completeness={record.intake.completeness_score}%, "
            f"issues={record.intake.inconsistencies or 'none'}"
        )
    if record.coverage:
        peers.append(
            f"COVERAGE: active={record.coverage.policy_active}, "
            f"peril_covered={record.coverage.peril_covered}, "
            f"covered=${record.coverage.covered_amount:,.0f}"
        )
    if record.fraud:
        flags = "; ".join(record.fraud.red_flags) if record.fraud.red_flags else "none"
        peers.append(
            f"FRAUD: risk_score={record.fraud.risk_score}/100, "
            f"flags=[{flags}], "
            f'model_note="{record.fraud.narrative_rationale}"'
        )

    prompt = (
        f"You are the Claims Adjudicator. Three specialists have analyzed this "
        f"auto insurance claim. Read their findings and decide.\n\n"
        f"Claim: {record.claim_id}\n"
        f"Policy: {record.policy.status}, expires {record.policy.expiry_date}\n"
        f"Incident: {record.incident.date}, {record.incident.type}\n"
        f"Estimate: ${record.damage.estimate_amount:,.0f}, "
        f"Deductible: ${record.policy.coverage.deductible:,}\n\n"
        f"Findings:\n" + "\n".join(f"  {p}" for p in peers) + "\n\n"
        f"HARD RULES (enforced as guardrails — do not violate):\n"
        f"1. If policy is NOT active on incident date → DENY\n"
        f"2. If risk_score >= 60 OR covered_amount > 10000 → ESCALATE\n"
        f"3. Otherwise → APPROVE with final_amount = covered_amount\n\n"
        f"Think step by step about what each specialist found and why, "
        f"then decide.\n\n"
        f"End with this EXACT JSON (no markdown):\n"
        f'{{"status":"APPROVE"|"DENY"|"ESCALATE","reason":"<your reasoning>",'
        f'"final_amount":<number>}}'
    )
    try:
        llm = ChatOpenAI(
            model="openai/gpt-oss-120b",
            base_url=os.environ["GROQ_BASE_URL"],
            api_key=os.environ["GROQ_API_KEY"],
            temperature=0.3,
        )
        resp = await llm.ainvoke(prompt)
        text = resp.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)

        status = str(data.get("status", "APPROVE"))
        reason = str(data.get("reason", ""))
        final_amount = float(data.get("final_amount", 0))

        risk = record.fraud.risk_score if record.fraud else 0
        cov_amt = record.coverage.covered_amount if record.coverage else 0
        pol_ok = bool(record.coverage.policy_active) if record.coverage else True

        must_deny = not pol_ok
        must_escalate = risk >= 60 or cov_amt > 10000

        if must_deny and status != "DENY":
            status = "DENY"
            reason = f"OVERRIDE: {reason} — policy is inactive."
            final_amount = 0.0
            print(
                "[adjudicator] LLM overruled: enforcing DENY (policy inactive)",
                flush=True,
            )
        elif must_escalate and status != "ESCALATE":
            status = "ESCALATE"
            reason = (
                f"OVERRIDE: {reason} — escalation threshold "
                f"(risk={risk}, amount=${cov_amt:,.0f}) was met."
            )
            final_amount = cov_amt
            print(
                "[adjudicator] LLM overruled: enforcing ESCALATE (threshold met)",
                flush=True,
            )
        elif not must_deny and not must_escalate and status == "DENY":
            print("[adjudicator] LLM denied a clean claim (allowed)", flush=True)
            final_amount = 0.0

        record.decision = DecisionBlock(
            status=status, reason=reason, final_amount=final_amount
        )
    except Exception as exc:
        print(f"[adjudicator] Groq judge failed ({exc}); using rule result", flush=True)
    return record


def _needs_peer_discovery(record: ClaimRecord) -> bool:
    block = record.fraud
    if block is None:
        return True
    if block.discovery_round > 0:
        return False
    return 40 <= block.risk_score <= 60


def _peer_items(response: object) -> list[object]:
    if isinstance(response, dict):
        data = response.get("peers") or response.get("data") or []
        return list(data)
    data = getattr(response, "data", None)
    if data is not None:
        return list(data)
    if isinstance(response, list):
        return list(response)
    return []


def _peer_identifier(peer: object) -> str | None:
    if isinstance(peer, dict):
        return (
            peer.get("id")
            or peer.get("handle")
            or peer.get("name")
            or peer.get("username")
        )
    return (
        getattr(peer, "id", None)
        or getattr(peer, "handle", None)
        or getattr(peer, "name", None)
        or getattr(peer, "username", None)
    )


async def _peer_discovery(record: ClaimRecord, inp: object) -> bool:
    """Recruit Fraud via Band discovery when the score is ambiguous or missing."""
    if not _needs_peer_discovery(record):
        return True

    if record.fraud is not None:
        record.fraud.discovery_round = 1

    peers_response = await inp.tools.lookup_peers()
    peer_identifier = None
    for peer in _peer_items(peers_response):
        identifier = _peer_identifier(peer)
        if not identifier:
            continue
        lowered = identifier.lower()
        if (
            lowered.endswith("/fraud")
            or lowered.endswith("@fraud")
            or lowered == "fraud"
        ):
            peer_identifier = identifier
            break

    await inp.tools.add_participant(peer_identifier or HANDLES["fraud"])

    if record.fraud is None:
        summary_text = (
            f"**{AGENT_NAME.capitalize()} Agent** — Fraud block missing; "
            "requesting a peer-discovery recheck."
        )
    else:
        summary_text = (
            f"**{AGENT_NAME.capitalize()} Agent** — Ambiguous fraud risk "
            f"({record.fraud.risk_score}/100); requesting a peer-discovery recheck."
        )

    body = "```json\n" + record.model_dump_json(indent=2) + "\n```"
    content = (
        f"{summary_text}\n\n"
        f"@{HANDLES['fraud']} please double-check this claim before I decide.\n\n"
        f"{body}"
    )
    await inp.tools.send_message(content, mentions=[HANDLES["fraud"]])
    print(f"[{AGENT_NAME}] peer discovery -> {HANDLES['fraud']}", flush=True)
    return False


async def _skip_crew_init(*_args, **_kwargs) -> None:
    # The deterministic relay overrides on_event, so the CrewAI crew/LLM is
    # never invoked. Skip its on_started LLM init (which needs litellm for
    # groq/* models) — we only use this adapter for Band identity + transport.
    return None


def _make_agent() -> Agent:
    agent_id, api_key = load_agent_config(AGENT_NAME)
    adapter = CrewAIAdapter(
        model="groq/openai/gpt-oss-120b",
        role="Claims Adjudicator",
        goal="Decide APPROVE/DENY/ESCALATE from peer findings",
        backstory=ADJUDICATOR_BACKSTORY,
    )
    adapter.on_event = make_relay_handler(
        AGENT_NAME,
        agent_id,
        transform,
        summary,
        "decision",
        note_fn,
        judge,
        pre_action_fn=_peer_discovery,
    )
    adapter.on_started = _skip_crew_init
    return Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.environ["BAND_WS_URL"],
        rest_url=os.environ["BAND_REST_URL"],
    )


async def main() -> None:
    room_id = os.environ.get("BAND_ROOM_ID", "UNKNOWN")
    print("[Adjudicator] framework=CrewAI vendor=Groq", flush=True)
    print(f"[Adjudicator] connect OK - Room ID: {room_id}", flush=True)
    print("Starting Adjudicator Agent...", flush=True)
    await serve(AGENT_NAME, _make_agent)


if __name__ == "__main__":
    asyncio.run(main())
