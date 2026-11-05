from fastapi import APIRouter

from app.ai import draft_notice, extract_metadata
from app.schemas import ExtractedMetadata, ExtractRequest, NoticeRequest

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/extract", response_model=ExtractedMetadata)
async def extract(payload: ExtractRequest) -> ExtractedMetadata:
    return extract_metadata(payload.raw_text)


@router.post("/notice")
async def notice(payload: NoticeRequest) -> dict[str, str]:
    return {
        "draft": draft_notice(
            payload.applicant_name, payload.mouza, payload.missing_items, payload.language
        )
    }
