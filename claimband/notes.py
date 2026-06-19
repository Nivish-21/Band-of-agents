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
    from openai import AsyncOpenAI

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
