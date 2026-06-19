"""One-command end-to-end ClaimBand demo runner.

Per fixture, with zero manual steps:
  fresh room -> 4 agents up -> seed claim -> wait for the live relay to finish
  -> capture the merged trail -> tear the agents down.

The relay itself is already autonomous (agents react to @mentions); this script only
removes the manual launch plumbing (create_new_room -> run_all -> seed -> dump -> kill).

Hard constraint: each agent holds ONE Band key, so it can be in only one room at a time.
`--all` therefore runs the three fixtures SEQUENTIALLY, each in its own fresh room — never
concurrently.

Usage:
  PYTHONPATH=. ./.venv/bin/python demo.py clean.json
  PYTHONPATH=. ./.venv/bin/python demo.py --all
  PYTHONPATH=. ./.venv/bin/python demo.py fraud.json --keep-up
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import sys
from asyncio.subprocess import PIPE, Process
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

import create_new_room
import dump_room_trail
import seed as seed_module

AGENTS: list[str] = ["intake", "coverage", "fraud", "adjudicator"]
FIXTURES: list[str] = ["clean.json", "deny.json", "fraud.json", "ambiguous.json"]

PREFLIGHT_TIMEOUT_S: float = 45.0
RELAY_TIMEOUT_S: float = 200.0
TEARDOWN_GRACE_S: float = 5.0

CONNECT_MARKER: str = "connect OK - Room ID:"
ADJUDICATOR_DONE_MARKER: str = "[adjudicator] handoff ->"

EVIDENCE_DIR: Path = Path("docs/evidence")
CLAIMS_DIR: Path = Path("claims")

_DECISION_RE = re.compile(r'"status":\s*"(APPROVE|DENY|ESCALATE)"')


# --------------------------------------------------------------------------- #
# Pure helpers (unit-tested in tests/test_demo.py)
# --------------------------------------------------------------------------- #
def parse_cli(args: list[str]) -> tuple[list[str], bool]:
    """Resolve CLI args into (fixture filenames, keep_up). Pure — no filesystem.

    ``--all`` expands to every fixture; bare names get a ``.json`` suffix.
    """
    keep_up = "--keep-up" in args
    if "--all" in args:
        return list(FIXTURES), keep_up
    positional = [a for a in args if not a.startswith("-")]
    if not positional:
        raise ValueError("need a fixture name (e.g. clean.json) or --all")
    fixtures = [a if a.endswith(".json") else f"{a}.json" for a in positional]
    return fixtures, keep_up


def extract_room_id(text: str) -> Optional[str]:
    """Return the room id from an agent ``connect OK`` line, else None."""
    if CONNECT_MARKER in text:
        return text.split(CONNECT_MARKER, 1)[1].strip()
    return None


def line_signals_done(text: str) -> bool:
    """True when the adjudicator has emitted its terminal handoff (relay complete)."""
    return ADJUDICATOR_DONE_MARKER in text


def extract_decision(trail: str) -> Optional[str]:
    """Return the first decision status (APPROVE/DENY/ESCALATE) found in a trail."""
    match = _DECISION_RE.search(trail)
    return match.group(1) if match else None


# --------------------------------------------------------------------------- #
# Live orchestration
# --------------------------------------------------------------------------- #
async def _stream_reader(
    name: str, stream: asyncio.StreamReader, queue: "asyncio.Queue[str]"
) -> None:
    """Print each agent line live and push it onto the shared queue for marker logic."""
    while True:
        raw = await stream.readline()
        if not raw:
            break
        text = raw.decode("utf-8", "replace").rstrip()
        print(f"[{name}] {text}", flush=True)
        await queue.put(text)


async def _await_preflight(queue: "asyncio.Queue[str]", expected_room: str) -> bool:
    """Block until all agents report ``connect OK`` on ``expected_room``, or timeout."""

    async def _loop() -> bool:
        seen = 0
        mismatched = False
        while seen < len(AGENTS):
            text = await queue.get()
            room_id = extract_room_id(text)
            if room_id is not None:
                seen += 1
                if room_id != expected_room:
                    mismatched = True
                    print(
                        f"[demo] ERROR: agent joined {room_id}, expected {expected_room}",
                        flush=True,
                    )
        return not mismatched

    try:
        return await asyncio.wait_for(_loop(), PREFLIGHT_TIMEOUT_S)
    except asyncio.TimeoutError:
        print("[demo] ERROR: pre-flight timed out", flush=True)
        return False


async def _await_relay_done(queue: "asyncio.Queue[str]") -> bool:
    """Block until the adjudicator's terminal handoff is seen, or timeout.

    A Gemini 429 on the coverage note is expected and non-fatal — the relay
    falls back to a template note and still completes, so we keep waiting.
    """

    async def _loop() -> bool:
        while True:
            text = await queue.get()
            if line_signals_done(text):
                return True

    try:
        return await asyncio.wait_for(_loop(), RELAY_TIMEOUT_S)
    except asyncio.TimeoutError:
        print("[demo] ERROR: relay did not complete in time", flush=True)
        return False


async def _launch_agents(
    queue: "asyncio.Queue[str]",
) -> tuple[list[Process], list[asyncio.Task[None]]]:
    """Start the 4 agent subprocesses, streaming their output into ``queue``."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    procs: list[Process] = []
    readers: list[asyncio.Task[None]] = []
    for name in AGENTS:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            f"claimband/agents/{name}.py",
            stdout=PIPE,
            stderr=PIPE,
            env=env,
        )
        procs.append(proc)
        assert proc.stdout is not None and proc.stderr is not None
        readers.append(asyncio.create_task(_stream_reader(name, proc.stdout, queue)))
        readers.append(asyncio.create_task(_stream_reader(name, proc.stderr, queue)))
    return procs, readers


async def _teardown(procs: list[Process], readers: list[asyncio.Task[None]]) -> None:
    """Terminate all agent subprocesses (so none are orphaned) and cancel readers."""
    for proc in procs:
        if proc.returncode is None:
            proc.terminate()
    for proc in procs:
        if proc.returncode is None:
            try:
                await asyncio.wait_for(proc.wait(), TEARDOWN_GRACE_S)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
    for task in readers:
        task.cancel()
    await asyncio.gather(*readers, return_exceptions=True)


async def run_fixture(fixture: str, keep_up: bool) -> bool:
    """Run one fixture end-to-end. Returns True only on a captured, decided trail."""
    if not (CLAIMS_DIR / fixture).exists():
        print(f"[demo] ERROR: fixture not found: {CLAIMS_DIR / fixture}", flush=True)
        return False

    print(f"\n[demo] === {fixture}: creating fresh room ===", flush=True)
    room_id = await create_new_room.main()
    load_dotenv(override=True)  # pick up the new BAND_ROOM_ID for seed + dump

    queue: "asyncio.Queue[str]" = asyncio.Queue()
    procs, readers = await _launch_agents(queue)

    try:
        if not await _await_preflight(queue, room_id):
            print(f"[demo] {fixture}: PRE-FLIGHT FAILED", flush=True)
            return False
        print(f"[demo] {fixture}: PRE-FLIGHT OK on room {room_id}", flush=True)

        await seed_module.main(fixture)
        print(f"[demo] {fixture}: seeded; waiting for the relay...", flush=True)

        completed = await _await_relay_done(queue)

        trail = await dump_room_trail.build_trail(room_id)
        out_path = EVIDENCE_DIR / f"dr3-{Path(fixture).stem}.txt"
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(trail, encoding="utf-8")

        decision = extract_decision(trail)
        md5 = hashlib.md5(out_path.read_bytes()).hexdigest()
        status = "OK" if (completed and decision is not None) else "INCOMPLETE"
        print(
            f"[demo] {fixture} -> {decision or 'NO-DECISION'} "
            f"[{status}] (room {room_id}, md5 {md5}) -> {out_path}",
            flush=True,
        )
        return completed and decision is not None and bool(trail.strip())
    finally:
        if keep_up:
            print(f"[demo] {fixture}: leaving agents up (--keep-up)", flush=True)
        else:
            await _teardown(procs, readers)


async def run(fixtures: list[str], keep_up: bool) -> int:
    """Run each fixture sequentially. Returns a process exit code (0 = all passed)."""
    results: dict[str, bool] = {}
    for fixture in fixtures:
        results[fixture] = await run_fixture(fixture, keep_up)

    print("\n[demo] === summary ===", flush=True)
    for fixture, ok in results.items():
        print(f"[demo]   {fixture}: {'PASS' if ok else 'FAIL'}", flush=True)
    return 0 if all(results.values()) else 1


def main() -> None:
    try:
        fixtures, keep_up = parse_cli(sys.argv[1:])
    except ValueError as exc:
        print(f"usage: demo.py <fixture.json> | --all  [--keep-up]\n  {exc}")
        sys.exit(2)
    sys.exit(asyncio.run(run(fixtures, keep_up)))


if __name__ == "__main__":
    main()
