"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { NEXT_ACTIONS, STATUS_CLASS, STATUS_LABEL } from "@/lib/labels";
import { mergeExtracted } from "@/lib/extract";
import type {
  AiRunSummary,
  Application,
  ApplicationStatus,
  ChainVerdict,
  HistoryEntry,
  MismatchFlag,
  NoticeDraft,
  OcrResult,
  OfficerRole,
} from "@/lib/types";

const VERDICT_LABEL: Record<ChainVerdict, string> = {
  MATCH: "Names match",
  LIKELY_SAME_PERSON: "Likely same person",
  POSSIBLE_LINK: "Link documents needed",
  MISMATCH: "Ownership mismatch",
  INSUFFICIENT_DATA: "Not enough information",
};

const ROLE_LABEL: Record<OfficerRole, string> = {
  REVENUE_INSPECTOR: "Revenue Inspector",
  EXTENSION_OFFICER: "Extension Officer",
  SUPERVISOR: "Supervisor",
  ADMIN: "Administrator",
};

const FIELD_LABEL: Record<string, string> = {
  applicant_name: "Applicant",
  mouza: "Mouza",
  jl_number: "J.L. No.",
  dag_number: "Dag No.",
  khatian_number: "Khatian No.",
  transferor_name: "Transferor",
  recorded_owner_name: "Recorded owner",
  khajna_status: "Khajna status",
};

function severityClass(flag: MismatchFlag | null | undefined) {
  if (!flag) return "border-ink/10 bg-white";
  if (flag.severity === "high") return "border-rose-300 bg-rose-50 text-rose-950";
  if (flag.severity === "medium") return "border-amber-300 bg-amber-50 text-amber-950";
  if (flag.severity === "ok") return "border-emerald-200 bg-emerald-50 text-emerald-950";
  return "border-ink/10 bg-white";
}

function EngineBadge({ engine, model }: { engine?: string | null; model?: string | null }) {
  if (!engine) return null;
  const ai = engine === "llm";
  return (
    <span
      title={ai && model ? `Model: ${model}` : undefined}
      className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${ai ? "bg-violet-100 text-violet-900" : "bg-ink/10 text-ink/70"}`}
    >
      {ai ? "AI assessment" : "Rule-based"}
    </span>
  );
}

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<Application | null>(null);
  const [remarks, setRemarks] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [transferor, setTransferor] = useState("");
  const [owner, setOwner] = useState("");
  const [khajna, setKhajna] = useState("");
  const [checking, setChecking] = useState(false);
  const [busy, setBusy] = useState(false);

  // Return flow: officer notes -> AI draft -> officer edits -> confirm.
  const [returning, setReturning] = useState(false);
  const [returnNotes, setReturnNotes] = useState("");
  const [language, setLanguage] = useState<"en" | "bn">("bn");
  const [draft, setDraft] = useState<NoticeDraft | null>(null);
  const [noticeText, setNoticeText] = useState("");
  const [drafting, setDrafting] = useState(false);

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

  async function runChainCheck() {
    if (!item) return;
    setError(null);
    setChecking(true);
    try {
      applyItem(await api.chainCheck(item.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chain check failed");
    } finally {
      setChecking(false);
    }
  }

  async function move(status: ApplicationStatus) {
    if (!item) return;
    if (status === "RETURNED") {
      openReturn();
      return;
    }
    if (status === "APPROVED" && item.mismatch_flag?.flagged) {
      const ok = window.confirm(
        `The ownership check raised a concern:\n\n${item.mismatch_flag.message}\n\nApprove this mutation anyway?`
      );
      if (!ok) return;
    }
    setError(null);
    setBusy(true);
    try {
      applyItem(await api.transition(item.id, status, { officer_remarks: remarks || undefined }));
      setRemarks("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transition failed");
    } finally {
      setBusy(false);
    }
  }

  function openReturn() {
    const suggested = item?.mismatch_flag?.documents_to_request ?? [];
    const notes = [remarks.trim(), ...suggested].filter(Boolean).join("\n");
    setReturnNotes(notes);
    setDraft(null);
    setNoticeText("");
    setReturning(true);
  }

  async function requestDraft() {
    if (!item) return;
    setError(null);
    setDrafting(true);
    try {
      const result = await api.draftNotice(item.id, returnNotes, language);
      setDraft(result);
      setNoticeText(result.notice);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not draft the notice");
    } finally {
      setDrafting(false);
    }
  }

  async function confirmReturn() {
    if (!item || !noticeText.trim()) return;
    const source = !draft ? "officer" : noticeText.trim() === draft.notice.trim() ? "ai" : "ai_edited";
    setError(null);
    setBusy(true);
    try {
      applyItem(
        await api.transition(item.id, "RETURNED", {
          officer_remarks: returnNotes.trim() || undefined,
          language,
          notice: noticeText.trim(),
          notice_source: source,
          notice_ai_run_id: draft?.ai_run_id,
        })
      );
      setReturning(false);
      setRemarks("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Return failed");
    } finally {
      setBusy(false);
    }
  }

  if (!item) {
    return <p className="text-sm text-ink/60">{error ?? "Loading…"}</p>;
  }

  const actions = NEXT_ACTIONS[item.status] ?? [];
  const chainEditable = item.status === "SUBMITTED" || item.status === "FIELD_VERIFICATION" || item.status === "READY_FOR_DECISION";

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

      <ChainCard
        flag={item.mismatch_flag}
        onRun={chainEditable ? runChainCheck : undefined}
        running={checking}
      />

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
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={saveFieldNotes} className="rounded border border-forest px-3 py-1.5 text-sm text-forest">
              Save verification notes
            </button>
            {chainEditable && (
              <button
                type="button"
                onClick={runChainCheck}
                disabled={checking}
                className="rounded border border-violet-400 px-3 py-1.5 text-sm text-violet-900 disabled:opacity-50"
              >
                {checking ? "Checking ownership chain…" : "Run AI chain check"}
              </button>
            )}
          </div>
          <p className="text-xs text-ink/50">Save your changes first; the check reads the saved names and the uploaded scans.</p>
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
            You make the final call. AI can check the ownership chain and draft a return notice; it cannot approve, reject or
            send anything.
          </p>

          {!returning && (
            <>
              <textarea
                className="min-h-24 w-full rounded border border-ink/20 px-3 py-2 text-sm"
                placeholder="Officer remarks (recorded in the history)"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                {actions.map((action) => (
                  <button
                    key={action.status}
                    type="button"
                    disabled={busy}
                    onClick={() => move(action.status)}
                    className={`rounded px-3 py-1.5 text-sm text-white disabled:opacity-50 ${
                      action.status === "REJECTED" ? "bg-rose-700" : action.status === "RETURNED" ? "bg-amber-700" : "bg-forest"
                    }`}
                  >
                    {action.label}
                  </button>
                ))}
                {actions.length === 0 && <p className="text-sm text-ink/50">This file is closed.</p>}
              </div>
            </>
          )}

          {returning && (
            <div className="space-y-3 rounded border border-amber-200 bg-amber-50/60 p-3">
              <p className="text-sm font-medium">Return to applicant</p>
              <label className="block text-sm">
                What is missing or needs correcting? (one item per line)
                <textarea
                  className="mt-1 min-h-20 w-full rounded border border-ink/20 bg-white px-3 py-2 text-sm"
                  value={returnNotes}
                  onChange={(e) => setReturnNotes(e.target.value)}
                />
              </label>
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <label className="flex items-center gap-2">
                  Notice language
                  <select
                    className="rounded border border-ink/20 bg-white px-2 py-1"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value as "en" | "bn")}
                  >
                    <option value="bn">বাংলা (Bengali)</option>
                    <option value="en">English</option>
                  </select>
                </label>
                <button
                  type="button"
                  onClick={requestDraft}
                  disabled={drafting}
                  className="rounded border border-violet-400 bg-white px-3 py-1 text-violet-900 disabled:opacity-50"
                >
                  {drafting ? "Drafting…" : draft ? "Redraft with AI" : "Draft notice with AI"}
                </button>
              </div>
              {draft && (
                <div className="flex flex-wrap items-center gap-2 text-xs text-ink/60">
                  <EngineBadge engine={draft.engine} model={draft.model} />
                  {draft.warning && <span>{draft.warning}</span>}
                </div>
              )}
              <label className="block text-sm">
                Notice to the applicant (review and edit before confirming)
                <textarea
                  lang={language}
                  className="mt-1 min-h-40 w-full rounded border border-ink/20 bg-white px-3 py-2 text-sm"
                  placeholder="Draft with AI, or write the notice yourself."
                  value={noticeText}
                  onChange={(e) => setNoticeText(e.target.value)}
                />
              </label>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy || !noticeText.trim()}
                  onClick={confirmReturn}
                  className="rounded bg-amber-700 px-3 py-1.5 text-sm text-white disabled:opacity-50"
                >
                  Confirm notice and return file
                </button>
                <button type="button" onClick={() => setReturning(false)} className="rounded border border-ink/20 px-3 py-1.5 text-sm">
                  Cancel
                </button>
              </div>
            </div>
          )}
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
                  run.extracted as Record<string, unknown>
                );
                setTransferor(String(filled.transferor_name ?? ""));
                setOwner(String(filled.recorded_owner_name ?? ""));
                setKhajna(String(filled.khajna_status ?? ""));
              }}
            />
          ))}
        </section>
      )}

      <Timeline history={item.history} aiRuns={item.ai_runs ?? []} />
    </div>
  );
}

function ChainCard({
  flag,
  onRun,
  running,
}: {
  flag: MismatchFlag | null;
  onRun?: () => void;
  running: boolean;
}) {
  if (!flag) return null;
  const lists: [string, string[] | undefined][] = [
    ["Why", flag.reasons],
    ["Check in the field", flag.suggested_checks],
    ["Documents to ask for", flag.documents_to_request],
  ];
  return (
    <section className={`space-y-2 rounded-lg border px-4 py-3 text-sm ${severityClass(flag)}`}>
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium">Ownership chain check</p>
        {flag.verdict && <span className="rounded-full bg-white/70 px-2 py-0.5 text-xs font-medium">{VERDICT_LABEL[flag.verdict]}</span>}
        {flag.confidence && flag.engine === "llm" && <span className="text-xs opacity-70">{flag.confidence} confidence</span>}
        <EngineBadge engine={flag.engine} model={flag.model} />
        {flag.checked_at && <span className="text-xs opacity-60">checked {formatTime(flag.checked_at)}</span>}
      </div>
      <p>{flag.summary || flag.message}</p>
      {flag.summary_bn && (
        <p lang="bn" className="opacity-90">
          {flag.summary_bn}
        </p>
      )}
      {lists.some(([, items]) => items && items.length > 0) && (
        <div className="grid gap-3 pt-1 sm:grid-cols-3">
          {lists
            .filter(([, items]) => items && items.length > 0)
            .map(([title, items]) => (
              <div key={title}>
                <p className="text-xs font-medium uppercase tracking-wide opacity-70">{title}</p>
                <ul className="mt-1 list-disc space-y-0.5 pl-4">
                  {items!.map((entry) => (
                    <li key={entry}>{entry}</li>
                  ))}
                </ul>
              </div>
            ))}
        </div>
      )}
      {flag.warning && <p className="text-xs opacity-70">{flag.warning}</p>}
      {flag.engine === "rules" && onRun && (
        <p className="text-xs opacity-80">
          {flag.stale ? "Names changed since the last AI check. " : "Quick exact-name comparison only. "}
          <button type="button" onClick={onRun} disabled={running} className="font-medium underline disabled:opacity-50">
            {running ? "Running AI check…" : "Run the AI chain check"}
          </button>{" "}
          to handle spelling variants, Bengali/English names and inheritance links.
        </p>
      )}
      <p className="text-xs opacity-60">Advisory only. You decide.</p>
    </section>
  );
}

type TimelineItem =
  | { kind: "history"; at: string; entry: HistoryEntry }
  | { kind: "ai"; at: string; run: AiRunSummary };

type Filter = "all" | "status" | "ai" | "edits";

function historyKind(entry: HistoryEntry): string | undefined {
  const flags = entry.ai_flags_triggered as { kind?: string } | null;
  return flags && typeof flags === "object" ? flags.kind : undefined;
}

function Timeline({ history, aiRuns }: { history: HistoryEntry[]; aiRuns: AiRunSummary[] }) {
  const [filter, setFilter] = useState<Filter>("all");
  const items = useMemo(() => {
    const merged: TimelineItem[] = [
      ...history.map((entry) => ({ kind: "history" as const, at: entry.created_at, entry })),
      ...aiRuns.map((run) => ({ kind: "ai" as const, at: run.created_at, run })),
    ];
    merged.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
    return merged.filter((item) => {
      if (filter === "all") return true;
      if (filter === "ai") return item.kind === "ai";
      if (item.kind !== "history") return false;
      const isEdit = historyKind(item.entry) === "FIELD_UPDATE";
      return filter === "edits" ? isEdit : !isEdit;
    });
  }, [history, aiRuns, filter]);

  const filters: [Filter, string][] = [
    ["all", "Everything"],
    ["status", "Status & decisions"],
    ["edits", "Edits"],
    ["ai", "AI activity"],
  ];

  return (
    <section className="rounded-lg border border-ink/10 bg-white">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-ink/10 px-4 py-3">
        <h2 className="font-medium">History</h2>
        <div className="flex flex-wrap gap-1">
          {filters.map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setFilter(key)}
              className={`rounded-full px-2.5 py-1 text-xs ${filter === key ? "bg-forest text-white" : "bg-ink/5 text-ink/70"}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {items.length === 0 && <p className="px-4 py-3 text-sm text-ink/50">Nothing to show for this filter.</p>}
      <ol className="divide-y divide-ink/10">
        {items.map((item) =>
          item.kind === "history" ? (
            <HistoryRow key={`h-${item.entry.id}`} entry={item.entry} />
          ) : (
            <AiRow key={`a-${item.run.id}`} run={item.run} />
          )
        )}
      </ol>
    </section>
  );
}

function Meta({ at, actor, role }: { at: string; actor?: string | null; role?: OfficerRole | null }) {
  return (
    <p className="text-xs text-ink/50">
      {formatTime(at)}
      {actor && (
        <>
          {" · "}
          <span className="text-ink/70">{actor}</span>
          {role && `, ${ROLE_LABEL[role]}`}
        </>
      )}
    </p>
  );
}

function HistoryRow({ entry }: { entry: HistoryEntry }) {
  const flags = (entry.ai_flags_triggered ?? {}) as Record<string, unknown>;
  const kind = historyKind(entry);

  if (kind === "FIELD_UPDATE") {
    const changes = (flags.changes ?? {}) as Record<string, { from: unknown; to: unknown }>;
    return (
      <li className="flex gap-3 px-4 py-3 text-sm">
        <Dot className="bg-sky-500" />
        <div className="min-w-0 flex-1">
          <p className="font-medium">Details edited</p>
          <Meta at={entry.created_at} actor={entry.actor_name} role={entry.actor_role} />
          <ul className="mt-1 space-y-0.5">
            {Object.entries(changes).map(([field, change]) => (
              <li key={field}>
                <span className="text-ink/60">{FIELD_LABEL[field] ?? field}:</span>{" "}
                <span className="text-ink/50 line-through">{String(change.from ?? "empty")}</span> →{" "}
                <span>{String(change.to ?? "empty")}</span>
              </li>
            ))}
          </ul>
        </div>
      </li>
    );
  }

  const title = entry.previous_status
    ? `${STATUS_LABEL[entry.previous_status]} → ${STATUS_LABEL[entry.new_status]}`
    : "File opened at intake";
  const chain = (kind === "DECISION" ? flags.chain_at_decision : entry.new_status === "READY_FOR_DECISION" ? flags : null) as
    | MismatchFlag
    | null;
  const dotColor =
    entry.new_status === "APPROVED"
      ? "bg-emerald-600"
      : entry.new_status === "REJECTED"
        ? "bg-rose-600"
        : entry.new_status === "RETURNED"
          ? "bg-amber-600"
          : "bg-forest";
  const sourceLabel: Record<string, string> = {
    ai: "AI draft, confirmed by officer",
    ai_edited: "AI draft, edited by officer",
    officer: "Written by officer",
  };

  return (
    <li className="flex gap-3 px-4 py-3 text-sm">
      <Dot className={dotColor} />
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium">{title}</p>
          <span className={`rounded-full px-2 py-0.5 text-[11px] ${STATUS_CLASS[entry.new_status]}`}>
            {STATUS_LABEL[entry.new_status]}
          </span>
        </div>
        <Meta at={entry.created_at} actor={entry.actor_name} role={entry.actor_role} />
        {entry.officer_remarks && (
          <p>
            <span className="text-ink/60">Remarks: </span>
            {entry.officer_remarks}
          </p>
        )}
        {chain && chain.message && (
          <p className="text-xs text-ink/70">
            Ownership check at this point: {chain.verdict ? VERDICT_LABEL[chain.verdict] : chain.flagged ? "flagged" : "clear"}
            {chain.engine && ` (${chain.engine === "llm" ? "AI" : "rule-based"})`}. {chain.summary || chain.message}
          </p>
        )}
        {kind === "RETURN_NOTICE" && typeof flags.notice === "string" && (
          <div className="mt-1 rounded border border-amber-200 bg-amber-50/60 p-2">
            <p className="text-xs text-ink/60">
              Notice sent ({flags.language === "bn" ? "Bengali" : "English"}) ·{" "}
              {sourceLabel[String(flags.notice_source)] ?? "Officer"}
            </p>
            <p lang={String(flags.language ?? "en")} className="mt-1 whitespace-pre-wrap">
              {flags.notice}
            </p>
          </div>
        )}
      </div>
    </li>
  );
}

function AiRow({ run }: { run: AiRunSummary }) {
  const label = run.pipeline === "OCR" ? "OCR" : run.pipeline === "CHAIN_CHECK" ? "Ownership chain check" : "Return notice draft";
  const detail = run.detail as Record<string, unknown>;
  const verdict = detail.verdict as ChainVerdict | undefined;
  const failed = run.status === "FAILED";
  return (
    <li className="flex gap-3 px-4 py-3 text-sm">
      <Dot className={failed ? "bg-rose-400" : "bg-violet-400"} />
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium text-ink/80">{label}</p>
          {verdict && <span className="rounded-full bg-violet-50 px-2 py-0.5 text-[11px] text-violet-900">{VERDICT_LABEL[verdict]}</span>}
          <EngineBadge engine={run.engine} model={run.model} />
        </div>
        <p className="text-xs text-ink/50">{formatTime(run.created_at)} · system</p>
        {run.summary && <p className="text-ink/80">{run.summary}</p>}
        {run.pipeline === "CHAIN_CHECK" && Boolean(detail.transferor_name || detail.recorded_owner_name) && (
          <p className="text-xs text-ink/60">
            Compared transferor “{String(detail.transferor_name ?? "—")}” with recorded owner “
            {String(detail.recorded_owner_name ?? "—")}”
          </p>
        )}
        {typeof detail.warning === "string" && detail.warning && <p className="text-xs text-ink/60">{detail.warning}</p>}
        {run.pipeline === "NOTICE" && typeof detail.notice === "string" && (
          <details>
            <summary className="cursor-pointer text-xs text-forest">Show draft</summary>
            <p lang={String(detail.language ?? "en")} className="mt-1 whitespace-pre-wrap rounded bg-ink/5 p-2 text-xs">
              {detail.notice}
            </p>
          </details>
        )}
      </div>
    </li>
  );
}

function Dot({ className }: { className: string }) {
  return <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${className}`} aria-hidden />;
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
