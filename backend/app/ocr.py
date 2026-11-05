"""Document OCR: text-layer PDFs, Tesseract for scans/images, UTF-8 for plain text."""

from __future__ import annotations

import io
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/tif",
    "image/webp",
    "image/bmp",
    "image/gif",
}
PDF_TYPES = {"application/pdf"}
TEXT_TYPES = {"text/plain", "text/csv"}


class OcrError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class OcrEngineResult:
    text: str
    engine: str
    page_count: int = 1
    warning: str | None = None


def tesseract_cmd() -> str | None:
    if settings.tesseract_cmd:
        return settings.tesseract_cmd
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ):
        if Path(candidate).exists():
            return candidate
    return None


def ocr_bytes(data: bytes, content_type: str, filename: str) -> OcrEngineResult:
    if len(data) > settings.ocr_max_bytes:
        raise OcrError(f"File is larger than {settings.ocr_max_bytes} bytes")

    kind = _kind(content_type, filename)
    if kind == "text":
        return OcrEngineResult(text=_decode_text(data), engine="plaintext", page_count=1)
    if kind == "pdf":
        return _ocr_pdf(data)
    if kind == "image":
        return _ocr_image(data)
    raise OcrError(f"Unsupported file type for OCR: {content_type or filename}")


def _kind(content_type: str, filename: str) -> str:
    lowered = (content_type or "").split(";")[0].strip().lower()
    suffix = Path(filename or "").suffix.lower()
    if lowered in TEXT_TYPES or suffix in {".txt", ".csv"}:
        return "text"
    if lowered in PDF_TYPES or suffix == ".pdf":
        return "pdf"
    if lowered in IMAGE_TYPES or suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp", ".gif"}:
        return "image"
    if lowered in {"application/octet-stream", ""} and suffix:
        return _kind("application/pdf" if suffix == ".pdf" else "", filename)
    return "unknown"


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return data.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace").strip()


def _ocr_pdf(data: bytes) -> OcrEngineResult:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    images = None
    page_count = 0
    truncated = None
    try:
        page_count = len(pdf)
        limit = min(page_count, settings.ocr_max_pages)
        text_parts: list[str] = []
        for index in range(limit):
            page = pdf[index]
            textpage = page.get_textpage()
            extracted = (textpage.get_text_range() or textpage.get_text_bounded() or "").strip()
            textpage.close()
            page.close()
            if extracted:
                text_parts.append(extracted)

        joined = "\n\n".join(text_parts).strip()
        truncated = None if page_count <= limit else f"Only the first {limit} pages were read"
        if len(joined) >= settings.ocr_min_text_chars:
            return OcrEngineResult(text=joined, engine="pdf-text", page_count=page_count, warning=truncated)
        images = _pdf_pages_as_images(pdf, limit)
    finally:
        pdf.close()

    ocr_text = _tesseract_images(images or [])
    warning = "PDF had little embedded text; pages were rasterized for Tesseract"
    if truncated:
        warning += f". {truncated}"
    return OcrEngineResult(text=ocr_text, engine="tesseract", page_count=page_count, warning=warning)


def _pdf_pages_as_images(pdf, limit: int):
    from PIL import Image

    images = []
    scale = settings.ocr_pdf_scale
    for index in range(limit):
        page = pdf[index]
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil()
        bitmap.close()
        page.close()
        images.append(pil.convert("RGB") if isinstance(pil, Image.Image) else pil)
    return images


def _ocr_image(data: bytes) -> OcrEngineResult:
    from PIL import Image

    image = Image.open(io.BytesIO(data))
    if image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    text = _tesseract_images([image])
    return OcrEngineResult(text=text, engine="tesseract", page_count=1)


def _tesseract_images(images: list) -> str:
    import pytesseract

    cmd = tesseract_cmd()
    if not cmd:
        raise OcrError(
            "Tesseract is not installed. Install the UB-Mannheim Tesseract build "
            "(with English and Bengali) or set TESSERACT_CMD."
        )
    pytesseract.pytesseract.tesseract_cmd = cmd
    langs = _usable_langs()
    parts: list[str] = []
    for image in images:
        parts.append(pytesseract.image_to_string(image, lang=langs, config="--psm 6"))
    return "\n\n".join(part.strip() for part in parts if part.strip()).strip()


def _usable_langs() -> str:
    import pytesseract

    requested = [part.strip() for part in settings.ocr_langs.split("+") if part.strip()]
    try:
        available = set(pytesseract.get_languages(config=""))
    except Exception:
        return "+".join(requested) or "eng"
    usable = [lang for lang in requested if lang in available]
    if usable:
        return "+".join(usable)
    if "eng" in available:
        return "eng"
    return "+".join(requested) or "eng"
