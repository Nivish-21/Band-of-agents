import Hero from "../components/Hero";
import Showcase from "../components/Showcase";
import Sandbox from "../components/Sandbox";

const PILLARS: { title: string; body: string }[] = [
  {
    title: "Band is the collaboration layer",
    body: "Agents exchange the full claim record as shared room context, route work with @mentions, and broadcast the verdict to the whole band — not a thin wrapper around a final notification.",
  },
  {
    title: "Rules as guardrails, models for judgment",
    body: "Data flows deterministically through Band's shared context (reliable — no JSON-shuttle failures). On top, each agent's model makes calls the rules can't: the Fraud agent reads the incident narrative and adds risk a field-check would miss. The deterministic guardrails set the hard floor; the model decides within them.",
  },
  {
    title: "Resilient by design",
    body: "When Gemini's free tier hits its 20/day cap and returns 429, the Coverage agent falls back to a templated note and the relay still completes end-to-end. No data loss, no crash.",
  },
];

const CRITERIA: { label: string; state: "pass" | "gap"; note: string }[] = [
  { label: "CLM-CLEAN → APPROVE, correct amount", state: "pass", note: "$3,700 payable" },
  { label: "CLM-DENY → DENY with reason", state: "pass", note: "policy expired" },
  { label: "CLM-FRAUD → ESCALATE + human @mention", state: "pass", note: "risk 60, human-in-loop" },
  { label: "Different frameworks AND vendors at startup", state: "pass", note: "shown in startup banner" },
  { label: "No agent crash, WebSocket reconnect handled", state: "pass", note: "3/3 runs clean" },
  { label: "Band peer-discovery on ambiguous-risk path", state: "gap", note: "designed, not yet demonstrated" },
];

export default function Home() {
  return (
    <main>
      <Hero />
      <Showcase />

      <div className="mx-auto max-w-6xl px-5">
        <hr className="border-line" />
      </div>

      <Sandbox />

      {/* Why it's built this way */}
      <section
        aria-labelledby="why-heading"
        className="mx-auto max-w-6xl px-5 py-20 sm:py-24"
      >
        <h2 id="why-heading" className="max-w-2xl text-3xl font-bold sm:text-4xl">
          Why this wins: real cross-framework collaboration
        </h2>
        <p className="mt-4 max-w-[65ch] text-ink-muted">
          Most agents work alone. ClaimBand puts three frameworks and two vendors in
          one room and makes them finish a regulated workflow together.
        </p>
        <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-3">
          {PILLARS.map((p) => (
            <article key={p.title} className="bg-bg p-6 sm:p-7">
              <h3 className="font-display text-lg font-bold text-ink">{p.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">{p.body}</p>
            </article>
          ))}
        </div>
      </section>

      {/* Honest status */}
      <section
        aria-labelledby="status-heading"
        className="mx-auto max-w-6xl px-5 pb-24"
      >
        <div className="rounded-2xl border border-line bg-surface/40 p-6 sm:p-8">
          <h2 id="status-heading" className="text-2xl font-bold">
            Acceptance criteria — honestly
          </h2>
          <p className="mt-3 max-w-[65ch] text-sm text-ink-muted">
            Five of six pass against the live runs. The sixth is built but not yet
            demonstrated; a credible system names its edges.
          </p>
          <ul className="mt-7 space-y-2.5">
            {CRITERIA.map((c) => {
              const ok = c.state === "pass";
              const color = ok ? "var(--color-approve)" : "var(--color-escalate)";
              return (
                <li
                  key={c.label}
                  className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-line/70 pb-2.5 last:border-0"
                >
                  <span
                    aria-hidden
                    className="flex size-5 shrink-0 items-center justify-center rounded-full text-[11px]"
                    style={{
                      background: `color-mix(in oklch, ${color} 20%, transparent)`,
                      color,
                    }}
                  >
                    {ok ? "✓" : "◐"}
                  </span>
                  <span className="text-sm text-ink">{c.label}</span>
                  <span className="mono ml-auto text-[11px]" style={{ color }}>
                    {c.note}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-10">
          <span className="font-display text-sm font-bold">
            Claim<span className="text-accent">Band</span>
          </span>
          <p className="mono text-[11px] text-ink-faint">
            Band of Agents Hackathon · Track 3 · LangGraph · Gemini SDK · CrewAI ·
            Groq · Gemini
          </p>
          <a
            href="https://github.com/Nivish-21/Band-of-agents"
            className="mono text-xs text-ink-muted transition-colors hover:text-ink"
          >
            github ↗
          </a>
        </div>
      </footer>
    </main>
  );
}
