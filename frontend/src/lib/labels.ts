import type { ApplicationStatus } from "./types";

export const STATUS_LABEL: Record<ApplicationStatus, string> = {
  SUBMITTED: "Intake",
  FIELD_VERIFICATION: "Field verification",
  READY_FOR_DECISION: "Ready for decision",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  RETURNED: "Returned",
};

export const STATUS_CLASS: Record<ApplicationStatus, string> = {
  SUBMITTED: "bg-sky-100 text-sky-900",
  FIELD_VERIFICATION: "bg-amber-100 text-amber-900",
  READY_FOR_DECISION: "bg-violet-100 text-violet-900",
  APPROVED: "bg-emerald-100 text-emerald-900",
  REJECTED: "bg-rose-100 text-rose-900",
  RETURNED: "bg-orange-100 text-orange-900",
};

export const NEXT_ACTIONS: Partial<Record<ApplicationStatus, { status: ApplicationStatus; label: string }[]>> = {
  SUBMITTED: [{ status: "FIELD_VERIFICATION", label: "Send to field verification" }],
  FIELD_VERIFICATION: [{ status: "READY_FOR_DECISION", label: "Mark ready for decision" }],
  READY_FOR_DECISION: [
    { status: "APPROVED", label: "Approve mutation" },
    { status: "REJECTED", label: "Reject" },
    { status: "RETURNED", label: "Return to applicant" },
  ],
  RETURNED: [{ status: "SUBMITTED", label: "Re-open at intake" }],
};
