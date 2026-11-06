"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { STATUS_CLASS, STATUS_LABEL } from "@/lib/labels";
import type { Application, ApplicationStatus, QueueSummary } from "@/lib/types";

type QueueFilter =
  | { id: "open" }
  | { id: "all" }
  | { id: "status"; status: ApplicationStatus }
  | { id: "flagged" };

const EMPTY: Record<string, string> = {
  open: "No open files. Start with a new intake.",
  all: "No applications yet. Start with a new intake.",
  SUBMITTED: "No files waiting at intake.",
  FIELD_VERIFICATION: "No files in field verification.",
  READY_FOR_DECISION: "No files waiting on a decision.",
  RETURNED: "No returned files.",
  APPROVED: "No approved mutations yet.",
  REJECTED: "No rejected applications yet.",
  flagged: "No open files with an ownership mismatch.",
};

const CLOSED: ApplicationStatus[] = ["APPROVED", "REJECTED"];

export default function DashboardPage() {
  const [summary, setSummary] = useState<QueueSummary | null>(null);
  const [items, setItems] = useState<Application[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<QueueFilter>({ id: "open" });

  useEffect(() => {
    const listParams =
      filter.id === "all"
        ? { view: "all" as const }
        : filter.id === "status"
          ? { view: CLOSED.includes(filter.status) ? ("all" as const) : ("open" as const), status: filter.status }
          : filter.id === "flagged"
            ? { view: "open" as const, flagged: true }
            : { view: "open" as const };

    Promise.all([api.summary(), api.list(listParams)])
      .then(([queue, applications]) => {
        setSummary(queue);
        setItems(applications);
      })
      .catch((err: Error) => setError(err.message));
  }, [filter]);

  function toggleStatus(status: ApplicationStatus) {
    setFilter((current) =>
      current.id === "status" && current.status === status ? { id: "open" } : { id: "status", status }
    );
  }

  const emptyKey =
    filter.id === "status" ? filter.status : filter.id === "flagged" ? "flagged" : filter.id;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Priority work queue</h1>
          <p className="mt-1 text-sm text-ink/70">
            Open files first: mismatches and decisions at the top, oldest wait first. Click a count to
            focus that slice.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setFilter((current) => (current.id === "all" ? { id: "open" } : { id: "all" }))}
          className={`text-sm ${filter.id === "all" ? "font-medium text-forest" : "text-ink/60 hover:text-forest"}`}
        >
          {filter.id === "all" ? "Showing all files" : "Include closed files"}
        </button>
      </div>

      {error && (
        <p className="rounded border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">
          Could not reach the API. Start the backend on port 8000. {error}
        </p>
      )}

      {summary && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Stat
            label="Intake pending"
            value={summary.submitted}
            active={filter.id === "status" && filter.status === "SUBMITTED"}
            onClick={() => toggleStatus("SUBMITTED")}
          />
          <Stat
            label="Field verification"
            value={summary.field_verification}
            active={filter.id === "status" && filter.status === "FIELD_VERIFICATION"}
            onClick={() => toggleStatus("FIELD_VERIFICATION")}
          />
          <Stat
            label="Ready for decision"
            value={summary.ready_for_decision}
            active={filter.id === "status" && filter.status === "READY_FOR_DECISION"}
            onClick={() => toggleStatus("READY_FOR_DECISION")}
          />
          <Stat
            label="Returned"
            value={summary.returned}
            active={filter.id === "status" && filter.status === "RETURNED"}
            onClick={() => toggleStatus("RETURNED")}
          />
          <Stat
            label="High-priority discrepancies"
            value={summary.high_priority_discrepancies}
            accent
            active={filter.id === "flagged"}
            onClick={() => setFilter((current) => (current.id === "flagged" ? { id: "open" } : { id: "flagged" }))}
          />
        </section>
      )}

      {summary && (
        <section>
          <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-ink/50">Decided</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Stat
              label="Approved"
              value={summary.approved}
              tone="approved"
              active={filter.id === "status" && filter.status === "APPROVED"}
              onClick={() => toggleStatus("APPROVED")}
            />
            <Stat
              label="Rejected"
              value={summary.rejected}
              tone="rejected"
              active={filter.id === "status" && filter.status === "REJECTED"}
              onClick={() => toggleStatus("REJECTED")}
            />
          </div>
        </section>
      )}

      <section className="overflow-hidden rounded-lg border border-ink/10 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-ink/5 text-xs uppercase tracking-wide text-ink/60">
            <tr>
              <th className="px-4 py-3">Applicant</th>
              <th className="px-4 py-3">Mouza / JL / Dag / Khatian</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Why it is here</th>
              <th className="px-4 py-3">Next action</th>
              <th className="px-4 py-3">AI flag</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.id}
                className={`border-t border-ink/10 ${item.mismatch_flag?.flagged ? "bg-rose-50/70" : ""}`}
              >
                <td className="px-4 py-3">
                  <Link href={`/applications/${item.id}`} className="font-medium text-forest hover:underline">
                    {item.applicant_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink/80">
                  {item.mouza} / {item.jl_number} / {item.dag_number} / {item.khatian_number}
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-1 text-xs ${STATUS_CLASS[item.status]}`}>
                    {STATUS_LABEL[item.status]}
                  </span>
                </td>
                <td className="px-4 py-3 text-ink/80">{item.attention_reason}</td>
                <td className="px-4 py-3 text-ink/80">{item.next_action}</td>
                <td className="px-4 py-3">
                  {item.mismatch_flag?.flagged ? (
                    <span className="text-rose-700">Mismatch</span>
                  ) : (
                    <span className="text-ink/50">None</span>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && !error && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink/50">
                  {EMPTY[emptyKey]}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}

const STAT_TONE = {
  default: {
    idle: "border-ink/10 bg-white hover:border-forest/40",
    active: "border-forest bg-emerald-50 ring-2 ring-forest/30",
  },
  accent: {
    idle: "border-rose-200 bg-rose-50 hover:border-rose-300",
    active: "border-rose-400 bg-rose-100 ring-2 ring-rose-300",
  },
  approved: {
    idle: "border-emerald-200 bg-white hover:border-emerald-400",
    active: "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-300",
  },
  rejected: {
    idle: "border-rose-200 bg-white hover:border-rose-400",
    active: "border-rose-500 bg-rose-50 ring-2 ring-rose-300",
  },
};

function Stat({
  label,
  value,
  accent,
  tone,
  active,
  onClick,
}: {
  label: string;
  value: number;
  accent?: boolean;
  tone?: keyof typeof STAT_TONE;
  active?: boolean;
  onClick: () => void;
}) {
  const colors = STAT_TONE[tone ?? (accent ? "accent" : "default")];
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-lg border px-4 py-3 text-left ${active ? colors.active : colors.idle}`}
    >
      <p className="text-xs uppercase tracking-wide text-ink/50">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </button>
  );
}
