export type ApplicationStatus =
  | "SUBMITTED"
  | "FIELD_VERIFICATION"
  | "READY_FOR_DECISION"
  | "APPROVED"
  | "REJECTED"
  | "RETURNED";

export type DocumentType = "SALE_DEED" | "PORCHA" | "OTHER";

export type OfficerRole = "REVENUE_INSPECTOR" | "EXTENSION_OFFICER" | "SUPERVISOR" | "ADMIN";

export type Officer = {
  id: string;
  employee_id: string;
  email: string;
  full_name: string;
  role: OfficerRole;
  office_code: string | null;
  is_active: boolean;
};

export type ChainVerdict = "MATCH" | "LIKELY_SAME_PERSON" | "POSSIBLE_LINK" | "MISMATCH" | "INSUFFICIENT_DATA";

export type MismatchFlag = {
  flagged: boolean;
  severity: "info" | "ok" | "medium" | "high";
  message: string;
  verdict?: ChainVerdict;
  confidence?: "low" | "medium" | "high" | null;
  summary?: string | null;
  summary_bn?: string | null;
  reasons?: string[];
  suggested_checks?: string[];
  documents_to_request?: string[];
  engine?: "llm" | "rules";
  model?: string | null;
  warning?: string | null;
  checked_at?: string;
  stale?: boolean;
};

export type HistoryEntry = {
  id: string;
  previous_status: ApplicationStatus | null;
  new_status: ApplicationStatus;
  action_taken_by: string;
  ai_flags_triggered: unknown;
  officer_remarks: string | null;
  created_at: string;
  actor_name: string | null;
  actor_role: OfficerRole | null;
};

export type AiRunSummary = {
  id: string;
  pipeline: "OCR" | "CHAIN_CHECK" | "NOTICE";
  status: "PENDING" | "SUCCEEDED" | "FAILED";
  engine: "llm" | "rules" | string | null;
  model: string | null;
  summary: string | null;
  detail: Record<string, unknown>;
  document_id: string | null;
  created_at: string;
};

export type NoticeDraft = {
  notice: string;
  language: "en" | "bn";
  engine: "llm" | "rules";
  model: string | null;
  warning: string | null;
  ai_run_id: string;
};

export type Document = {
  id: string;
  document_type: DocumentType;
  blob_key: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_by_officer_id: string;
  created_at: string;
};

export type ExtractedMetadata = {
  applicant_name: string | null;
  mouza: string | null;
  jl_number: number | null;
  dag_number: number | null;
  khatian_number: number | null;
  transferor_name: string | null;
  recorded_owner_name: string | null;
  khajna_status: string | null;
};

export type OcrResult = {
  document_id: string | null;
  document_type: DocumentType | null;
  original_filename: string | null;
  status: "PENDING" | "SUCCEEDED" | "FAILED";
  engine: string | null;
  raw_text: string | null;
  extracted: ExtractedMetadata | null;
  applied_fields: string[];
  warning: string | null;
  error: string | null;
  created_at: string;
};

export type OcrScan = {
  status: "PENDING" | "SUCCEEDED" | "FAILED";
  engine: string | null;
  raw_text: string;
  extracted: ExtractedMetadata;
  warning: string | null;
  error: string | null;
  page_count: number | null;
};

export type Application = {
  id: string;
  applicant_name: string;
  mouza: string;
  jl_number: number;
  dag_number: number;
  khatian_number: number;
  transferor_name: string | null;
  recorded_owner_name: string | null;
  khajna_status: string | null;
  status: ApplicationStatus;
  assigned_officer_id: string;
  created_by_officer_id: string;
  created_at: string;
  history: HistoryEntry[];
  documents: Document[];
  mismatch_flag: MismatchFlag | null;
  ocr_results: OcrResult[];
  ai_runs: AiRunSummary[];
  attention_rank: number;
  attention_reason: string | null;
  next_action: string | null;
};

export type QueueSummary = {
  submitted: number;
  field_verification: number;
  ready_for_decision: number;
  returned: number;
  high_priority_discrepancies: number;
  approved: number;
  rejected: number;
};

export type ApplicationDraft = {
  applicant_name: string;
  mouza: string;
  jl_number: number;
  dag_number: number;
  khatian_number: number;
  transferor_name: string;
  recorded_owner_name: string;
  khajna_status: string;
};
