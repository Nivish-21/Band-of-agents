# Product

## Register

brand

> The deliverable is a showcase/demo surface for the Band of Agents Hackathon (Track 3).
> A judge's impression *is* the thing being made — design IS the product here. The underlying
> ClaimBand system is a Python multi-agent backend; this web surface presents it.

## Users
Hackathon judges and enterprise evaluators viewing the submission online. Context: skimming many
projects quickly, on a laptop, deciding in minutes whether this is real and impressive. Job to be
done: understand in seconds *what* ClaimBand does, *that* it genuinely works (real runs, not a mock),
and *why* cross-framework multi-agent collaboration through Band is the interesting part.

## Product Purpose
Make ClaimBand's multi-agent claim-adjudication workflow legible and credible at a glance. The site
replays three REAL captured runs (clean → APPROVE, deny → DENY, fraud → ESCALATE-to-human), showing
a claim enter, four specialist agents (each a different framework + vendor) collaborate through one
Band room, and a final auditable verdict emerge. Success = a judge instantly grasps the workflow,
trusts it's real (the actual Band room trail is shown), and remembers the cross-framework story.

## Brand Personality
Precise, traceable, alive. The voice of a high-stakes control room / telemetry surface: confident,
technical, calm under stakes. Not playful, not corporate-bland. Three words: **clinical, kinetic, trustworthy.**

## Anti-references
- Generic enterprise-SaaS: navy-and-white, hero-metric template, endless identical icon-cards. The
  "fintech trust" cliché.
- The 2026 AI-cream / warm-neutral landing page with a display-serif italic headline and tracked
  uppercase eyebrows above every section (editorial-typographic slop).
- A dashboard full of nested cards. The relay is a *flow*, not a card grid.
- Monospace everywhere as costume. Mono is reserved for genuine data (the claim JSON, the room trail).

## Design Principles
- **Show the real thing.** Every number, decision, and message on screen comes from an actual captured
  run (`docs/evidence/`), not lorem/mock. Authenticity is the pitch.
- **The relay is the hero.** The four-agent handoff pipeline is the central visual, animated to read
  as a live system, not a static diagram.
- **Traceability is a feature, not a footnote.** Make the audit trail (who said what, in order, in the
  Band room) visible and first-class — it's why this fits a regulated workflow.
- **Honest by construction.** State plainly what passes and what's a known gap (peer-discovery). A
  credible system admits its edges.
- **Fast and unbreakable.** Static, no backend, no secrets, no live dependency. It cannot fail in front
  of a judge.

## Accessibility & Inclusion
WCAG 2.2 AA. Body text ≥4.5:1 on the dark surface (use bright ink, not muted gray, for anything that
must be read). Verdict states never rely on colour alone — pair the green/amber/red with an explicit
label and icon (APPROVE / DENY / ESCALATE). Full `prefers-reduced-motion` alternative for the relay
animation (instant/crossfade, no motion). Keyboard-navigable scenario switcher; visible focus rings.
