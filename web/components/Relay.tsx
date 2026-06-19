"use client";

import { Fragment } from "react";
import { motion } from "motion/react";
import { agents } from "../lib/data";
import type { ClaimRecord } from "../lib/data";
import AgentNode from "./AgentNode";

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.16, delayChildren: 0.08 } },
};

function Connector() {
  return (
    <div
      aria-hidden
      className="flex shrink-0 items-center justify-center py-0.5"
    >
      <div className="relative flex items-center justify-center">
        <span className="block h-6 w-px bg-gradient-to-b from-transparent via-accent/50 to-transparent" />
        <motion.span
          className="absolute font-display text-lg leading-none text-accent"
          animate={{ opacity: [0.45, 1, 0.45] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
        >
          ∷
        </motion.span>
      </div>
    </div>
  );
}

interface RelayProps {
  record: ClaimRecord;
  runKey: string | number;
}

export default function Relay({ record, runKey }: RelayProps) {
  return (
    <motion.ol
      key={runKey}
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="flex flex-col items-stretch gap-3"
    >
      {agents.map((agent, i) => (
        <Fragment key={agent.key}>
          <AgentNode agent={agent} record={record} index={i} />
          {i < agents.length - 1 && <Connector />}
        </Fragment>
      ))}
    </motion.ol>
  );
}
