import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    FIELD_VERIFICATION = "FIELD_VERIFICATION"
    READY_FOR_DECISION = "READY_FOR_DECISION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    applicant_name: Mapped[str] = mapped_column(String(255))
    mouza: Mapped[str] = mapped_column(String(255))
    jl_number: Mapped[int] = mapped_column(Integer)
    dag_number: Mapped[int] = mapped_column(Integer)
    khatian_number: Mapped[int] = mapped_column(Integer)
    transferor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    khajna_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sale_deed_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    porcha_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=32),
        default=ApplicationStatus.SUBMITTED,
    )
    assigned_officer_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    history: Mapped[list["ApplicationHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationHistory.timestamp"
    )


class ApplicationHistory(Base):
    __tablename__ = "application_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("applications.id"))
    previous_status: Mapped[ApplicationStatus | None] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=32), nullable=True
    )
    new_status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=32)
    )
    action_taken_by: Mapped[uuid.UUID] = mapped_column(Uuid)
    ai_flags_triggered: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    officer_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="history")
