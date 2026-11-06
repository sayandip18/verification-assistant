import asyncio

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.ai import extract_metadata
from app.llm import compose_notice
from app.deps import get_current_officer
from app.models import DocumentType, Officer, PipelineStatus
from app.ocr import OcrError, ocr_bytes
from app.schemas import ExtractedMetadata, ExtractRequest, NoticeRequest, OcrScanOut

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/extract", response_model=ExtractedMetadata)
async def extract(
    payload: ExtractRequest, _: Officer = Depends(get_current_officer)
) -> ExtractedMetadata:
    return extract_metadata(
        payload.raw_text,
        payload.document_type.value if payload.document_type else None,
    )


@router.post("/ocr", response_model=OcrScanOut)
async def ocr_scan(
    file: UploadFile = File(...),
    document_type: DocumentType | None = Form(default=None),
    _: Officer = Depends(get_current_officer),
) -> OcrScanOut:
    data = await file.read()
    filename = file.filename or "scan.bin"
    content_type = file.content_type or "application/octet-stream"
    try:
        result = await asyncio.to_thread(ocr_bytes, data, content_type, filename)
        extracted = extract_metadata(
            result.text, document_type.value if document_type else None
        )
        return OcrScanOut(
            status=PipelineStatus.SUCCEEDED,
            engine=result.engine,
            raw_text=result.text,
            extracted=extracted,
            warning=result.warning,
            page_count=result.page_count,
        )
    except OcrError as exc:
        return OcrScanOut(
            status=PipelineStatus.FAILED,
            raw_text="",
            extracted=ExtractedMetadata(),
            error=exc.message,
        )


@router.post("/notice")
async def notice(payload: NoticeRequest, _: Officer = Depends(get_current_officer)) -> dict:
    result = await compose_notice(
        applicant=payload.applicant_name,
        mouza=payload.mouza,
        dag=None,
        khatian=None,
        officer_notes="\n".join(payload.missing_items),
        language=payload.language,
        chain=None,
    )
    return {"draft": result["notice"], "engine": result["engine"], "warning": result["warning"]}
