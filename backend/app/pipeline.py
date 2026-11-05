"""OCR / AI agent pipeline. Each call writes an `ai_runs` row."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import chain_mismatch, draft_notice, extract_metadata, merge_extracted
from app.blob import get_bytes
from app.models import AiRun, Application, Document, PipelineName, PipelineStatus
from app.ocr import OcrError, ocr_bytes


async def run_ocr(db: AsyncSession, application: Application, document: Document) -> AiRun:
    data = get_bytes(document.blob_key)
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


async def run_chain_check(db: AsyncSession, application: Application) -> dict:
    result = chain_mismatch(application.transferor_name, application.recorded_owner_name)
    db.add(
        AiRun(
            application_id=application.id,
            pipeline=PipelineName.CHAIN_CHECK,
            status=PipelineStatus.SUCCEEDED,
            input_payload={
                "transferor_name": application.transferor_name,
                "recorded_owner_name": application.recorded_owner_name,
            },
            output_payload=result,
        )
    )
    return result


async def run_notice_draft(
    db: AsyncSession, application: Application, missing_items: list[str], language: str
) -> str:
    notice = draft_notice(application.applicant_name, application.mouza, missing_items, language)
    db.add(
        AiRun(
            application_id=application.id,
            pipeline=PipelineName.NOTICE,
            status=PipelineStatus.SUCCEEDED,
            input_payload={"missing_items": missing_items, "language": language},
            output_payload={"notice": notice},
        )
    )
    return notice
