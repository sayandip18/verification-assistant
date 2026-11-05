"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { NEXT_ACTIONS, STATUS_CLASS, STATUS_LABEL } from "@/lib/labels";
import { mergeExtracted } from "@/lib/extract";
import type { Application, ApplicationDraft, ApplicationStatus, OcrResult } from "@/lib/types";

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<Application | null>(null);
  const [remarks, setRemarks] = useState("");
  const [language, setLanguage] = useState("en");
  const [error, setError] = useState<string | null>(null);
  const [transferor, setTransferor] = useState("");
  const [owner, setOwner] = useState("");
  const [khajna, setKhajna] = useState("");

  function applyItem(data: Application) {
    setItem(data);
    setTransferor(data.transferor_name ?? "");
    setOwner(data.recorded_owner_name ?? "");
    setKhajna(data.khajna_status ?? "");
  }

  async function load() {
    applyItem(await api.get(params.id));
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
      applyItem(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function move(status: ApplicationStatus) {
    if (!item) return;
    setError(null);
    try {
      applyItem(await api.transition(item.id, status, remarks || undefined, language));
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
                  applyItem(await api.upload(item.id, { saleDeed: file }));
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Upload failed");
                }
              }}
            />
            {item.documents.some((doc) => doc.document_type === "SALE_DEED") && (
              <span className="text-xs text-ink/50">Stored in blob storage</span>
            )}
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
                  applyItem(await api.upload(item.id, { porcha: file }));
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Upload failed");
                }
              }}
            />
            {item.documents.some((doc) => doc.document_type === "PORCHA") && (
              <span className="text-xs text-ink/50">Stored in blob storage</span>
            )}
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

      {(item.ocr_results ?? []).length > 0 && (
        <section className="space-y-3">
          <h2 className="font-medium">OCR results</h2>
          {item.ocr_results.map((run) => (
            <OcrCard
              key={`${run.document_id}-${run.created_at}`}
              run={run}
              onRerun={async () => {
                if (!run.document_id) return;
                setError(null);
                try {
                  applyItem(await api.rerunOcr(item.id, run.document_id));
                } catch (err) {
                  setError(err instanceof Error ? err.message : "OCR failed");
                }
              }}
              onFillEmpty={() => {
                if (!run.extracted) return;
                const filled = mergeExtracted(
                  {
                    transferor_name: transferor,
                    recorded_owner_name: owner,
                    khajna_status: khajna,
                  },
                  run.extracted as Partial<ApplicationDraft>
                );
                setTransferor(String(filled.transferor_name ?? ""));
                setOwner(String(filled.recorded_owner_name ?? ""));
                setKhajna(String(filled.khajna_status ?? ""));
              }}
            />
          ))}
        </section>
      )}

      <section className="rounded-lg border border-ink/10 bg-white">
        <h2 className="border-b border-ink/10 px-4 py-3 font-medium">Audit trail</h2>
        <ol className="divide-y divide-ink/10">
          {item.history.map((entry) => (
            <li key={entry.id} className="px-4 py-3 text-sm">
              <p className="font-medium">
                {entry.previous_status ?? "—"} → {STATUS_LABEL[entry.new_status]}
              </p>
              <p className="text-ink/50">{new Date(entry.created_at).toLocaleString()}</p>
              {entry.officer_remarks && <p className="mt-1">{entry.officer_remarks}</p>}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function OcrCard({
  run,
  onRerun,
  onFillEmpty,
}: {
  run: OcrResult;
  onRerun: () => void;
  onFillEmpty: () => void;
}) {
  const failed = run.status === "FAILED";
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${failed ? "border-rose-200 bg-rose-50" : "border-ink/10 bg-white"}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium">
          {run.document_type === "SALE_DEED" ? "Sale deed" : run.document_type === "PORCHA" ? "Porcha" : "Document"}{" "}
          <span className="font-normal text-ink/50">{run.original_filename}</span>
        </p>
        <p className="text-xs uppercase tracking-wide text-ink/50">
          {run.status}
          {run.engine ? ` · ${run.engine}` : ""}
        </p>
      </div>
      {run.warning && <p className="mt-1 text-ink/70">{run.warning}</p>}
      {run.error && <p className="mt-1 text-rose-800">{run.error}</p>}
      {run.extracted && (
        <dl className="mt-2 grid gap-1 sm:grid-cols-2">
          {Object.entries(run.extracted)
            .filter(([, value]) => value !== null && value !== "")
            .map(([key, value]) => (
              <div key={key}>
                <dt className="text-xs uppercase tracking-wide text-ink/50">{key.replaceAll("_", " ")}</dt>
                <dd>{String(value)}</dd>
              </div>
            ))}
        </dl>
      )}
      {run.applied_fields.length > 0 && (
        <p className="mt-2 text-xs text-ink/50">Filled empty fields: {run.applied_fields.join(", ")}</p>
      )}
      {run.raw_text && (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-forest">Show OCR text</summary>
          <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-ink/5 p-2 text-xs">{run.raw_text}</pre>
        </details>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" onClick={onFillEmpty} className="rounded border border-forest px-3 py-1 text-xs text-forest">
          Fill empty verification fields
        </button>
        <button type="button" onClick={onRerun} className="rounded border border-ink/20 px-3 py-1 text-xs">
          Re-run OCR
        </button>
      </div>
    </div>
  );
}
