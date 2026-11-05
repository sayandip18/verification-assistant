import uuid

from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.attention import CLOSED_STATUSES, attention_for, attention_sort_key
from app.blob import make_blob_key, put_bytes
from app.database import get_db
from app.deps import get_current_officer
from app.models import (
    AiRun,
    Application,
    ApplicationHistory,
    ApplicationStatus,
    Document,
    DocumentType,
    Officer,
    PipelineName,
)
from app.pipeline import run_chain_check, run_notice_draft, run_ocr
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    ExtractedMetadata,
    OcrResultOut,
    QueueSummary,
    TransitionRequest,
)
from app.state_machine import assert_transition

router = APIRouter(prefix="/applications", tags=["applications"])
LOAD_OPTIONS = (selectinload(Application.history), selectinload(Application.documents))
LOAD_DETAIL = (*LOAD_OPTIONS, selectinload(Application.ai_runs))


def _ocr_results(application: Application) -> list[OcrResultOut]:
    docs = {document.id: document for document in application.documents}
    latest: dict[uuid.UUID | None, AiRun] = {}
    for run in application.ai_runs:
        if run.pipeline != PipelineName.OCR:
            continue
        current = latest.get(run.document_id)
        if current is None or run.created_at >= current.created_at:
            latest[run.document_id] = run

    results: list[OcrResultOut] = []
    for run in latest.values():
        document = docs.get(run.document_id) if run.document_id else None
        output = run.output_payload or {}
        extracted_raw = output.get("extracted") or {}
        results.append(
            OcrResultOut(
                document_id=run.document_id,
                document_type=document.document_type if document else None,
                original_filename=document.original_filename if document else None,
                status=run.status,
                engine=output.get("engine"),
                raw_text=output.get("raw_text"),
                extracted=ExtractedMetadata.model_validate(extracted_raw) if extracted_raw else None,
                applied_fields=output.get("applied_fields") or [],
                warning=output.get("warning"),
                error=output.get("error"),
                created_at=run.created_at,
            )
        )
    results.sort(key=lambda item: item.created_at)
    return results


def _with_flag(application: Application, *, include_ocr: bool = True) -> ApplicationOut:
    payload = ApplicationOut.model_validate(application)
    info = attention_for(application)
    payload.mismatch_flag = info.mismatch
    payload.attention_rank = info.rank
    payload.attention_reason = info.reason
    payload.next_action = info.next_action
    if include_ocr:
        payload.ocr_results = _ocr_results(application)
    return payload


async def _get_application(application_id: uuid.UUID, db: AsyncSession) -> Application:
    result = await db.execute(
        select(Application)
        .options(*LOAD_DETAIL)
        .where(Application.id == application_id)
        .execution_options(populate_existing=True)
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


@router.get("/queue/summary", response_model=QueueSummary)
async def queue_summary(
    db: AsyncSession = Depends(get_db),
    _: Officer = Depends(get_current_officer),
) -> QueueSummary:
    result = await db.execute(select(Application))
    applications = result.scalars().all()
    discrepancies = 0
    counts = {status: 0 for status in ApplicationStatus}
    for application in applications:
        counts[application.status] += 1
        info = attention_for(application)
        if info.mismatch["flagged"] and not info.closed:
            discrepancies += 1
    return QueueSummary(
        submitted=counts[ApplicationStatus.SUBMITTED],
        field_verification=counts[ApplicationStatus.FIELD_VERIFICATION],
        ready_for_decision=counts[ApplicationStatus.READY_FOR_DECISION],
        returned=counts[ApplicationStatus.RETURNED],
        high_priority_discrepancies=discrepancies,
    )


@router.get("", response_model=list[ApplicationOut])
async def list_applications(
    db: AsyncSession = Depends(get_db),
    _: Officer = Depends(get_current_officer),
    view: Literal["open", "all"] = Query(default="open"),
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    flagged: bool = Query(default=False),
) -> list[ApplicationOut]:
    result = await db.execute(select(Application).options(*LOAD_OPTIONS))
    applications = list(result.scalars().unique().all())
    if view == "open":
        applications = [item for item in applications if item.status not in CLOSED_STATUSES]
    if status_filter is not None:
        applications = [item for item in applications if item.status == status_filter]
    if flagged:
        applications = [item for item in applications if attention_for(item).mismatch["flagged"]]
    applications.sort(key=attention_sort_key)
    return [_with_flag(item, include_ocr=False) for item in applications]


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
) -> ApplicationOut:
    application = Application(
        **payload.model_dump(),
        assigned_officer_id=officer.id,
        created_by_officer_id=officer.id,
    )
    db.add(application)
    await db.flush()
    db.add(
        ApplicationHistory(
            application_id=application.id,
            previous_status=None,
            new_status=ApplicationStatus.SUBMITTED,
            action_taken_by=officer.id,
            officer_remarks="Application intake recorded.",
        )
    )
    await db.commit()
    return _with_flag(await _get_application(application.id, db))


@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Officer = Depends(get_current_officer),
) -> ApplicationOut:
    return _with_flag(await _get_application(application_id, db))


@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    _: Officer = Depends(get_current_officer),
) -> ApplicationOut:
    application = await _get_application(application_id, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, key, value)
    await db.commit()
    return _with_flag(await _get_application(application_id, db))


@router.post("/{application_id}/documents")
async def upload_documents(
    application_id: uuid.UUID,
    sale_deed: UploadFile | None = File(default=None),
    porcha: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
) -> ApplicationOut:
    application = await _get_application(application_id, db)
    uploads = (
        (sale_deed, DocumentType.SALE_DEED),
        (porcha, DocumentType.PORCHA),
    )
    for upload, document_type in uploads:
        if upload is None:
            continue
        data = await upload.read()
        filename = upload.filename or f"{document_type.value.lower()}.bin"
        content_type = upload.content_type or "application/octet-stream"
        blob_key = make_blob_key(application.id, document_type.value, filename)
        put_bytes(blob_key, data, content_type)
        document = Document(
            application_id=application.id,
            document_type=document_type,
            blob_key=blob_key,
            original_filename=filename,
            content_type=content_type,
            size_bytes=len(data),
            uploaded_by_officer_id=officer.id,
        )
        db.add(document)
        await db.flush()
        await run_ocr(db, application, document)

    await db.commit()
    return _with_flag(await _get_application(application_id, db))


@router.post("/{application_id}/documents/{document_id}/ocr", response_model=ApplicationOut)
async def rerun_document_ocr(
    application_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Officer = Depends(get_current_officer),
) -> ApplicationOut:
    application = await _get_application(application_id, db)
    document = next((item for item in application.documents if item.id == document_id), None)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await run_ocr(db, application, document)
    await db.commit()
    return _with_flag(await _get_application(application_id, db))


@router.post("/{application_id}/transition", response_model=ApplicationOut)
async def transition(
    application_id: uuid.UUID,
    payload: TransitionRequest,
    db: AsyncSession = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
) -> ApplicationOut:
    application = await _get_application(application_id, db)
    assert_transition(application.status, payload.new_status)

    flags: dict | list | None = None
    remarks = payload.officer_remarks

    if payload.new_status == ApplicationStatus.READY_FOR_DECISION:
        flags = await run_chain_check(db, application)
    if payload.new_status == ApplicationStatus.RETURNED:
        missing = [remarks] if remarks else ["supporting documents"]
        drafted = await run_notice_draft(db, application, missing, payload.language)
        remarks = drafted
        flags = {"notice": drafted, "language": payload.language}

    db.add(
        ApplicationHistory(
            application_id=application.id,
            previous_status=application.status,
            new_status=payload.new_status,
            action_taken_by=officer.id,
            ai_flags_triggered=flags,
            officer_remarks=remarks,
        )
    )
    application.status = payload.new_status
    await db.commit()
    return _with_flag(await _get_application(application_id, db))
