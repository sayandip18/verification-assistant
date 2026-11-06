import type {
  Application,
  ApplicationDraft,
  ExtractedMetadata,
  NoticeDraft,
  Officer,
  OcrScan,
  QueueSummary,
} from "./types";

export type TransitionOptions = {
  officer_remarks?: string;
  language?: "en" | "bn";
  notice?: string;
  notice_source?: "ai" | "ai_edited" | "officer";
  notice_ai_run_id?: string;
};

const API_URL = "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (response.status === 204) {
    return undefined as T;
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(response.status, detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<Officer>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request<{ status: string }>("/auth/logout", { method: "POST" }),
  me: () => request<Officer>("/auth/me"),
  summary: () => request<QueueSummary>("/applications/queue/summary"),
  list: (params?: { view?: "open" | "all"; status?: string; flagged?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.view) query.set("view", params.view);
    if (params?.status) query.set("status", params.status);
    if (params?.flagged) query.set("flagged", "true");
    const suffix = query.toString() ? `?${query}` : "";
    return request<Application[]>(`/applications${suffix}`);
  },
  get: (id: string) => request<Application>(`/applications/${id}`),
  create: (payload: ApplicationDraft) =>
    request<Application>("/applications", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: Partial<ApplicationDraft>) =>
    request<Application>(`/applications/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  transition: (id: string, new_status: string, options: TransitionOptions = {}) =>
    request<Application>(`/applications/${id}/transition`, {
      method: "POST",
      body: JSON.stringify({ new_status, language: "en", ...options }),
    }),
  chainCheck: (id: string) => request<Application>(`/applications/${id}/chain-check`, { method: "POST" }),
  draftNotice: (id: string, officer_notes: string, language: "en" | "bn") =>
    request<NoticeDraft>(`/applications/${id}/notice-draft`, {
      method: "POST",
      body: JSON.stringify({ officer_notes, language }),
    }),
  extract: (raw_text: string, document_type?: string) =>
    request<ExtractedMetadata>("/ai/extract", {
      method: "POST",
      body: JSON.stringify({ raw_text, document_type: document_type || null }),
    }),
  ocrFile: async (file: File, document_type?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (document_type) form.append("document_type", document_type);
    return request<OcrScan>("/ai/ocr", { method: "POST", body: form });
  },
  rerunOcr: (applicationId: string, documentId: string) =>
    request<Application>(`/applications/${applicationId}/documents/${documentId}/ocr`, { method: "POST" }),
  upload: async (id: string, files: { saleDeed?: File; porcha?: File }) => {
    const form = new FormData();
    if (files.saleDeed) form.append("sale_deed", files.saleDeed);
    if (files.porcha) form.append("porcha", files.porcha);
    return request<Application>(`/applications/${id}/documents`, { method: "POST", body: form });
  },
};
