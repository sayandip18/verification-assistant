"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { STATUS_CLASS, STATUS_LABEL } from "@/lib/labels";
import type { Application, QueueSummary } from "@/lib/types";

export default function DashboardPage() {
  const [summary, setSummary] = useState<QueueSummary | null>(null);
  const [items, setItems] = useState<Application[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.summary(), api.list()])
      .then(([queue, applications]) => {
        setSummary(queue);
        setItems(applications);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Priority work queue</h1>
        <p className="mt-1 text-sm text-ink/70">
          Pending intake, field checks, decisions, and ownership discrepancies.
        </p>
      </div>

      {error && (
        <p className="rounded border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">
          Could not reach the API. Start the backend on port 8000. {error}
        </p>
      )}

      {summary && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Stat label="Intake pending" value={summary.submitted} />
          <Stat label="Field verification" value={summary.field_verification} />
          <Stat label="Ready for decision" value={summary.ready_for_decision} />
          <Stat label="Returned" value={summary.returned} />
          <Stat label="High-priority discrepancies" value={summary.high_priority_discrepancies} accent />
        </section>
      )}

      <section className="overflow-hidden rounded-lg border border-ink/10 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-ink/5 text-xs uppercase tracking-wide text-ink/60">
            <tr>
              <th className="px-4 py-3">Applicant</th>
              <th className="px-4 py-3">Mouza / JL / Dag / Khatian</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">AI flag</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-ink/10">
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
                <td colSpan={4} className="px-4 py-8 text-center text-ink/50">
                  No applications yet. Start with a new intake.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: number; accent?: boolean }) {
  return (
    <div className={`rounded-lg border px-4 py-3 ${accent ? "border-rose-200 bg-rose-50" : "border-ink/10 bg-white"}`}>
      <p className="text-xs uppercase tracking-wide text-ink/50">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
