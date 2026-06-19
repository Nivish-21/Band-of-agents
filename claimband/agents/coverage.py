"""Coverage agent — Gemini SDK adapter + Gemini (gemini-2.5-flash).

Determines policy coverage via genuine Gemini reasoning, then hands off to Fraud.
Guardrails catch any LLM violation of hard rules (can't approve an expired policy).
"""

import json
import os
import asyncio
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

import google.genai as genai

from band import Agent
from band.adapters import GeminiAdapter
from band.config import load_agent_config

from claimband.schema import ClaimRecord, CoverageBlock
from claimband.coverage import compute_coverage
from claimband.notes import gemini_note
from claimband.relay import make_relay_handler, serve

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "coverage.md"
with open(PROMPT_PATH, "r") as f:
    COVERAGE_PROMPT = f.read()

AGENT_NAME = "coverage"


def transform(record: ClaimRecord) -> ClaimRecord:
    record.coverage = compute_coverage(record)
    return record


def summary(record: ClaimRecord) -> str:
    block = record.coverage
    if block is None:
        return f"Coverage check incomplete for claim {record.claim_id}."
    if not block.policy_active:
        return "Policy is not active — claim not covered."
    if not block.peril_covered:
        return "Peril is not covered under this policy."
    return (
        f"Covered: ${block.covered_amount:,.0f} payable after "
        f"${block.deductible_applied:,} deductible."
    )


async def note_fn(record: ClaimRecord) -> str:
    return await gemini_note(
        f"Coverage determination result: {record.coverage.model_dump_json()}"
    )


async def judge(record: ClaimRecord) -> ClaimRecord:
    """Gemini reads the policy and determines coverage with reasoning.
    Falls back to the deterministic rule result on any failure.
    """
    prompt = (
        f"You are a Coverage Agent for auto insurance. Read the policy and claim, then "
        f"determine the coverage amount. Show your reasoning step by step, then output "
        f"the result as a JSON object.\n\n"
        f"Claim: {record.claim_id}\n"
        f"Policy: {record.policy.status}, {record.policy.effective_date} to "
        f"{record.policy.expiry_date}\n"
        f"Incident: {record.incident.date}, type={record.incident.type}\n"
        f"Collision covered: {record.policy.coverage.collision}\n"
        f"Limit: ${record.policy.coverage.liability_limit:,}, "
        f"Deductible: ${record.policy.coverage.deductible:,}\n"
        f"Estimate: ${record.damage.estimate_amount:,.0f}\n\n"
        f"Formula: covered = min(estimate, limit) - deductible. "
        f"Zero if policy expired or peril not covered.\n\n"
        f"---\n"
        f"Reason step by step, then end with this EXACT JSON (no markdown):\n"
        f'{{"policy_active":bool,"peril_covered":bool,"covered_amount":float,'
        f'"reasons":[string]}}'
    )
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)

        rule = compute_coverage(record)

        pol_active = bool(data.get("policy_active", rule.policy_active))
        peril_ok = bool(data.get("peril_covered", rule.peril_covered))
        cov_amount = max(0.0, float(data.get("covered_amount", rule.covered_amount)))
        reasons = list(data.get("reasons", rule.reasons))

        if not rule.policy_active:
            pol_active = False
            peril_ok = rule.peril_covered
            cov_amount = 0.0
            reasons = rule.reasons
            print("[coverage] Gemini overruled: policy expired — enforcing", flush=True)
        else:
            rule_max = rule.covered_amount
            if cov_amount > rule_max:
                print(
                    f"[coverage] Gemini capped: ${cov_amount:.0f} > ${rule_max:.0f}",
                    flush=True,
                )
                cov_amount = rule_max

        record.coverage = CoverageBlock(
            policy_active=pol_active,
            peril_covered=peril_ok,
            deductible_applied=rule.deductible_applied,
            covered_amount=cov_amount,
            reasons=reasons,
        )
    except Exception as exc:
        print(f"[coverage] Gemini judge failed ({exc}); using rule result", flush=True)
    return record


def _make_agent() -> Agent:
    agent_id, api_key = load_agent_config(AGENT_NAME)
    adapter = GeminiAdapter(
        model="gemini-2.5-flash",
        prompt=COVERAGE_PROMPT,
    )
    adapter.on_event = make_relay_handler(
        AGENT_NAME, agent_id, transform, summary, "coverage", note_fn, judge
    )
    return Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.environ["BAND_WS_URL"],
        rest_url=os.environ["BAND_REST_URL"],
    )


async def main() -> None:
    room_id = os.environ.get("BAND_ROOM_ID", "UNKNOWN")
    print("[Coverage] framework=Gemini-SDK vendor=Gemini", flush=True)
    print(f"[Coverage] connect OK - Room ID: {room_id}", flush=True)
    print("Starting Coverage Agent...", flush=True)
    await serve(AGENT_NAME, _make_agent)


if __name__ == "__main__":
    asyncio.run(main())
