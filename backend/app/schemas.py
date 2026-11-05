import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import ApplicationStatus


class ApplicationCreate(BaseModel):
    applicant_name: str
    mouza: str
    jl_number: int
    dag_number: int
    khatian_number: int
    transferor_name: str | None = None
    recorded_owner_name: str | None = None
    khajna_status: str | None = None


class ApplicationUpdate(BaseModel):
    applicant_name: str | None = None
    mouza: str | None = None
    jl_number: int | None = None
    dag_number: int | None = None
    khatian_number: int | None = None
    transferor_name: str | None = None
    recorded_owner_name: str | None = None
    khajna_status: str | None = None


class TransitionRequest(BaseModel):
    new_status: ApplicationStatus
    officer_remarks: str | None = None
    language: str = Field(default="en", pattern="^(en|bn)$")


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    previous_status: ApplicationStatus | None
    new_status: ApplicationStatus
    action_taken_by: uuid.UUID
    ai_flags_triggered: Any | None
    officer_remarks: str | None
    timestamp: datetime


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applicant_name: str
    mouza: str
    jl_number: int
    dag_number: int
    khatian_number: int
    transferor_name: str | None
    recorded_owner_name: str | None
    khajna_status: str | None
    sale_deed_path: str | None
    porcha_path: str | None
    status: ApplicationStatus
    assigned_officer_id: uuid.UUID
    created_at: datetime
    history: list[HistoryOut] = []
    mismatch_flag: dict | None = None


class QueueSummary(BaseModel):
    submitted: int
    field_verification: int
    ready_for_decision: int
    returned: int
    high_priority_discrepancies: int


class ExtractRequest(BaseModel):
    raw_text: str


class ExtractedMetadata(BaseModel):
    applicant_name: str | None = None
    mouza: str | None = None
    jl_number: int | None = None
    dag_number: int | None = None
    khatian_number: int | None = None
    transferor_name: str | None = None
    recorded_owner_name: str | None = None


class NoticeRequest(BaseModel):
    missing_items: list[str]
    language: str = "en"
    applicant_name: str
    mouza: str
