import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai import chain_mismatch, draft_notice
from app.config import settings
from app.database import get_db
from app.models import Application, ApplicationHistory, ApplicationStatus
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    QueueSummary,
    TransitionRequest,
)
from app.state_machine import assert_transition

router = APIRouter(prefix="/applications", tags=["applications"])
upload_root = Path(settings.upload_dir)


def _with_flag(application: Application) -> ApplicationOut:
    payload = ApplicationOut.model_validate(application)
    payload.mismatch_flag = chain_mismatch(application.transferor_name, application.recorded_owner_name)
    return payload


async def _get_application(application_id: uuid.UUID, db: AsyncSession) -> Application:
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.history))
        .where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


@router.get("/queue/summary", response_model=QueueSummary)
async def queue_summary(db: AsyncSession = Depends(get_db)) -> QueueSummary:
    result = await db.execute(select(Application))
    applications = result.scalars().all()
    discrepancies = 0
    counts = {status: 0 for status in ApplicationStatus}
    for application in applications:
        counts[application.status] += 1
        flag = chain_mismatch(application.transferor_name, application.recorded_owner_name)
        if flag["flagged"] and application.status not in {
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED,
        }:
            discrepancies += 1
    return QueueSummary(
        submitted=counts[ApplicationStatus.SUBMITTED],
        field_verification=counts[ApplicationStatus.FIELD_VERIFICATION],
        ready_for_decision=counts[ApplicationStatus.READY_FOR_DECISION],
        returned=counts[ApplicationStatus.RETURNED],
        high_priority_discrepancies=discrepancies,
    )


@router.get("", response_model=list[ApplicationOut])
async def list_applications(db: AsyncSession = Depends(get_db)) -> list[ApplicationOut]:
    result = await db.execute(
        select(Application).options(selectinload(Application.history)).order_by(Application.created_at.desc())
    )
    return [_with_flag(item) for item in result.scalars().all()]


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate, db: AsyncSession = Depends(get_db)
) -> ApplicationOut:
    officer_id = uuid.UUID(settings.default_officer_id)
    application = Application(**payload.model_dump(), assigned_officer_id=officer_id)
    db.add(application)
    await db.flush()
    db.add(
        ApplicationHistory(
            application_id=application.id,
            previous_status=None,
            new_status=ApplicationStatus.SUBMITTED,
            action_taken_by=officer_id,
            officer_remarks="Application intake recorded.",
        )
    )
    await db.commit()
    return _with_flag(await _get_application(application.id, db))


@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ApplicationOut:
    return _with_flag(await _get_application(application_id, db))


@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
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
) -> ApplicationOut:
    application = await _get_application(application_id, db)
    folder = upload_root / str(application.id)
    folder.mkdir(parents=True, exist_ok=True)

    if sale_deed is not None:
        dest = folder / f"sale_deed_{sale_deed.filename}"
        with dest.open("wb") as handle:
            shutil.copyfileobj(sale_deed.file, handle)
        application.sale_deed_path = str(dest)
    if porcha is not None:
        dest = folder / f"porcha_{porcha.filename}"
        with dest.open("wb") as handle:
            shutil.copyfileobj(porcha.file, handle)
        application.porcha_path = str(dest)

    await db.commit()
    return _with_flag(await _get_application(application_id, db))


@router.post("/{application_id}/transition", response_model=ApplicationOut)
async def transition(
    application_id: uuid.UUID,
    payload: TransitionRequest,
    db: AsyncSession = Depends(get_db),
) -> ApplicationOut:
    application = await _get_application(application_id, db)
    assert_transition(application.status, payload.new_status)

    officer_id = uuid.UUID(settings.default_officer_id)
    flags: dict | list | None = None
    remarks = payload.officer_remarks

    if payload.new_status == ApplicationStatus.READY_FOR_DECISION:
        flags = chain_mismatch(application.transferor_name, application.recorded_owner_name)
    if payload.new_status == ApplicationStatus.RETURNED:
        missing = [remarks] if remarks else ["supporting documents"]
        drafted = draft_notice(application.applicant_name, application.mouza, missing, payload.language)
        remarks = drafted
        flags = {"notice": drafted, "language": payload.language}

    history = ApplicationHistory(
        application_id=application.id,
        previous_status=application.status,
        new_status=payload.new_status,
        action_taken_by=officer_id,
        ai_flags_triggered=flags,
        officer_remarks=remarks,
    )
    application.status = payload.new_status
    db.add(history)
    await db.commit()
    return _with_flag(await _get_application(application_id, db))
