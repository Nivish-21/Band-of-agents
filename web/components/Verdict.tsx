"use client";

import { motion } from "motion/react";

const META: Record<
  string,
  { color: string; icon: string; line: string }
> = {
  APPROVE: { color: "var(--color-approve)", icon: "✓", line: "Auto-approved" },
  DENY: { color: "var(--color-deny)", icon: "✕", line: "Denied" },
  ESCALATE: {
    color: "var(--color-escalate)",
    icon: "⚑",
    line: "Escalated to a human",
  },
};

interface VerdictProps {
  outcome: string;
  reason: string;
  finalAmount: number | null;
  claimId: string;
}

export default function Verdict({
  outcome,
  reason,
  finalAmount,
  claimId,
}: VerdictProps) {
  const meta = META[outcome] ?? {
    color: "var(--color-ink)",
    icon: "•",
    line: outcome,
  };
  const amount = finalAmount;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.95, ease: [0.16, 1, 0.3, 1] }}
      className="relative overflow-hidden rounded-2xl border p-6 sm:p-8"
      style={{
        borderColor: meta.color,
        background: `color-mix(in oklch, ${meta.color} 12%, var(--color-surface))`,
      }}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -right-16 -top-16 size-48 rounded-full blur-3xl"
        style={{ background: meta.color, opacity: 0.18 }}
      />
      <div className="flex flex-wrap items-center gap-x-6 gap-y-4">
        <div
          className="flex size-14 shrink-0 items-center justify-center rounded-xl text-2xl"
          style={{
            background: `color-mix(in oklch, ${meta.color} 22%, transparent)`,
            color: meta.color,
          }}
          aria-hidden
        >
          {meta.icon}
        </div>
        <div className="min-w-0">
          <p className="mono text-[11px] uppercase tracking-wider text-ink-faint">
            Final decision · {claimId}
          </p>
          <p
            className="font-display text-3xl font-extrabold sm:text-4xl"
            style={{ color: meta.color }}
          >
            {outcome}
          </p>
        </div>
        {amount != null && outcome !== "DENY" && (
          <div className="ml-auto text-right">
            <p className="mono text-[11px] uppercase tracking-wider text-ink-faint">
              {outcome === "APPROVE" ? "Payable" : "Amount under review"}
            </p>
            <p className="font-display text-3xl font-bold text-ink">
              ${amount.toLocaleString()}
            </p>
          </div>
        )}
      </div>
      <p className="mt-5 max-w-[70ch] text-sm leading-relaxed text-ink-muted">
        {reason}
      </p>
    </motion.div>
  );
}
