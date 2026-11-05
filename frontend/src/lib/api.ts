import type { Application, ApplicationDraft, QueueSummary } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  summary: () => request<QueueSummary>("/applications/queue/summary"),
  list: () => request<Application[]>("/applications"),
  get: (id: string) => request<Application>(`/applications/${id}`),
  create: (payload: ApplicationDraft) =>
    request<Application>("/applications", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: Partial<ApplicationDraft>) =>
    request<Application>(`/applications/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  transition: (id: string, new_status: string, officer_remarks?: string, language = "en") =>
    request<Application>(`/applications/${id}/transition`, {
      method: "POST",
      body: JSON.stringify({ new_status, officer_remarks, language }),
    }),
  extract: (raw_text: string) =>
    request<Partial<ApplicationDraft>>("/ai/extract", {
      method: "POST",
      body: JSON.stringify({ raw_text }),
    }),
  upload: async (id: string, files: { saleDeed?: File; porcha?: File }) => {
    const form = new FormData();
    if (files.saleDeed) form.append("sale_deed", files.saleDeed);
    if (files.porcha) form.append("porcha", files.porcha);
    return request<Application>(`/applications/${id}/documents`, { method: "POST", body: form });
  },
};
