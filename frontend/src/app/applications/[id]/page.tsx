"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { NEXT_ACTIONS, STATUS_CLASS, STATUS_LABEL } from "@/lib/labels";
import type { Application, ApplicationStatus } from "@/lib/types";

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<Application | null>(null);
  const [remarks, setRemarks] = useState("");
  const [language, setLanguage] = useState("en");
  const [error, setError] = useState<string | null>(null);
  const [transferor, setTransferor] = useState("");
  const [owner, setOwner] = useState("");
  const [khajna, setKhajna] = useState("");

  async function load() {
    const data = await api.get(params.id);
    setItem(data);
    setTransferor(data.transferor_name ?? "");
    setOwner(data.recorded_owner_name ?? "");
    setKhajna(data.khajna_status ?? "");
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, [params.id]);

  async function saveFieldNotes() {
    if (!item) return;
    setError(null);
    try {
      const updated = await api.update(item.id, {
        transferor_name: transferor,
        recorded_owner_name: owner,
        khajna_status: khajna,
      });
      setItem(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function move(status: ApplicationStatus) {
    if (!item) return;
    setError(null);
    try {
      const updated = await api.transition(item.id, status, remarks || undefined, language);
      setItem(updated);
      setRemarks("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transition failed");
    }
  }

  if (!item) {
    return <p className="text-sm text-ink/60">{error ?? "Loading…"}</p>;
  }

  const actions = NEXT_ACTIONS[item.status] ?? [];

  return (
    <div className="space-y-8">
      <div>
        <Link href="/" className="text-sm text-forest hover:underline">
          Back to queue
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold">{item.applicant_name}</h1>
          <span className={`rounded-full px-2 py-1 text-xs ${STATUS_CLASS[item.status]}`}>
            {STATUS_LABEL[item.status]}
          </span>
        </div>
        <p className="mt-1 text-sm text-ink/70">
          Mouza {item.mouza} · J.L. {item.jl_number} · Dag {item.dag_number} · Khatian {item.khatian_number}
        </p>
      </div>

      {error && <p className="rounded bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>}

      {item.mismatch_flag && (
        <section
          className={`rounded-lg border px-4 py-3 text-sm ${
            item.mismatch_flag.flagged ? "border-rose-200 bg-rose-50 text-rose-900" : "border-ink/10 bg-white"
          }`}
        >
          <p className="font-medium">AI chain check</p>
          <p className="mt-1">{item.mismatch_flag.message}</p>
        </section>
      )}

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-3 rounded-lg border border-ink/10 bg-white p-4">
          <h2 className="font-medium">Stage 2: Field and chain verification</h2>
          <label className="block text-sm">
            Transferor
            <input className="mt-1 w-full rounded border border-ink/20 px-3 py-2" value={transferor} onChange={(e) => setTransferor(e.target.value)} />
          </label>
          <label className="block text-sm">
            Recorded owner
            <input className="mt-1 w-full rounded border border-ink/20 px-3 py-2" value={owner} onChange={(e) => setOwner(e.target.value)} />
          </label>
          <label className="block text-sm">
            Khajna status
            <input className="mt-1 w-full rounded border border-ink/20 px-3 py-2" value={khajna} onChange={(e) => setKhajna(e.target.value)} />
          </label>
          <button type="button" onClick={saveFieldNotes} className="rounded border border-forest px-3 py-1.5 text-sm text-forest">
            Save verification notes
          </button>
          <label className="block text-sm">
            Sale deed (Dalil)
            <input
              type="file"
              className="mt-1 block w-full text-sm"
              onChange={async (event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                try {
                  setItem(await api.upload(item.id, { saleDeed: file }));
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Upload failed");
                }
              }}
            />
            {item.sale_deed_path && <span className="text-xs text-ink/50">Stored</span>}
          </label>
          <label className="block text-sm">
            Existing Porcha
            <input
              type="file"
              className="mt-1 block w-full text-sm"
              onChange={async (event) => {
                const file = event.target.files?.[0];
                if (!file) return;
                try {
                  setItem(await api.upload(item.id, { porcha: file }));
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Upload failed");
                }
              }}
            />
            {item.porcha_path && <span className="text-xs text-ink/50">Stored</span>}
          </label>
        </div>

        <div className="space-y-3 rounded-lg border border-ink/10 bg-white p-4">
          <h2 className="font-medium">Stage 3: Officer decision</h2>
          <p className="text-sm text-ink/60">
            The inspector retains final authority. AI may draft a return notice; it cannot approve or reject.
          </p>
          <textarea
            className="min-h-24 w-full rounded border border-ink/20 px-3 py-2 text-sm"
            placeholder="Officer remarks, or missing documents for a return"
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
          />
          <label className="flex items-center gap-2 text-sm">
            Notice language
            <select className="rounded border border-ink/20 px-2 py-1" value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">English</option>
              <option value="bn">Bengali</option>
            </select>
          </label>
          <div className="flex flex-wrap gap-2">
            {actions.map((action) => (
              <button
                key={action.status}
                type="button"
                onClick={() => move(action.status)}
                className="rounded bg-forest px-3 py-1.5 text-sm text-white"
              >
                {action.label}
              </button>
            ))}
            {actions.length === 0 && <p className="text-sm text-ink/50">This file is closed.</p>}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-ink/10 bg-white">
        <h2 className="border-b border-ink/10 px-4 py-3 font-medium">Audit trail</h2>
        <ol className="divide-y divide-ink/10">
          {item.history.map((entry) => (
            <li key={entry.id} className="px-4 py-3 text-sm">
              <p className="font-medium">
                {entry.previous_status ?? "—"} → {STATUS_LABEL[entry.new_status]}
              </p>
              <p className="text-ink/50">{new Date(entry.timestamp).toLocaleString()}</p>
              {entry.officer_remarks && <p className="mt-1">{entry.officer_remarks}</p>}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
