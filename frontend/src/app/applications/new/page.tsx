"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import type { ApplicationDraft } from "@/lib/types";

const empty: ApplicationDraft = {
  applicant_name: "",
  mouza: "",
  jl_number: 0,
  dag_number: 0,
  khatian_number: 0,
  transferor_name: "",
  recorded_owner_name: "",
  khajna_status: "",
};

export default function NewApplicationPage() {
  const router = useRouter();
  const [form, setForm] = useState<ApplicationDraft>(empty);
  const [ocr, setOcr] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function setField<K extends keyof ApplicationDraft>(key: K, value: ApplicationDraft[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function applyExtract() {
    setError(null);
    try {
      const extracted = await api.extract(ocr);
      setForm((current) => ({
        ...current,
        ...Object.fromEntries(
          Object.entries(extracted).filter(([, value]) => value !== null && value !== undefined && value !== "")
        ),
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Extraction failed");
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const created = await api.create(form);
      router.push(`/applications/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-5">
      <form onSubmit={onSubmit} className="space-y-4 lg:col-span-3">
        <h1 className="text-2xl font-semibold">Stage 1: Intake and digitization</h1>
        {error && <p className="rounded bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>}
        <Field label="Applicant name">
          <input
            required
            className="mt-1 w-full rounded border border-ink/20 bg-white px-3 py-2"
            value={form.applicant_name}
            onChange={(e) => setField("applicant_name", e.target.value)}
          />
        </Field>
        <Field label="Mouza">
          <input
            required
            className="mt-1 w-full rounded border border-ink/20 bg-white px-3 py-2"
            value={form.mouza}
            onChange={(e) => setField("mouza", e.target.value)}
          />
        </Field>
        <div className="grid grid-cols-3 gap-3">
          <Field label="J.L. No.">
            <input
              type="number"
              required
              className="mt-1 w-full rounded border border-ink/20 bg-white px-3 py-2"
              value={form.jl_number || ""}
              onChange={(e) => setField("jl_number", Number(e.target.value))}
            />
          </Field>
          <Field label="Dag / Plot No.">
            <input
              type="number"
              required
              className="mt-1 w-full rounded border border-ink/20 bg-white px-3 py-2"
              value={form.dag_number || ""}
              onChange={(e) => setField("dag_number", Number(e.target.value))}
            />
          </Field>
          <Field label="Khatian No.">
            <input
              type="number"
              required
              className="mt-1 w-full rounded border border-ink/20 bg-white px-3 py-2"
              value={form.khatian_number || ""}
              onChange={(e) => setField("khatian_number", Number(e.target.value))}
            />
          </Field>
        </div>
        <Field label="Transferor on sale deed (Dalil)">
          <input
            className="mt-1 w-full rounded border border-ink/20 bg-white px-3 py-2"
            value={form.transferor_name}
            onChange={(e) => setField("transferor_name", e.target.value)}
          />
        </Field>
        <Field label="Recorded owner on Porcha">
          <input
            className="mt-1 w-full rounded border border-ink/20 bg-white px-3 py-2"
            value={form.recorded_owner_name}
            onChange={(e) => setField("recorded_owner_name", e.target.value)}
          />
        </Field>
        <Field label="Khajna / tax status">
          <input
            className="mt-1 w-full rounded border border-ink/20 bg-white px-3 py-2"
            value={form.khajna_status}
            onChange={(e) => setField("khajna_status", e.target.value)}
          />
        </Field>
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-forest px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          Save application
        </button>
      </form>

      <aside className="space-y-3 rounded-lg border border-ink/10 bg-white p-4 lg:col-span-2">
        <h2 className="font-medium">AI field pre-fill</h2>
        <p className="text-sm text-ink/60">
          Paste OCR text from a Dalil or Porcha. The extractor looks for labelled fields such as
          Applicant, Mouza, J.L. No., Dag, Khatian, Transferor, Recorded owner.
        </p>
        <textarea
          className="min-h-40 w-full rounded border border-ink/20 bg-white px-3 py-2 text-sm"
          value={ocr}
          onChange={(e) => setOcr(e.target.value)}
          placeholder="Applicant: Aparna Das&#10;Mouza: Shyamnagar&#10;J.L. No.: 42"
        />
        <button type="button" onClick={applyExtract} className="rounded border border-forest px-3 py-1.5 text-sm text-forest">
          Extract into form
        </button>
      </aside>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-ink/70">{label}</span>
      {children}
    </label>
  );
}
