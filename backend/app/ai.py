import re

from app.schemas import ExtractedMetadata


def extract_metadata(raw_text: str) -> ExtractedMetadata:
    """Boilerplate extractor: regex over pasted OCR text.

    Swap this implementation for Tesseract + GPT-4o / a local LLM.
    """
    text = raw_text.replace("\n", " ")

    def find(pattern: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def find_int(pattern: str) -> int | None:
        value = find(pattern)
        if value is None:
            return None
        digits = re.sub(r"\D", "", value)
        return int(digits) if digits else None

    return ExtractedMetadata(
        applicant_name=find(r"applicant[:\s]+([A-Za-z .]+)"),
        mouza=find(r"mouza[:\s]+([A-Za-z .]+)"),
        jl_number=find_int(r"j\.?l\.?\s*(?:no\.?|number)?[:\s]+(\d+)"),
        dag_number=find_int(r"(?:dag|plot)[:\s]+(\d+)"),
        khatian_number=find_int(r"khatian[:\s]+(\d+)"),
        transferor_name=find(r"transferor[:\s]+([A-Za-z .]+)"),
        recorded_owner_name=find(r"(?:recorded owner|porcha owner)[:\s]+([A-Za-z .]+)"),
    )


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
