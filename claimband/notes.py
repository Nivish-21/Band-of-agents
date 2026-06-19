"""Best-effort one-line LLM reasoning notes per vendor (see D13).

These are flavour only: the relay's data path is deterministic. Each note is a
short natural-language sentence explaining the agent's finding. Any failure
(rate limit, network, bad output) is the caller's concern — the relay falls
back to a deterministic template when a note call raises.

- Groq (LangGraph/CrewAI agents): intake, fraud, adjudicator.
- Gemini (Gemini SDK agent): coverage.
"""

from __future__ import annotations

import asyncio
import os
import re

from openai import AsyncOpenAI

# Note model is non-reasoning on purpose: gpt-oss-120b spends its token budget
# on hidden reasoning and returns empty visible content for tiny prompts.
_GROQ_MODEL = "llama-3.3-70b-versatile"
_GEMINI_MODEL = "gemini-2.5-flash-lite"
_MAX_TOKENS = 80

_SYSTEM = (
    "You are an insurance claim agent. In ONE concise sentence (max 25 words), "
    "explain your finding for a colleague. No preamble, no JSON, just the sentence."
)


async def groq_note(prompt: str) -> str:
    """Return a one-line note from Groq, or raise on failure."""
    client = AsyncOpenAI(
        base_url=os.environ["GROQ_BASE_URL"],
        api_key=os.environ["GROQ_API_KEY"],
    )
    resp = await client.chat.completions.create(
        model=_GROQ_MODEL,
        temperature=0,
        max_tokens=_MAX_TOKENS,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or ""


_NARRATIVE_SYSTEM = (
    "You are an auto-insurance fraud analyst. Judge ONLY narrative/contextual "
    "fraud signals that simple field rules CANNOT see: a story inconsistent with "
    "the damage or amount, an implausible or vague description, severity that "
    "doesn't match the claimed sum. Reply on ONE line, exactly:\n"
    "RISK=<integer 0-40> | <reason in <=20 words>\n"
    "0 means the narrative is plausible and consistent; 40 means strong narrative "
    "fraud signals. This is ADDED on top of rule-based red flags."
)

_RISK_RE = re.compile(r"RISK\s*=\s*(\d+)\s*\|\s*(.*)", re.IGNORECASE | re.DOTALL)


def _parse_narrative_risk_response(text: str) -> tuple[int, str]:
    """Parse the Groq narrative-risk response into a bounded score and rationale."""
    match = _RISK_RE.search(text.strip())
    if not match:
        return 0, ""
    try:
        risk = int(match.group(1))
    except ValueError:
        return 0, ""
    return max(0, min(40, risk)), match.group(2).strip()


async def groq_narrative_risk(claim_summary: str) -> tuple[int, str]:
    """LLM narrative fraud judgment (Groq): returns (narrative_risk 0-40, rationale).

    This is the agent genuinely deciding something the deterministic rules can't —
    reading the free-text story. Returns (0, "") on any failure so the relay falls
    back cleanly to the rule-only score.
    """
    client = AsyncOpenAI(
        base_url=os.environ["GROQ_BASE_URL"],
        api_key=os.environ["GROQ_API_KEY"],
    )
    resp = await client.chat.completions.create(
        model=_GROQ_MODEL,
        temperature=0,
        max_tokens=120,
        messages=[
            {"role": "system", "content": _NARRATIVE_SYSTEM},
            {"role": "user", "content": claim_summary},
        ],
    )
    text = resp.choices[0].message.content or ""
    return _parse_narrative_risk_response(text)


async def gemini_note(prompt: str) -> str:
    """Return a one-line note from Gemini, or raise on failure."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def _call() -> str:
        resp = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=f"{_SYSTEM}\n\n{prompt}",
        )
        return resp.text or ""

    return await asyncio.to_thread(_call)
