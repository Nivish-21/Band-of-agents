"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { agents, scenarios } from "../lib/data";
import AgentNode from "./AgentNode";
import Verdict from "./Verdict";
import Trail from "./Trail";

const OUTCOME_COLOR: Record<string, string> = {
  APPROVE: "var(--color-approve)",
  DENY: "var(--color-deny)",
  ESCALATE: "var(--color-escalate)",
};

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.16, delayChildren: 0.08 } },
};

function Connector() {
  return (
    <div
      aria-hidden
      className="flex shrink-0 items-center justify-center py-0.5 md:px-1 md:py-0"
    >
      <div className="relative flex items-center justify-center">
        <span className="block h-6 w-px bg-gradient-to-b from-transparent via-accent/50 to-transparent md:h-px md:w-8 md:bg-gradient-to-r" />
        <motion.span
          className="absolute rotate-90 font-display text-lg leading-none text-accent md:rotate-0"
          animate={{ opacity: [0.45, 1, 0.45] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
        >
          ›
        </motion.span>
      </div>
    </div>
  );
}

function ClaimStrip({
  vehicle,
  claimant,
  incident,
  amount,
  policyStatus,
}: {
  vehicle: string;
  claimant: string;
  incident: string;
  amount: number;
  policyStatus: string;
}) {
  const facts: [string, string][] = [
    ["claimant", claimant],
    ["vehicle", vehicle],
    ["incident", incident],
    ["claimed", `$${amount.toLocaleString()}`],
    ["policy", policyStatus],
  ];
  return (
    <dl className="flex flex-wrap gap-x-8 gap-y-3">
      {facts.map(([k, v]) => (
        <div key={k}>
          <dt className="mono text-[11px] uppercase tracking-wider text-ink-faint">
            {k}
          </dt>
          <dd className="text-sm text-ink">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function Showcase() {
  const [activeKey, setActiveKey] = useState(scenarios[0].key);
  const active = scenarios.find((s) => s.key === activeKey) ?? scenarios[0];

  return (
    <section
      id="demo"
      aria-labelledby="demo-heading"
      className="mx-auto max-w-6xl px-5 py-20 sm:py-28"
    >
      <header className="mb-10 max-w-2xl">
        <p className="mono mb-3 text-xs uppercase tracking-[0.2em] text-accent">
          Live relay · real captured runs
        </p>
        <h2 id="demo-heading" className="text-3xl font-bold sm:text-4xl">
          Watch a claim move through the band
        </h2>
        <p className="mt-4 text-ink-muted">
          Pick a claim. Each agent reads the shared record from the Band room, runs
          its tested logic, and hands off to the next — exactly as captured in a live
          run.
        </p>
      </header>

      {/* Scenario switch */}
      <div
        role="tablist"
        aria-label="Choose a claim scenario"
        className="mb-8 inline-flex flex-wrap gap-1.5 rounded-xl border border-line bg-surface/60 p-1.5"
      >
        {scenarios.map((s) => {
          const selected = s.key === activeKey;
          return (
            <button
              key={s.key}
              role="tab"
              aria-selected={selected}
              onClick={() => setActiveKey(s.key)}
              className="group relative rounded-lg px-4 py-2 text-sm font-medium transition-colors"
              style={{ color: selected ? "var(--color-ink)" : undefined }}
            >
              {selected && (
                <motion.span
                  layoutId="tab-bg"
                  className="absolute inset-0 rounded-lg border border-line bg-surface-2"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <span className="relative flex items-center gap-2">
                <span
                  className="size-1.5 rounded-full"
                  style={{ background: OUTCOME_COLOR[s.outcome] }}
                  aria-hidden
                />
                {s.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Claim summary */}
      <div className="mb-8 rounded-2xl border border-line bg-surface/40 p-5 sm:p-6">
        <div className="mb-4 flex items-center gap-3">
          <span className="mono whitespace-nowrap text-sm text-ink">
            {active.claim_id}
          </span>
          <span
            className="mono whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11px]"
            style={{
              color: OUTCOME_COLOR[active.outcome],
              background: `color-mix(in oklch, ${OUTCOME_COLOR[active.outcome]} 15%, transparent)`,
            }}
          >
            → {active.outcome}
          </span>
          <span className="text-sm text-ink-faint">{active.blurb}</span>
        </div>
        <ClaimStrip
          vehicle={active.claim.damage.vehicle}
          claimant={active.claim.claimant.name}
          incident={`${active.claim.incident.type} · ${active.claim.incident.date}`}
          amount={active.claim.amount_claimed}
          policyStatus={active.claim.policy.status}
        />
      </div>

      {/* Relay */}
      <motion.ol
        key={active.key}
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="mb-8 flex flex-col items-stretch gap-3 md:flex-row md:gap-1"
      >
        {agents.map((agent, i) => (
          <ContentsWithConnector key={agent.key} last={i === agents.length - 1}>
            <AgentNode agent={agent} record={active.record} index={i} />
          </ContentsWithConnector>
        ))}
      </motion.ol>

      <Verdict scenario={active} />

      {/* Audit trail */}
      <div className="mt-14">
        <h3 className="mb-1 text-xl font-bold">The Band room trail</h3>
        <p className="mb-5 max-w-2xl text-sm text-ink-muted">
          The actual messages from the live room — the full audit trail. The verdict
          is broadcast to every agent and the human reviewer.
        </p>
        <Trail messages={active.messages} />
      </div>
    </section>
  );
}

function ContentsWithConnector({
  children,
  last,
}: {
  children: React.ReactNode;
  last: boolean;
}) {
  return (
    <>
      {children}
      {!last && <Connector />}
    </>
  );
}
