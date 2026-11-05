export type ApplicationStatus =
  | "SUBMITTED"
  | "FIELD_VERIFICATION"
  | "READY_FOR_DECISION"
  | "APPROVED"
  | "REJECTED"
  | "RETURNED";

export type MismatchFlag = {
  flagged: boolean;
  severity: "info" | "ok" | "high";
  message: string;
};

export type HistoryEntry = {
  id: string;
  previous_status: ApplicationStatus | null;
  new_status: ApplicationStatus;
  action_taken_by: string;
  ai_flags_triggered: unknown;
  officer_remarks: string | null;
  timestamp: string;
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
  sale_deed_path: string | null;
  porcha_path: string | null;
  status: ApplicationStatus;
  assigned_officer_id: string;
  created_at: string;
  history: HistoryEntry[];
  mismatch_flag: MismatchFlag | null;
};

export type QueueSummary = {
  submitted: number;
  field_verification: number;
  ready_for_decision: number;
  returned: number;
  high_priority_discrepancies: number;
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
