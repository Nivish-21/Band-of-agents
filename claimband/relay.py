"""Deterministic relay engine for ClaimBand (see docs/decisions.md D13).

Each agent reads the latest claim record from the inbound Band message
(shared room context), runs its tested pure domain function, and hands off
to the next agent with a small structured message. The LLM produces a
one-line reasoning note (best-effort, templated fallback) but is NEVER on
the data path — deterministic Python copies the record, so large payloads
never depend on a model faithfully reproducing them.

SDK facts this relies on (verified in band-sdk source):
- Adapters implement ``on_event(inp: AgentInput)``. We override it.
- ``inp.msg`` is the triggering ``PlatformMessage`` (``.content``, ``.metadata``).
- ``inp.tools.send_message(content, mentions)`` takes handle strings and
  requires at least one mention.
- The default preprocessor does self-message filtering but NOT mention
  gating, so we gate on mention ourselves to enforce relay order.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Awaitable, Callable, Optional

from claimband.schema import ClaimRecord

# Owner-qualified handles (verified live from the room participants).
HANDLES: dict[str, str] = {
    "intake": "nivishnick2k/intake",
    "coverage": "nivishnick2k/coverage",
    "fraud": "nivishnick2k/fraud",
    "adjudicator": "nivishnick2k/adjudicator",
    "human": "nivishnick2k",
}

# Relay routing: each agent -> the next agent it hands off to.
NEXT_AGENT: dict[str, Optional[str]] = {
    "intake": "coverage",
    "coverage": "fraud",
    "fraud": "adjudicator",
    "adjudicator": None,  # terminal — hands off to the human
}

# Transform = pure function that returns an updated ClaimRecord.
Transform = Callable[[ClaimRecord], ClaimRecord]
# Summary = deterministic one-line description (template fallback for the note).
Summary = Callable[[ClaimRecord], str]
# NoteFn = optional async vendor LLM call producing a one-line reasoning note.
NoteFn = Callable[[ClaimRecord], Awaitable[str]]
# ReprocessFn = optional callback that allows one more pass for a populated block.
ReprocessFn = Callable[[ClaimRecord, object], bool]
# PreActionFn = optional async hook that can emit a discovery/recruitment event
# before the current agent finishes its turn. Returning False stops the turn.
PreActionFn = Callable[[ClaimRecord, object], Awaitable[bool]]

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_latest_record(texts: list[str]) -> Optional[ClaimRecord]:
    """Return the most recent valid claim record found in ``texts``.

    Scans newest-first for a fenced JSON object containing ``claim_id``.
    Purely deterministic — no LLM, so the payload round-trips exactly.
    """
    for text in reversed(texts):
        if not text:
            continue
        for match in _FENCE_RE.finditer(text):
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and "claim_id" in data:
                try:
                    return ClaimRecord.model_validate(data)
                except Exception:
                    continue
    return None


def collect_texts(inp: object) -> list[str]:
    """All candidate message texts: bootstrap history first, then the trigger."""
    texts: list[str] = []
    history = getattr(inp, "history", None)
    raw = getattr(history, "raw", None) or []
    for entry in raw:
        content = entry.get("content") if isinstance(entry, dict) else None
        if content:
            texts.append(content)
    msg = getattr(inp, "msg", None)
    content = getattr(msg, "content", None) if msg is not None else None
    if content:
        texts.append(content)
    return texts


def is_addressed_to(inp: object, agent_id: str, agent_handle: str) -> bool:
    """True if this agent is mentioned in the triggering message.

    Checks structured ``metadata.mentions`` first (by id/username/handle/name),
    then falls back to the rendered ``@handle`` appearing in the content.
    """
    msg = getattr(inp, "msg", None)
    if msg is None:
        return False

    metadata = getattr(msg, "metadata", None)
    mentions: list[object] = []
    if isinstance(metadata, dict):
        mentions = metadata.get("mentions") or []
    elif metadata is not None:
        mentions = getattr(metadata, "mentions", None) or []

    targets = {agent_id, agent_handle, agent_handle.lstrip("@")}
    for mention in mentions:
        if isinstance(mention, dict):
            values = {
                str(mention.get(k))
                for k in ("id", "username", "handle", "name")
                if mention.get(k)
            }
        else:
            values = {
                str(getattr(mention, k))
                for k in ("id", "username", "handle", "name")
                if getattr(mention, k, None)
            }
        if targets & values:
            return True

    content = getattr(msg, "content", "") or ""
    return agent_handle.lstrip("@") in content


def _format_record_block(record: ClaimRecord) -> str:
    return "```json\n" + record.model_dump_json(indent=2) + "\n```"


async def _safe_send(
    tools: object, agent_name: str, content: str, mentions: list[str]
) -> None:
    """Send a message, tolerating rooms where a mention can't be resolved.

    The platform replays an agent's undelivered @mentions across ALL its rooms
    on connect; some legacy rooms lack the next participant. Those handoffs
    can't succeed and must not crash the live relay — log and skip.
    """
    try:
        await tools.send_message(content, mentions=mentions)
    except ValueError as exc:
        print(f"[{agent_name}] skip handoff (mention unresolved): {exc}", flush=True)


async def serve(agent_name: str, make_agent: Callable[[], object]) -> None:
    """Keep an agent connected across disconnects.

    The platform issues a *terminal* WebSocket close (e.g. idle/replaced) for
    which the SDK disables auto-reconnect and ``agent.run()`` returns. We rebuild
    a fresh agent and reconnect; with the backlog intact, a reconnect picks up
    any pending @mention and the relay completes. Backoff avoids tight thrash.
    """
    while True:
        try:
            agent = make_agent()
            await agent.run()
            print(f"[{agent_name}] run() returned (disconnected)", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[{agent_name}] run error: {exc}", flush=True)
        print(f"[{agent_name}] reconnecting in 3s...", flush=True)
        await asyncio.sleep(3)


def make_relay_handler(
    agent_name: str,
    agent_id: str,
    transform: Transform,
    summary: Summary,
    block_attr: str,
    note_fn: Optional[NoteFn] = None,
    judge_fn: Optional[Callable[[ClaimRecord], Awaitable[ClaimRecord]]] = None,
    reprocess_if: Optional[ReprocessFn] = None,
    pre_action_fn: Optional[PreActionFn] = None,
):
    """Build a deterministic ``on_event`` handler for one relay agent.

    ``block_attr`` is the ClaimRecord field this agent populates (e.g. "intake",
    "decision"). If it is already set on the inbound record, the agent has
    nothing to do — it skips. This makes the relay idempotent: redelivered
    backlog messages and the broadcast final decision cannot restart the chain.
    """
    agent_handle = HANDLES[agent_name]
    next_name = NEXT_AGENT.get(agent_name)

    async def on_event(inp: object) -> None:
        if not is_addressed_to(inp, agent_id, agent_handle):
            print(f"[{agent_name}] message not addressed to me; skipping", flush=True)
            return

        record = extract_latest_record(collect_texts(inp))
        if record is None:
            print(f"[{agent_name}] no claim record in context; skipping", flush=True)
            return

        if getattr(record, block_attr) is not None and not (
            reprocess_if is not None and reprocess_if(record, inp)
        ):
            print(
                f"[{agent_name}] claim {record.claim_id} already has '{block_attr}'; skipping",
                flush=True,
            )
            return

        if pre_action_fn is not None:
            try:
                should_continue = await pre_action_fn(record, inp)
            except Exception as exc:
                print(
                    f"[{agent_name}] pre-action failed ({exc}); continuing",
                    flush=True,
                )
                should_continue = True
            if not should_continue:
                return

        print(f"[{agent_name}] processing claim {record.claim_id}", flush=True)
        try:
            record = transform(record)
        except Exception as exc:  # surface to the room, do not crash the process
            await _safe_send(
                inp.tools,
                agent_name,
                f"**{agent_name.capitalize()} Agent** — error: {exc}",
                [HANDLES["human"]],
            )
            return

        # Optional async LLM judgment that materially updates the record. The
        # deterministic transform above is the floor/guardrail; this lets the
        # model contribute a real decision (e.g. reading the incident narrative).
        # Any failure falls back to the deterministic result.
        if judge_fn is not None:
            try:
                record = await judge_fn(record)
            except Exception as exc:
                print(
                    f"[{agent_name}] judge LLM failed ({exc}); using rule result",
                    flush=True,
                )

        note = ""
        if note_fn is not None:
            try:
                note = (await note_fn(record)).strip()
            except Exception as exc:
                print(
                    f"[{agent_name}] note LLM failed ({exc}); using template",
                    flush=True,
                )
        if not note:
            note = summary(record)

        header = f"**{agent_name.capitalize()} Agent** — {note}"
        body = _format_record_block(record)

        if next_name is not None:
            next_handle = HANDLES[next_name]
            content = f"{header}\n\nHanding off to @{next_handle} for the next step.\n\n{body}"
            mentions = [next_handle]
        else:
            decision = record.decision
            status = decision.status if decision is not None else "UNKNOWN"
            if status == "ESCALATE":
                content = (
                    f"{header}\n\n@{HANDLES['human']} this claim is **ESCALATED** for "
                    f"human review.\n\n{body}"
                )
            else:
                content = f"{header}\n\nFinal decision: **{status}**.\n\n{body}"
            # Broadcast the verdict to the whole band (human + peers). Safe from
            # re-triggering the relay: every peer's block is already populated,
            # so the idempotency guard makes them skip.
            mentions = [
                HANDLES["human"],
                HANDLES["intake"],
                HANDLES["coverage"],
                HANDLES["fraud"],
            ]

        print(f"[{agent_name}] handoff -> {mentions}", flush=True)
        await _safe_send(inp.tools, agent_name, content, mentions)

    return on_event
