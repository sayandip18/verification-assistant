import asyncio

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.ai import draft_notice, extract_metadata
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
async def notice(payload: NoticeRequest, _: Officer = Depends(get_current_officer)) -> dict[str, str]:
    return {
        "draft": draft_notice(
            payload.applicant_name, payload.mouza, payload.missing_items, payload.language
        )
    }
