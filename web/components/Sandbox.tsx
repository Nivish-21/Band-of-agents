"use client";

import { useMemo, useState } from "react";
import { data, scenarioOrder } from "../lib/data";
import type { ClaimRecord } from "../lib/data";
import { runRelay } from "../lib/engine";
import Relay from "./Relay";
import Verdict from "./Verdict";

interface Form {
  policyStatus: string;
  effectiveDate: string;
  expiryDate: string;
  collisionCovered: boolean;
  liabilityLimit: number;
  deductible: number;
  incidentDate: string;
  incidentType: string;
  policeReport: boolean;
  photosCount: number;
  estimate: number;
  amountClaimed: number;
  isPolicyHolder: boolean;
  priorClaims: number;
}

const INCIDENT_TYPES = ["collision", "theft", "fire", "vandalism"];

function fromClaim(c: ClaimRecord): Form {
  return {
    policyStatus: c.policy.status,
    effectiveDate: c.policy.effective_date,
    expiryDate: c.policy.expiry_date,
    collisionCovered: c.policy.coverage.collision,
    liabilityLimit: c.policy.coverage.liability_limit,
    deductible: c.policy.coverage.deductible,
    incidentDate: c.incident.date,
    incidentType: c.incident.type,
    policeReport: c.incident.police_report,
    photosCount: c.damage.photos_count,
    estimate: c.damage.estimate_amount,
    amountClaimed: c.amount_claimed,
    isPolicyHolder: c.claimant.is_policy_holder,
    priorClaims: c.claimant.prior_claims_12mo,
  };
}

function toClaim(f: Form): ClaimRecord {
  return {
    claim_id: "CLM-YOURS",
    policy: {
      policy_id: "POL-LIVE",
      status: f.policyStatus,
      effective_date: f.effectiveDate,
      expiry_date: f.expiryDate,
      coverage: {
        collision: f.collisionCovered,
        liability_limit: f.liabilityLimit,
        deductible: f.deductible,
      },
    },
    claimant: {
      name: "Submitted claimant",
      is_policy_holder: f.isPolicyHolder,
      prior_claims_12mo: f.priorClaims,
    },
    incident: {
      date: f.incidentDate,
      type: f.incidentType,
      at_fault: "self",
      police_report: f.policeReport,
      description: "—",
    },
    damage: {
      vehicle: "Submitted vehicle",
      estimate_amount: f.estimate,
      photos_count: f.photosCount,
    },
    amount_claimed: f.amountClaimed,
    intake: null,
    coverage: null,
    fraud: null,
    decision: null,
  };
}

const fieldCls =
  "w-full rounded-lg border border-line bg-bg/60 px-3 py-2 text-sm text-ink transition-colors focus-visible:border-accent";

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={htmlFor} className="block">
      <span className="mono mb-1.5 block text-[11px] uppercase tracking-wider text-ink-faint">
        {label}
      </span>
      {children}
    </label>
  );
}

function Toggle({
  id,
  checked,
  onChange,
  onLabel,
  offLabel,
}: {
  id: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  onLabel: string;
  offLabel: string;
}) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex w-full items-center justify-between rounded-lg border border-line bg-bg/60 px-3 py-2 text-sm transition-colors hover:border-accent/50"
    >
      <span className={checked ? "text-ink" : "text-ink-faint"}>
        {checked ? onLabel : offLabel}
      </span>
      <span
        className="relative h-5 w-9 rounded-full transition-colors"
        style={{
          background: checked
            ? "var(--color-accent)"
            : "var(--color-surface-2)",
        }}
      >
        <span
          className="absolute top-0.5 size-4 rounded-full bg-white transition-all"
          style={{ left: checked ? "1.125rem" : "0.125rem" }}
        />
      </span>
    </button>
  );
}

export default function Sandbox() {
  const [form, setForm] = useState<Form>(() =>
    fromClaim(data.scenarios[scenarioOrder[0]].claim),
  );
  const [runId, setRunId] = useState(0);
  const set = <K extends keyof Form>(key: K, value: Form[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const result = useMemo(() => runRelay(toClaim(form)), [form, runId]);
  const decision = result.decision;

  return (
    <section
      id="try"
      aria-labelledby="try-heading"
      className="mx-auto max-w-6xl px-5 py-20 sm:py-28"
    >
      <header className="mb-10 max-w-2xl">
        <p className="mono mb-3 text-xs uppercase tracking-[0.2em] text-accent">
          Deterministic guardrails · runs in your browser
        </p>
        <h2 id="try-heading" className="text-3xl font-bold sm:text-4xl">
          Adjudicate your own claim
        </h2>
        <p className="mt-4 text-ink-muted">
          Edit the claim and run the{" "}
          <span className="text-ink">deterministic policy guardrails</span> the agents
          must obey — live in your browser. These set the hard floor a regulated
          workflow can&apos;t cross. On top of them, the agents&apos; models add{" "}
          <span className="text-ink">narrative judgment</span> the rules can&apos;t make
          — e.g. the Fraud agent reading the incident story (see the replay above).
        </p>
      </header>

      {/* Presets */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <span className="mono text-[11px] uppercase tracking-wider text-ink-faint">
          Start from
        </span>
        {scenarioOrder.map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => {
              setForm(fromClaim(data.scenarios[k].claim));
              setRunId((n) => n + 1);
            }}
            className="rounded-lg border border-line bg-surface/60 px-3 py-1.5 text-sm text-ink-muted transition-colors hover:border-accent/50 hover:text-ink"
          >
            {data.scenarios[k].label}
          </button>
        ))}
      </div>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        {/* Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setRunId((n) => n + 1);
          }}
          className="rounded-2xl border border-line bg-surface/40 p-5 sm:p-6"
        >
          <fieldset className="mb-6">
            <legend className="mb-3 font-display text-sm font-bold text-ink">
              Policy
            </legend>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Status" htmlFor="status">
                <select
                  id="status"
                  value={form.policyStatus}
                  onChange={(e) => set("policyStatus", e.target.value)}
                  className={fieldCls}
                >
                  <option value="active">active</option>
                  <option value="expired">expired</option>
                </select>
              </Field>
              <Field label="Collision covered" htmlFor="collision">
                <Toggle
                  id="collision"
                  checked={form.collisionCovered}
                  onChange={(v) => set("collisionCovered", v)}
                  onLabel="covered"
                  offLabel="excluded"
                />
              </Field>
              <Field label="Effective date" htmlFor="eff">
                <input
                  id="eff"
                  type="date"
                  value={form.effectiveDate}
                  onChange={(e) => set("effectiveDate", e.target.value)}
                  className={fieldCls}
                />
              </Field>
              <Field label="Expiry date" htmlFor="exp">
                <input
                  id="exp"
                  type="date"
                  value={form.expiryDate}
                  onChange={(e) => set("expiryDate", e.target.value)}
                  className={fieldCls}
                />
              </Field>
              <Field label="Liability limit ($)" htmlFor="limit">
                <input
                  id="limit"
                  type="number"
                  value={form.liabilityLimit}
                  onChange={(e) => set("liabilityLimit", Number(e.target.value))}
                  className={fieldCls}
                />
              </Field>
              <Field label="Deductible ($)" htmlFor="ded">
                <input
                  id="ded"
                  type="number"
                  value={form.deductible}
                  onChange={(e) => set("deductible", Number(e.target.value))}
                  className={fieldCls}
                />
              </Field>
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-3 font-display text-sm font-bold text-ink">
              Incident &amp; claimant
            </legend>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Incident type" htmlFor="type">
                <select
                  id="type"
                  value={form.incidentType}
                  onChange={(e) => set("incidentType", e.target.value)}
                  className={fieldCls}
                >
                  {INCIDENT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Incident date" htmlFor="incdate">
                <input
                  id="incdate"
                  type="date"
                  value={form.incidentDate}
                  onChange={(e) => set("incidentDate", e.target.value)}
                  className={fieldCls}
                />
              </Field>
              <Field label="Damage estimate ($)" htmlFor="est">
                <input
                  id="est"
                  type="number"
                  value={form.estimate}
                  onChange={(e) => set("estimate", Number(e.target.value))}
                  className={fieldCls}
                />
              </Field>
              <Field label="Amount claimed ($)" htmlFor="amt">
                <input
                  id="amt"
                  type="number"
                  value={form.amountClaimed}
                  onChange={(e) => set("amountClaimed", Number(e.target.value))}
                  className={fieldCls}
                />
              </Field>
              <Field label="Photos provided" htmlFor="photos">
                <input
                  id="photos"
                  type="number"
                  value={form.photosCount}
                  onChange={(e) => set("photosCount", Number(e.target.value))}
                  className={fieldCls}
                />
              </Field>
              <Field label="Prior claims (12mo)" htmlFor="prior">
                <input
                  id="prior"
                  type="number"
                  value={form.priorClaims}
                  onChange={(e) => set("priorClaims", Number(e.target.value))}
                  className={fieldCls}
                />
              </Field>
              <Field label="Police report" htmlFor="police">
                <Toggle
                  id="police"
                  checked={form.policeReport}
                  onChange={(v) => set("policeReport", v)}
                  onLabel="filed"
                  offLabel="none"
                />
              </Field>
              <Field label="Claimant" htmlFor="holder">
                <Toggle
                  id="holder"
                  checked={form.isPolicyHolder}
                  onChange={(v) => set("isPolicyHolder", v)}
                  onLabel="policyholder"
                  offLabel="third party"
                />
              </Field>
            </div>
          </fieldset>

          <button
            type="submit"
            className="mt-6 w-full rounded-lg bg-accent px-4 py-3 font-display text-sm font-bold text-bg transition-transform hover:scale-[1.01] active:scale-100"
          >
            Adjudicate claim →
          </button>
        </form>

        {/* Result */}
        <div className="space-y-6">
          <Relay record={result} runKey={runId} />
          {decision && (
            <Verdict
              outcome={decision.status}
              reason={decision.reason}
              finalAmount={decision.final_amount}
              claimId="CLM-YOURS"
            />
          )}
        </div>
      </div>
    </section>
  );
}
