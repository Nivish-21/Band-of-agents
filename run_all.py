import os
import sys
import asyncio
from asyncio.subprocess import Process, PIPE

AGENTS = ["intake", "coverage", "fraud", "adjudicator"]


async def run_agent(agent_name: str, room_ids: dict):
    # Pass PYTHONPATH=. to the environment
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    cmd = [sys.executable, f"claimband/agents/{agent_name}.py"]

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=PIPE, stderr=PIPE, env=env
    )

    async def read_stream(stream, prefix):
        while True:
            line = await stream.readline()
            if not line:
                break
            line_str = line.decode("utf-8").rstrip()
            print(f"{prefix} {line_str}", flush=True)

            # Check for room ID assertion
            if "connect OK - Room ID:" in line_str:
                parts = line_str.split("connect OK - Room ID:")
                if len(parts) > 1:
                    room_id = parts[1].strip()
                    room_ids[agent_name] = room_id

    await asyncio.gather(
        read_stream(process.stdout, f"[{agent_name}]"),
        read_stream(process.stderr, f"[{agent_name}]"),
    )
    await process.wait()
    print(f"[{agent_name}] process exited with code {process.returncode}")


async def main():
    room_ids = {}
    tasks = []

    print("Starting all agents...")
    for agent in AGENTS:
        tasks.append(asyncio.create_task(run_agent(agent, room_ids)))

    # Wait a bit to let them start and print their connection lines
    await asyncio.sleep(5)

    # Assert room IDs
    if not room_ids:
        print("ERROR: No agents reported a Room ID. Aborting.", flush=True)
        sys.exit(1)

    first_room_id = next(iter(room_ids.values()))
    if first_room_id == "UNKNOWN" or first_room_id == "None":
        print(f"ERROR: BAND_ROOM_ID is unset or UNKNOWN. Aborting.", flush=True)
        sys.exit(1)

    for agent, rid in room_ids.items():
        if rid != first_room_id:
            print(
                f"ERROR: Mismatched Room IDs! {agent} joined {rid}, expected {first_room_id}. Aborting.",
                flush=True,
            )
            sys.exit(1)

    print(
        f"\n✅ PRE-FLIGHT OK: All agents joined Room ID: {first_room_id}\n", flush=True
    )

    # Let them run
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
