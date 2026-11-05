from dataclasses import dataclass
from datetime import datetime, timezone

from app.ai import chain_mismatch
from app.models import Application, ApplicationStatus

CLOSED_STATUSES = {ApplicationStatus.APPROVED, ApplicationStatus.REJECTED}

NEXT_ACTION = {
    ApplicationStatus.SUBMITTED: "Send to field verification",
    ApplicationStatus.FIELD_VERIFICATION: "Mark ready for decision",
    ApplicationStatus.READY_FOR_DECISION: "Approve, reject, or return",
    ApplicationStatus.RETURNED: "Re-open at intake",
    ApplicationStatus.APPROVED: "File is closed",
    ApplicationStatus.REJECTED: "File is closed",
}


@dataclass(frozen=True)
class Attention:
    rank: int
    reason: str
    next_action: str
    mismatch: dict
    closed: bool


def is_flagged(application: Application) -> bool:
    return bool(chain_mismatch(application.transferor_name, application.recorded_owner_name)["flagged"])


def attention_for(application: Application) -> Attention:
    mismatch = chain_mismatch(application.transferor_name, application.recorded_owner_name)
    flagged = bool(mismatch["flagged"])
    status = application.status
    closed = status in CLOSED_STATUSES
    next_action = NEXT_ACTION[status]

    if status == ApplicationStatus.APPROVED:
        return Attention(90, "Approved", next_action, mismatch, True)
    if status == ApplicationStatus.REJECTED:
        return Attention(91, "Rejected", next_action, mismatch, True)
    if status == ApplicationStatus.READY_FOR_DECISION and flagged:
        return Attention(1, "Ownership mismatch · ready to decide", next_action, mismatch, False)
    if status == ApplicationStatus.READY_FOR_DECISION:
        return Attention(2, "Waiting on your decision", next_action, mismatch, False)
    if status == ApplicationStatus.FIELD_VERIFICATION and flagged:
        return Attention(3, "Ownership mismatch · field check due", next_action, mismatch, False)
    if status == ApplicationStatus.RETURNED:
        return Attention(4, "Returned to applicant", next_action, mismatch, False)
    if status == ApplicationStatus.FIELD_VERIFICATION:
        return Attention(5, "Field check due", next_action, mismatch, False)
    if status == ApplicationStatus.SUBMITTED and flagged:
        return Attention(6, "Ownership mismatch · new intake", next_action, mismatch, False)
    if status == ApplicationStatus.SUBMITTED:
        return Attention(7, "New intake", next_action, mismatch, False)
    return Attention(80, status.value, next_action, mismatch, closed)


def wait_key(application: Application) -> datetime:
    stamp = application.updated_at or application.created_at
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp


def attention_sort_key(application: Application) -> tuple:
    info = attention_for(application)
    return (info.rank, wait_key(application))
