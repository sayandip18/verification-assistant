import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OfficerRole(str, enum.Enum):
    REVENUE_INSPECTOR = "REVENUE_INSPECTOR"
    EXTENSION_OFFICER = "EXTENSION_OFFICER"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    FIELD_VERIFICATION = "FIELD_VERIFICATION"
    READY_FOR_DECISION = "READY_FOR_DECISION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"


class DocumentType(str, enum.Enum):
    SALE_DEED = "SALE_DEED"
    PORCHA = "PORCHA"
    OTHER = "OTHER"


class PipelineName(str, enum.Enum):
    OCR = "OCR"
    CHAIN_CHECK = "CHAIN_CHECK"
    NOTICE = "NOTICE"


class PipelineStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class Officer(Base):
    __tablename__ = "officers"
    __table_args__ = (Index("ix_officers_email", "email", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[str] = mapped_column(String(64), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[OfficerRole] = mapped_column(
        Enum(OfficerRole, native_enum=False, length=32), default=OfficerRole.REVENUE_INSPECTOR
    )
    office_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    assigned_applications: Mapped[list["Application"]] = relationship(
        back_populates="assigned_officer", foreign_keys="Application.assigned_officer_id"
    )


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (Index("ix_applications_status", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_name: Mapped[str] = mapped_column(String(255))
    mouza: Mapped[str] = mapped_column(String(255))
    jl_number: Mapped[int] = mapped_column(Integer)
    dag_number: Mapped[int] = mapped_column(Integer)
    khatian_number: Mapped[int] = mapped_column(Integer)
    transferor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    khajna_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=32),
        default=ApplicationStatus.SUBMITTED,
    )
    assigned_officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("officers.id", ondelete="RESTRICT")
    )
    created_by_officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("officers.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    assigned_officer: Mapped[Officer] = relationship(foreign_keys=[assigned_officer_id])
    created_by_officer: Mapped[Officer] = relationship(foreign_keys=[created_by_officer_id])
    history: Mapped[list["ApplicationHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationHistory.created_at"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    ai_runs: Mapped[list["AiRun"]] = relationship(back_populates="application", cascade="all, delete-orphan")


class ApplicationHistory(Base):
    __tablename__ = "application_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    previous_status: Mapped[ApplicationStatus | None] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=32), nullable=True
    )
    new_status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=32)
    )
    action_taken_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("officers.id", ondelete="RESTRICT")
    )
    ai_flags_triggered: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    officer_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="history")
    officer: Mapped[Officer] = relationship()


class Document(Base):
    """Metadata only. File bytes live in blob storage under blob_key."""

    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_application_id", "application_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, native_enum=False, length=32))
    blob_key: Mapped[str] = mapped_column(String(512), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_by_officer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("officers.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="documents")


class AiRun(Base):
    """Log for OCR / chain-check / notice pipeline runs."""

    __tablename__ = "ai_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    pipeline: Mapped[PipelineName] = mapped_column(Enum(PipelineName, native_enum=False, length=32))
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus, native_enum=False, length=32), default=PipelineStatus.PENDING
    )
    input_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application | None] = relationship(back_populates="ai_runs")
