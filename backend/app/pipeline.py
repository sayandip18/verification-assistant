"""OCR / AI agent pipeline. Each call writes an `ai_runs` row."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import extract_metadata, merge_extracted
from app.llm import assess_chain, compose_notice
from app.blob import get_bytes
from app.models import AiRun, Application, Document, PipelineName, PipelineStatus
from app.ocr import OcrError, ocr_bytes


async def run_ocr(db: AsyncSession, application: Application, document: Document) -> AiRun:
    data = await get_bytes(document.blob_key)
    try:
        result = await asyncio.to_thread(ocr_bytes, data, document.content_type, document.original_filename)
        extracted = extract_metadata(result.text, document.document_type.value)
        applied = merge_extracted(application, extracted, document.document_type)
        run = AiRun(
            application_id=application.id,
            document_id=document.id,
            pipeline=PipelineName.OCR,
            status=PipelineStatus.SUCCEEDED,
            input_payload={
                "blob_key": document.blob_key,
                "content_type": document.content_type,
                "filename": document.original_filename,
                "engine": result.engine,
                "page_count": result.page_count,
            },
            output_payload={
                "engine": result.engine,
                "raw_text": result.text,
                "extracted": extracted.model_dump(),
                "applied_fields": applied,
                "warning": result.warning,
            },
        )
    except OcrError as exc:
        run = AiRun(
            application_id=application.id,
            document_id=document.id,
            pipeline=PipelineName.OCR,
            status=PipelineStatus.FAILED,
            input_payload={
                "blob_key": document.blob_key,
                "content_type": document.content_type,
                "filename": document.original_filename,
            },
            output_payload={"error": exc.message, "raw_text": "", "extracted": {}},
        )
    except Exception as exc:
        run = AiRun(
            application_id=application.id,
            document_id=document.id,
            pipeline=PipelineName.OCR,
            status=PipelineStatus.FAILED,
            input_payload={
                "blob_key": document.blob_key,
                "content_type": document.content_type,
                "filename": document.original_filename,
            },
            output_payload={"error": str(exc), "raw_text": "", "extracted": {}},
        )
    db.add(run)
    return run


def _latest_ocr_excerpts(application: Application) -> dict[str, str]:
    latest: dict[str, AiRun] = {}
    docs = {document.id: document for document in application.documents}
    for run in application.ai_runs:
        if run.pipeline != PipelineName.OCR or run.status != PipelineStatus.SUCCEEDED:
            continue
        document = docs.get(run.document_id)
        kind = document.document_type.value if document else "OTHER"
        if kind not in latest or run.created_at >= latest[kind].created_at:
            latest[kind] = run
    return {kind: (run.output_payload or {}).get("raw_text") or "" for kind, run in latest.items()}


async def run_chain_check(db: AsyncSession, application: Application) -> dict:
    excerpts = _latest_ocr_excerpts(application)
    result = await assess_chain(
        transferor=application.transferor_name,
        owner=application.recorded_owner_name,
        applicant=application.applicant_name,
        khajna=application.khajna_status,
        mouza=application.mouza,
        dag=application.dag_number,
        khatian=application.khatian_number,
        excerpts=excerpts,
    )
    db.add(
        AiRun(
            application_id=application.id,
            pipeline=PipelineName.CHAIN_CHECK,
            status=PipelineStatus.SUCCEEDED,
            input_payload={
                "transferor_name": application.transferor_name,
                "recorded_owner_name": application.recorded_owner_name,
                "khajna_status": application.khajna_status,
                "documents": sorted(excerpts),
            },
            output_payload=result,
        )
    )
    return result


async def run_notice_draft(
    db: AsyncSession, application: Application, officer_notes: str, language: str, chain: dict | None
) -> dict:
    result = await compose_notice(
        applicant=application.applicant_name,
        mouza=application.mouza,
        dag=application.dag_number,
        khatian=application.khatian_number,
        officer_notes=officer_notes,
        language=language,
        chain=chain,
    )
    run = AiRun(
        application_id=application.id,
        pipeline=PipelineName.NOTICE,
        status=PipelineStatus.SUCCEEDED,
        input_payload={"officer_notes": officer_notes, "language": language},
        output_payload=result,
    )
    db.add(run)
    await db.flush()
    return {**result, "ai_run_id": str(run.id), "language": language}
