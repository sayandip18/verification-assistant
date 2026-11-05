import re

from app.models import DocumentType
from app.schemas import ExtractedMetadata

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
LABEL = (
    r"mouza|মৌজা|j\.?l\.?\s*(?:no\.?|number)?|জে\.?\s*এল|"
    r"dag|plot|দাগ|khatian|খতিয়ান|খতিয়ান|"
    r"transferor|seller|vendor|executant|বিক্রেতা|হস্তান্তরকারী|"
    r"recorded owner|porcha owner|raiyat|খতিয়ানভুক্ত মালিক|রেকর্ডীয় মালিক|owner|মালিক|"
    r"applicant|purchaser|vendee|buyer|ক্রেতা|আবেদনকারী|"
    r"khajna|খাজনা|land tax"
)
VALUE = r"(.+?)"
BOUNDARY = rf"(?=\s+(?:{LABEL})[:\s#]|$)"


def extract_metadata(raw_text: str, document_type: str | DocumentType | None = None) -> ExtractedMetadata:
    if isinstance(document_type, DocumentType):
        document_type = document_type.value
    text = re.sub(r"\s+", " ", raw_text or "").translate(BN_DIGITS).strip()

    def find(pattern: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        value = match.group(1).strip(" .,-")
        return value or None

    def find_int(pattern: str) -> int | None:
        value = find(pattern)
        if value is None:
            return None
        digits = re.sub(r"\D", "", value)
        return int(digits) if digits else None

    applicant = find(rf"(?:applicant|purchaser|vendee|buyer|ক্রেতা|আবেদনকারী)[:\s]+{VALUE}{BOUNDARY}")
    transferor = find(
        rf"(?:transferor|seller|vendor|executant|বিক্রেতা|হস্তান্তরকারী)[:\s]+{VALUE}{BOUNDARY}"
    )
    recorded_owner = find(
        rf"(?:recorded owner|porcha owner|raiyat|খতিয়ানভুক্ত মালিক|রেকর্ডীয় মালিক)[:\s]+{VALUE}{BOUNDARY}"
    )
    generic_owner = find(rf"(?:owner|মালিক)[:\s]+{VALUE}{BOUNDARY}")

    if document_type == DocumentType.PORCHA.value:
        recorded_owner = recorded_owner or generic_owner or applicant
    elif document_type == DocumentType.SALE_DEED.value:
        transferor = transferor or generic_owner
    else:
        recorded_owner = recorded_owner or generic_owner

    return ExtractedMetadata(
        applicant_name=applicant,
        mouza=find(rf"(?:mouza|মৌজা)[:\s]+{VALUE}{BOUNDARY}"),
        jl_number=find_int(r"(?:j\.?l\.?\s*(?:no\.?|number)?|জে\.?\s*এল)[:\s]+(\d+)"),
        dag_number=find_int(r"(?:dag|plot|দাগ)[:\s#]*(\d+)"),
        khatian_number=find_int(r"(?:khatian|খতিয়ান|খতিয়ান)[:\s#]*(\d+)"),
        transferor_name=transferor,
        recorded_owner_name=recorded_owner,
        khajna_status=find(rf"(?:khajna|খাজনা|land tax)[:\s]+{VALUE}{BOUNDARY}"),
    )


def merge_extracted(application, extracted: ExtractedMetadata, document_type: DocumentType) -> list[str]:
    """Fill blank application fields from OCR. Never overwrite officer-entered values."""
    applied: list[str] = []
    data = extracted.model_dump()

    def empty(value) -> bool:
        return value is None or value == "" or value == 0

    plot_fields = ("mouza", "jl_number", "dag_number", "khatian_number", "khajna_status")
    for field in plot_fields:
        incoming = data.get(field)
        if incoming in (None, ""):
            continue
        if empty(getattr(application, field)):
            setattr(application, field, incoming)
            applied.append(field)

    if document_type == DocumentType.SALE_DEED:
        if data.get("transferor_name") and empty(application.transferor_name):
            application.transferor_name = data["transferor_name"]
            applied.append("transferor_name")
        if data.get("applicant_name") and empty(application.applicant_name):
            application.applicant_name = data["applicant_name"]
            applied.append("applicant_name")
    elif document_type == DocumentType.PORCHA:
        owner = data.get("recorded_owner_name") or data.get("applicant_name")
        if owner and empty(application.recorded_owner_name):
            application.recorded_owner_name = owner
            applied.append("recorded_owner_name")
    else:
        for field in ("applicant_name", "transferor_name", "recorded_owner_name"):
            incoming = data.get(field)
            if incoming and empty(getattr(application, field)):
                setattr(application, field, incoming)
                applied.append(field)

    return applied


def chain_mismatch(transferor_name: str | None, recorded_owner_name: str | None) -> dict:
    if not transferor_name or not recorded_owner_name:
        return {
            "flagged": False,
            "severity": "info",
            "message": "Transferor or recorded owner is missing. Complete field verification before deciding.",
        }

    if transferor_name.strip().casefold() == recorded_owner_name.strip().casefold():
        return {
            "flagged": False,
            "severity": "ok",
            "message": "Transferor matches the recorded owner on the existing Porcha.",
        }

    return {
        "flagged": True,
        "severity": "high",
        "message": (
            f"Warning: Transferor '{transferor_name}' does not match recorded owner "
            f"'{recorded_owner_name}'. Check for an inheritance link deed."
        ),
    }


def draft_notice(applicant_name: str, mouza: str, missing_items: list[str], language: str) -> str:
    items_en = ", ".join(missing_items) if missing_items else "the required supporting documents"
    if language == "bn":
        items_bn = ", ".join(missing_items) if missing_items else "প্রয়োজনীয় সহায়ক নথি"
        return (
            f"শ্রী/শ্রীমতী {applicant_name}, {mouza} মৌজার দাখিলকৃত নামান্তরণ আবেদন "
            f"নিম্নলিখিত নথি ছাড়া অসম্পূর্ণ: {items_bn}। অনুগ্রহ করে নথি জমা দিয়ে আবেদনটি পুনরায় দাখিল করুন।"
        )
    return (
        f"To {applicant_name}, regarding the mutation application for Mouza {mouza}: "
        f"the file is returned for want of {items_en}. Please resubmit with the missing papers."
    )
