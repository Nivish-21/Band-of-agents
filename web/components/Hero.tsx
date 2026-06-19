"use client";

import { motion } from "motion/react";
import { agents } from "../lib/data";

const STATS: [string, string][] = [
  ["4", "remote agents"],
  ["3", "frameworks"],
  ["2", "model vendors"],
  ["1", "Band room"],
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, delay: 0.06 * i, ease: [0.16, 1, 0.3, 1] as const },
  }),
};

export default function Hero() {
  return (
    <header className="relative mx-auto max-w-6xl px-5 pb-12 pt-8">
      <nav className="mb-20 flex items-center justify-between">
        <span className="font-display text-lg font-bold tracking-tight">
          Claim<span className="text-accent">Band</span>
        </span>
        <a
          href="https://github.com/Nivish-21/Band-of-agents"
          className="mono text-xs text-ink-muted transition-colors hover:text-ink"
        >
          github ↗
        </a>
      </nav>

      <div className="max-w-4xl">
        <motion.p
          custom={0}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          className="mono mb-5 text-xs uppercase tracking-[0.22em] text-accent"
        >
          Band of Agents Hackathon · Track 3 — regulated &amp; high-stakes
        </motion.p>

        <motion.h1
          custom={1}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          className="text-[clamp(2.6rem,7vw,5.5rem)] font-extrabold"
        >
          Insurance claims,{" "}
          <span className="text-accent">adjudicated by a band of agents.</span>
        </motion.h1>

        <motion.p
          custom={2}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          className="mt-6 max-w-[60ch] text-lg text-ink-muted"
        >
          Four specialist AI agents — each on a different framework and model vendor —
          collaborate inside one Band room to triage an auto-insurance claim and decide{" "}
          <span className="text-ink">APPROVE</span>,{" "}
          <span className="text-ink">DENY</span>, or{" "}
          <span className="text-ink">ESCALATE</span> to a human.
        </motion.p>
      </div>

      {/* relay motif */}
      <motion.div
        custom={3}
        variants={fadeUp}
        initial="hidden"
        animate="show"
        className="mt-12 flex flex-wrap items-center gap-x-2 gap-y-3"
      >
        {agents.map((a, i) => (
          <span key={a.key} className="flex items-center gap-2">
            <span className="rounded-lg border border-line bg-surface/60 px-3 py-2">
              <span className="font-display text-sm font-bold text-ink">
                {a.name}
              </span>
              <span className="mono ml-2 text-[11px] text-ink-faint">
                {a.framework}
              </span>
            </span>
            {i < agents.length - 1 && (
              <span className="font-display text-accent/70" aria-hidden>
                →
              </span>
            )}
          </span>
        ))}
        <span className="font-display text-ink-faint" aria-hidden>
          →
        </span>
        <span className="mono rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-[11px] text-accent">
          human reviewer
        </span>
      </motion.div>

      {/* stats */}
      <motion.dl
        custom={4}
        variants={fadeUp}
        initial="hidden"
        animate="show"
        className="mt-14 grid grid-cols-2 gap-6 border-t border-line pt-8 sm:grid-cols-4"
      >
        {STATS.map(([n, label]) => (
          <div key={label}>
            <dt className="font-display text-4xl font-extrabold text-ink">{n}</dt>
            <dd className="mono mt-1 text-[11px] uppercase tracking-wider text-ink-faint">
              {label}
            </dd>
          </div>
        ))}
      </motion.dl>

      <motion.div
        custom={5}
        variants={fadeUp}
        initial="hidden"
        animate="show"
        className="mt-12 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm"
      >
        <a
          href="#demo"
          className="inline-flex items-center gap-2 text-ink-muted transition-colors hover:text-ink"
        >
          Watch a claim get adjudicated
          <span aria-hidden className="text-accent">
            ↓
          </span>
        </a>
        <a
          href="#try"
          className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-4 py-2 font-medium text-accent transition-colors hover:bg-accent/20"
        >
          Adjudicate your own claim
          <span aria-hidden>→</span>
        </a>
      </motion.div>
    </header>
  );
}
