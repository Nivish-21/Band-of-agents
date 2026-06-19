# Gemini — Phase 6b (real evidence + submission assets)

Paste the block below into Gemini. Context: it is running unattended (YOLO) and previously marked
Phase 6 "complete" without valid proof.

```
You are running unattended with auto-approval. Obey the UNATTENDED / AUTONOMOUS guardrails in GEMINI.md:
no git push, no deletions (rooms/messages/files), no global installs, stay inside this project, and do
NOT mark anything "done" or "verified" without real saved evidence.

YOUR LAST RUN OVER-CLAIMED. You set docs/status.md to "Phase 6 complete, fraud -> ESCALATE verified,"
but the evidence does not hold:
- docs/evidence/dr3-clean.txt, dr3-deny.txt, dr3-fraud.txt are BYTE-IDENTICAL (same md5 7399554b...).
  They are one full room dump copied 3x, not per-fixture trails.
- No ESCALATE decision appears in the fraud evidence.
So fraud -> ESCALATE is NOT verified. Redo the evidence properly before claiming anything.

DO THIS, IN ORDER. Report after each step with concrete output (paths, md5s, the decision line).

1) RE-VERIFY ALL 3 FIXTURES WITH CLEAN, DISTINCT EVIDENCE.
   For EACH fixture (clean.json, deny.json, fraud.json), to avoid mixing claims in one room:
   a. python create_new_room.py   (this updates BAND_ROOM_ID in .env to a fresh room)
   b. Launch the agents as a directly-tracked process (do NOT background with `&` inside a wrapper —
      the harness reaps the orphan and the agents die silently):  PYTHONPATH=. ./.venv/bin/python run_all.py
   c. Confirm 4x "connect OK" on the SAME room id + "PRE-FLIGHT OK".
   d. python seed.py <fixture>
   e. Wait for the full 5-message relay (seed -> Intake -> Coverage -> Fraud -> Adjudicator decision).
   f. Capture ONLY that room's MERGED trail (union of all 4 agent keys via list_agent_messages,
      deduped by message id, sorted by inserted_at) to docs/evidence/dr3-<fixture>.txt.
      The adjudicator's verdict is only visible because it is broadcast to all agents (see D14.3).
   Each file MUST show its own claim_id only and the correct final decision:
     - clean.json -> APPROVE, final_amount 3700
     - deny.json  -> DENY (policy expired)
     - fraud.json -> ESCALATE, and the adjudicator message must @mention the human nivishnick2k
       (this is acceptance criterion 5: human-in-the-loop).
   VERIFY the three files now have DIFFERENT md5sums (md5 docs/evidence/dr3-*.txt) and each greps to
   exactly one claim_id and the expected decision status. If they are still identical or a decision is
   missing, the relay did not complete for that fixture — fix it, do not paper over it.
   Note: a Gemini 429 (free-tier 20/day cap) is EXPECTED and fine — coverage falls back to a template
   note and the relay still completes. Do not block on it; do not switch models to work around it.

2) MAP TO ACCEPTANCE CRITERIA.
   Map each captured trail to the 6 criteria in docs/prd.md (section Acceptance). Write a short
   PASS/FAIL table into docs/status.md, each row citing the exact proving message/line.

3) SUBMISSION ASSETS (this is the bulk of remaining work — none exist yet). Keep them text-based so
   you can actually produce them in a CLI:
   a. Slide deck as docs/slides.md (Marp-style: one slide per `---` divider). Cover: the problem
      (auto-insurance claim adjudication, regulated/high-stakes); the architecture (4 remote agents,
      3 frameworks LangGraph/Gemini SDK/CrewAI, 2 vendors Groq+Gemini, collaborating through ONE Band
      room); the deterministic-relay design and WHY (D13 — free models can't reliably shuttle the JSON,
      so data flows through Band's shared context, LLM narrates); the decision rules; live-demo stills
      (paste real trail excerpts from docs/evidence/); cross-framework/vendor as the prize story. If
      python-pptx is already in .venv, ALSO export docs/claimband-deck.pptx; if not, leave the .md only
      (do NOT pip install anything).
   b. docs/recording-script.md — a 3-minute spoken script: post a claim -> watch the 4-agent relay in
      the Band room -> human-in-loop on the ESCALATE case -> final verdict. Time-stamped beats.
   c. Cover image: write docs/cover.svg directly (simple, clean: title "ClaimBand", subtitle, the
      4-agent relay arrow Intake->Coverage->Fraud->Adjudicator, "Band of Agents Hackathon — Track 3").
      Do not call an external image service.
   d. README final polish: verify run instructions work from a clean checkout — fresh venv import of
      claimband + PYTHONPATH=. ./.venv/bin/python -m pytest (must stay 23 green, black clean). State the
      Gemini free-tier 20/day cap honestly (relay is resilient by design).

4) UPDATE docs/status.md + docs/changelog.md with what ACTUALLY happened, including any failures or
   skips. If a step needs an irreversible or outward-facing action (git push, deleting the orphan rooms
   38dc6e6c.../2e7e1b59.../34cd5ad4..., creating a PR), DO NOT do it — write it under a
   "BLOCKED — needs human" heading in docs/status.md with your recommendation, and continue with other
   allowed work.

Honesty bar: the planner cold-verifies against docs/evidence/* and md5s. A false "done" will be caught.
Report exactly what you verified, with file paths, md5sums, and the decision line for each fixture.
```
