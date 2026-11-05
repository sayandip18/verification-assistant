import unittest

from app.ai import extract_metadata, merge_extracted
from app.models import DocumentType
from app.ocr import ocr_bytes
from app.schemas import ExtractedMetadata


class ExtractTests(unittest.TestCase):
    def test_english_labels_do_not_swallow_the_next_field(self) -> None:
        extracted = extract_metadata(
            "Applicant: Aparna Das\nMouza: Shyamnagar\nJ.L. No.: 42\nDag: 118\n"
            "Khatian: 7\nTransferor: Aparna Das\nRecorded owner: Bimal Das\nKhajna: Paid up to 2025"
        )
        self.assertEqual(extracted.applicant_name, "Aparna Das")
        self.assertEqual(extracted.mouza, "Shyamnagar")
        self.assertEqual(extracted.jl_number, 42)
        self.assertEqual(extracted.dag_number, 118)
        self.assertEqual(extracted.khatian_number, 7)
        self.assertEqual(extracted.transferor_name, "Aparna Das")
        self.assertEqual(extracted.recorded_owner_name, "Bimal Das")
        self.assertEqual(extracted.khajna_status, "Paid up to 2025")

    def test_sale_deed_uses_seller_and_purchaser(self) -> None:
        extracted = extract_metadata(
            "Seller: Bimal Das Mouza: Shyamnagar Purchaser: Aparna Das Dag: 12",
            DocumentType.SALE_DEED,
        )
        self.assertEqual(extracted.transferor_name, "Bimal Das")
        self.assertEqual(extracted.applicant_name, "Aparna Das")

    def test_porcha_uses_owner_as_recorded_owner(self) -> None:
        extracted = extract_metadata(
            "মৌজা: শ্যামনগর Owner: Bimal Das দাগ: 118 খতিয়ান: 7",
            DocumentType.PORCHA,
        )
        self.assertEqual(extracted.mouza, "শ্যামনগর")
        self.assertEqual(extracted.recorded_owner_name, "Bimal Das")
        self.assertEqual(extracted.dag_number, 118)
        self.assertEqual(extracted.khatian_number, 7)

    def test_bengali_digits(self) -> None:
        extracted = extract_metadata("জে.এল: ৪২ দাগ: ১১৮ খতিয়ান: ৭")
        self.assertEqual(extracted.jl_number, 42)
        self.assertEqual(extracted.dag_number, 118)
        self.assertEqual(extracted.khatian_number, 7)

    def test_merge_does_not_overwrite_officer_values(self) -> None:
        class Application:
            applicant_name = "Existing"
            mouza = ""
            jl_number = 0
            dag_number = 5
            khatian_number = 0
            transferor_name = None
            recorded_owner_name = None
            khajna_status = None

        extracted = ExtractedMetadata(
            applicant_name="Aparna Das",
            mouza="Shyamnagar",
            jl_number=42,
            dag_number=118,
            transferor_name="Aparna Das",
        )
        applied = merge_extracted(Application, extracted, DocumentType.SALE_DEED)
        self.assertEqual(Application.applicant_name, "Existing")
        self.assertEqual(Application.mouza, "Shyamnagar")
        self.assertEqual(Application.jl_number, 42)
        self.assertEqual(Application.dag_number, 5)
        self.assertEqual(Application.transferor_name, "Aparna Das")
        self.assertIn("mouza", applied)
        self.assertNotIn("applicant_name", applied)
        self.assertNotIn("dag_number", applied)


class PlaintextOcrTests(unittest.TestCase):
    def test_plain_text_file(self) -> None:
        result = ocr_bytes(
            "Applicant: Aparna Das\nMouza: Shyamnagar".encode("utf-8"),
            "text/plain",
            "dalil.txt",
        )
        self.assertEqual(result.engine, "plaintext")
        self.assertIn("Aparna Das", result.text)


if __name__ == "__main__":
    unittest.main()
