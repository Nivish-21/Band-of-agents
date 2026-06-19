"use client";

import { motion } from "motion/react";
import type { Agent, ClaimRecord } from "../lib/data";

interface AgentNodeProps {
  agent: Agent;
  record: ClaimRecord;
  index: number;
}

const itemVariants = {
  hidden: { opacity: 0, y: 18, filter: "blur(6px)" },
  show: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const },
  },
};

function Pill({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span
      className="mono inline-flex items-center gap-1 text-[11px] leading-none"
      style={{ color: ok ? "var(--color-approve)" : "var(--color-deny)" }}
    >
      <span aria-hidden>{ok ? "✓" : "✕"}</span>
      {label}
    </span>
  );
}

function Findings({ agent, record }: { agent: Agent; record: ClaimRecord }) {
  if (agent.produces === "intake" && record.intake) {
    const b = record.intake;
    return (
      <ul className="space-y-1.5">
        <li>
          <Pill label={b.is_valid ? "valid" : "invalid"} ok={b.is_valid} />
        </li>
        <li className="mono text-[11px] text-ink-faint">
          completeness {b.completeness_score.toFixed(0)}%
        </li>
        <li className="mono text-[11px] text-ink-faint">
          {b.missing_fields.length} missing · {b.inconsistencies.length} conflicts
        </li>
      </ul>
    );
  }
  if (agent.produces === "coverage" && record.coverage) {
    const b = record.coverage;
    return (
      <ul className="space-y-1.5">
        <li>
          <Pill label="policy active" ok={b.policy_active} />
        </li>
        <li>
          <Pill label="peril covered" ok={b.peril_covered} />
        </li>
        <li className="mono text-[11px] text-ink-faint">
          covered{" "}
          <span className="text-ink">
            ${b.covered_amount.toLocaleString()}
          </span>
        </li>
      </ul>
    );
  }
  if (agent.produces === "fraud" && record.fraud) {
    const b = record.fraud;
    const rule = b.rule_risk ?? b.risk_score;
    const narrative = b.narrative_risk ?? 0;
    const combined = Math.min(100, rule + narrative);
    const high = combined >= 60;
    const mid = combined >= 40 && combined < 60;
    const color = high
      ? "var(--color-deny)"
      : mid
        ? "var(--color-escalate)"
        : "var(--color-approve)";
    return (
      <div className="space-y-2">
        <div className="flex items-baseline gap-1.5">
          <span
            className="font-display text-3xl font-bold leading-none"
            style={{ color }}
          >
            {combined}
          </span>
          <span className="mono text-[11px] text-ink-faint">/100 risk</span>
        </div>
        <p className="mono text-[11px] text-ink-faint">
          {rule} rules
          {narrative > 0 && (
            <>
              {" + "}
              <span style={{ color: "var(--color-accent)" }}>
                {narrative} model
              </span>
            </>
          )}
        </p>
        {b.narrative_rationale && (
          <p className="border-t border-line/70 pt-2 text-[12px] italic leading-snug text-ink-muted">
            “{b.narrative_rationale}”
          </p>
        )}
      </div>
    );
  }
  if (agent.produces === "decision" && record.decision) {
    const b = record.decision;
    return (
      <div className="space-y-1.5">
        <span className="mono text-[11px] text-ink-faint">verdict →</span>
        <p className="font-display text-base font-bold text-ink">{b.status}</p>
      </div>
    );
  }
  return null;
}

export default function AgentNode({ agent, record, index }: AgentNodeProps) {
  return (
    <motion.li
      variants={itemVariants}
      className="group relative flex-1 rounded-xl border border-line bg-surface/70 p-4 backdrop-blur-sm transition-colors duration-300 hover:border-accent/60"
      style={{ boxShadow: "0 1px 0 0 oklch(1 0 0 / 0.04) inset" }}
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="mono text-[11px] text-ink-faint">
          0{index + 1}
        </span>
        <motion.span
          aria-hidden
          className="size-2 rounded-full"
          style={{ background: "var(--color-accent)" }}
          animate={{ opacity: [0.35, 1, 0.35] }}
          transition={{
            duration: 2,
            repeat: Infinity,
            delay: index * 0.4,
            ease: "easeInOut",
          }}
        />
      </div>
      <h3 className="font-display text-lg font-bold text-ink">{agent.name}</h3>
      <p className="mono mt-1 mb-3 text-[11px] text-accent">
        {agent.framework} · {agent.vendor}
      </p>
      <Findings agent={agent} record={record} />
    </motion.li>
  );
}
