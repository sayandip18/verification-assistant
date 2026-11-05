import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import ApplicationStatus, DocumentType, OfficerRole, PipelineStatus


class LoginRequest(BaseModel):
    email: str
    password: str


class OfficerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: str
    email: str
    full_name: str
    role: OfficerRole
    office_code: str | None
    is_active: bool


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
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_type: DocumentType
    blob_key: str
    original_filename: str
    content_type: str
    size_bytes: int
    uploaded_by_officer_id: uuid.UUID
    created_at: datetime


class ExtractedMetadata(BaseModel):
    applicant_name: str | None = None
    mouza: str | None = None
    jl_number: int | None = None
    dag_number: int | None = None
    khatian_number: int | None = None
    transferor_name: str | None = None
    recorded_owner_name: str | None = None
    khajna_status: str | None = None


class ExtractRequest(BaseModel):
    raw_text: str
    document_type: DocumentType | None = None


class OcrResultOut(BaseModel):
    document_id: uuid.UUID | None = None
    document_type: DocumentType | None = None
    original_filename: str | None = None
    status: PipelineStatus
    engine: str | None = None
    raw_text: str | None = None
    extracted: ExtractedMetadata | None = None
    applied_fields: list[str] = []
    warning: str | None = None
    error: str | None = None
    created_at: datetime


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
    status: ApplicationStatus
    assigned_officer_id: uuid.UUID
    created_by_officer_id: uuid.UUID
    created_at: datetime
    history: list[HistoryOut] = []
    documents: list[DocumentOut] = []
    mismatch_flag: dict | None = None
    ocr_results: list[OcrResultOut] = []
    attention_rank: int = 7
    attention_reason: str | None = None
    next_action: str | None = None


class QueueSummary(BaseModel):
    submitted: int
    field_verification: int
    ready_for_decision: int
    returned: int
    high_priority_discrepancies: int


class OcrScanOut(BaseModel):
    status: PipelineStatus
    engine: str | None = None
    raw_text: str = ""
    extracted: ExtractedMetadata
    warning: str | None = None
    error: str | None = None
    page_count: int | None = None


class NoticeRequest(BaseModel):
    missing_items: list[str]
    language: str = "en"
    applicant_name: str
    mouza: str
