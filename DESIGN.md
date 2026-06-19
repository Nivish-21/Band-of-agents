# Design

Visual system for the ClaimBand showcase. Dark "control-room / signal" aesthetic — reads as a live,
traceable system. Palette is identity-preserved from the committed `docs/cover.svg` (deep ink + cyan→indigo).

## Theme
Dark, single dominant world. The surface IS the brand (deep ink), brand energy carried by a cyan→indigo
signal accent and by the kinetic relay. Verdict semantics (green/amber/red) are the only other colours
and appear sparingly, only on decisions.

## Color (OKLCH; hex shown for reference, matches cover.svg)
| Role | Value | Use |
|---|---|---|
| `--bg` | `oklch(0.18 0.04 264)` ≈ `#0b1120` | page background (deep ink) |
| `--surface` | `oklch(0.23 0.05 264)` ≈ `#111c3a` | raised panels, agent nodes |
| `--surface-2` | `oklch(0.27 0.04 256)` ≈ `#1e293b` | hover / nested fills, borders |
| `--ink` | `oklch(0.98 0.005 248)` ≈ `#f8fafc` | primary text |
| `--ink-muted` | `oklch(0.80 0.03 250)` ≈ `#cbd5e1` | secondary text (≥4.5:1 on bg) |
| `--ink-faint` | `oklch(0.68 0.03 252)` ≈ `#94a3b8` | labels/meta only (large/non-essential) |
| `--accent` | `oklch(0.78 0.13 230)` ≈ `#38bdf8` | signal cyan: active relay, links, focus |
| `--accent-2` | `oklch(0.72 0.12 280)` ≈ `#818cf8` | indigo: gradients on lines/glow (never on text) |
| `--approve` | `oklch(0.78 0.15 165)` ≈ `#34d399` | APPROVE verdict |
| `--escalate` | `oklch(0.83 0.15 85)` ≈ `#fbbf24` | ESCALATE verdict |
| `--deny` | `oklch(0.70 0.17 25)` ≈ `#f87171` | DENY verdict |

Strategy: **Committed/Drenched dark.** No gradient text (banned). Cyan→indigo gradient only on relay
lines and glows. Verdict colour always paired with a label + icon (a11y).

## Typography
Pairing on a contrast axis: a characterful grotesque for display, a neutral grotesque for body, a true
mono for data. All non-reflex (no Inter / Space Grotesk / IBM Plex). Loaded via `next/font/google`.
- **Display / wordmark / section titles:** Bricolage Grotesque (700/800). Distinctive, engineered feel.
- **Body / UI:** Archivo (400/500/600). Highly legible neutral grotesque.
- **Data (claim JSON, room trail, telemetry, badges):** JetBrains Mono (400/500). Genuine technical use, not costume.
- Scale: fluid `clamp()`, ≥1.25 ratio. Hero ≤ 6rem. Letter-spacing ≥ -0.04em on display. Line-height
  +0.05–0.1 for light-on-dark. `text-wrap: balance` on headings.

## Layout
- Single long scroll, single-purpose folds: (1) hero with the relay as the centrepiece, (2) scenario
  switcher driving (3) the animated 4-agent relay + filling blocks, (4) verdict, (5) the raw Band room
  trail (audit), (6) the cross-framework "why this wins" + honest status, (7) footer/repo.
- Flex for 1D rows, grid only where 2D. Relay is a horizontal pipeline on desktop, vertical on mobile.
- Fluid spacing with `clamp()`; vary rhythm. No card-grid filler.

## Components
- **Agent node:** surface panel, status dot (idle/active/done), agent name (Bricolage), framework·vendor
  badge (mono), and the block it produced (mono key/values). Active state: cyan ring + soft glow.
- **Relay connector:** animated cyan→indigo line/flow between nodes; draws in sequence to read as handoff.
- **Verdict banner:** large status word + icon + reason + amount; colour = semantic, always with label.
- **Scenario switch:** segmented control (clean / deny / fraud); keyboard accessible, focus-visible.
- **Trail panel:** mono, message-by-message room dump (sender, time, content), the audit view.
- **Stat row (sparing):** 4 frameworks · 3? no — 3 frameworks · 2 vendors · 4 agents · 1 room.

## Motion
- Page-load: hero relay draws once (connectors stagger, nodes settle) — one orchestrated entrance.
- Scenario change: connectors re-draw in handoff order, blocks count/fill in, verdict resolves last.
- Ease-out-expo/quint; no bounce. Stagger the four nodes. Use `motion` (Framer Motion).
- Full `prefers-reduced-motion`: no draw/stagger, content shown instantly (crossfade at most).
- Never gate content visibility on a class-triggered transition (must render without JS motion).

## Imagery
The "imagery" is the custom relay visualization (SVG/canvas/DOM + motion) — the data viz IS the hero,
per the brand register. No stock photos; this is a system, not a place. The cover.svg motif (relay arrow)
is echoed in the hero.
