# ClaimBand — showcase frontend

A static Next.js site that visualises the **real** captured ClaimBand runs (clean → APPROVE,
deny → DENY, fraud → ESCALATE-to-human). Dark "control-room" aesthetic; the four-agent relay is
the hero. No backend, no secrets — the data is bundled from `web/data/scenarios.json`, which is
generated from `docs/evidence/dr3-*.txt` by `scripts/build_web_data.py`.

## Local dev

```bash
cd web
npm install
npm run dev      # http://localhost:3000 (falls back to 3001 if taken)
npm run build    # production build — fully static (SSG)
```

## Regenerate the data (optional)

The committed `web/data/scenarios.json` is enough to build. To refresh it from new evidence:

```bash
# from the repo root, in the Python venv
PYTHONPATH=. ./.venv/bin/python scripts/build_web_data.py
```

## Deploying on Vercel

This app lives in the `web/` subdirectory of the repo, so when importing the GitHub repo into Vercel:

1. **Root Directory:** set it to **`web`** (Vercel → Project → Settings → Build & Deployment → Root Directory).
2. Framework preset: **Next.js** (auto-detected). Build command `next build`, output handled automatically.
3. No environment variables are required — the showcase is fully static.

Or with the CLI from the repo root:

```bash
cd web && vercel --prod
```

## Stack
Next.js 16 (App Router) · React 19 · Tailwind CSS v4 · `motion` (Framer Motion) ·
`next/font` (Bricolage Grotesque / Archivo / JetBrains Mono). Design context lives in the repo-root
`PRODUCT.md` and `DESIGN.md`.
