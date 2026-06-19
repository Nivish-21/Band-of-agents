"use client";

import type { Message } from "../lib/data";

const SENDER_COLOR: Record<string, string> = {
  Intake: "var(--color-accent)",
  Coverage: "var(--color-accent-2)",
  Fraud: "var(--color-escalate)",
  Adjudicator: "var(--color-approve)",
};

function shortTime(iso: string): string {
  // "2026-06-19 04:36:11.710885+00:00" -> "04:36:11"
  const m = iso.match(/(\d{2}:\d{2}:\d{2})/);
  return m ? m[1] : iso;
}

export default function Trail({ messages }: { messages: Message[] }) {
  return (
    <ol className="space-y-px overflow-hidden rounded-xl border border-line bg-bg/60">
      {messages.map((m) => {
        const color = SENDER_COLOR[m.sender] ?? "var(--color-ink-faint)";
        return (
          <li
            key={m.n}
            className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 px-4 py-3 transition-colors hover:bg-surface/50 sm:grid-cols-[7ch_14ch_1fr]"
          >
            <span className="mono text-[11px] text-ink-faint">
              {shortTime(m.time)}
            </span>
            <span
              className="mono text-[11px] font-medium"
              style={{ color }}
            >
              {m.sender}
            </span>
            <span className="mono col-span-2 text-[12px] leading-relaxed text-ink-muted sm:col-span-1">
              {m.content}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
