import unittest
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as N

from app.models import ApplicationStatus, DocumentType, OfficerRole, PipelineName, PipelineStatus
from app.routers.applications import _with_flag

NOW = datetime(2026, 3, 1, tzinfo=timezone.utc)


def _application():
    officer = N(id=uuid.uuid4(), full_name="Rina Ghosh", role=OfficerRole.REVENUE_INSPECTOR)
    doc = N(
        id=uuid.uuid4(),
        document_type=DocumentType.SALE_DEED,
        blob_key="k",
        original_filename="dalil.pdf",
        content_type="application/pdf",
        size_bytes=10,
        uploaded_by_officer_id=officer.id,
        created_at=NOW,
    )
    history = [
        N(
            id=uuid.uuid4(),
            previous_status=None,
            new_status=ApplicationStatus.SUBMITTED,
            action_taken_by=officer.id,
            ai_flags_triggered=None,
            officer_remarks="Application intake recorded.",
            created_at=NOW,
            officer=officer,
        ),
        N(
            id=uuid.uuid4(),
            previous_status=ApplicationStatus.SUBMITTED,
            new_status=ApplicationStatus.SUBMITTED,
            action_taken_by=officer.id,
            ai_flags_triggered={"kind": "FIELD_UPDATE", "changes": {"transferor_name": {"from": None, "to": "Bimol Das"}}},
            officer_remarks=None,
            created_at=NOW + timedelta(minutes=1),
            officer=officer,
        ),
    ]
    runs = [
        N(
            id=uuid.uuid4(),
            application_id=None,
            document_id=doc.id,
            pipeline=PipelineName.OCR,
            status=PipelineStatus.SUCCEEDED,
            input_payload={},
            output_payload={"engine": "pdf-text", "raw_text": "x", "extracted": {}, "applied_fields": ["mouza"]},
            created_at=NOW,
        ),
        N(
            id=uuid.uuid4(),
            application_id=None,
            document_id=None,
            pipeline=PipelineName.CHAIN_CHECK,
            status=PipelineStatus.SUCCEEDED,
            input_payload={"transferor_name": "Bimol Das", "recorded_owner_name": "Bimal Das"},
            output_payload={
                "flagged": False,
                "severity": "ok",
                "message": "Spelling variant.",
                "summary": "Spelling variant.",
                "verdict": "LIKELY_SAME_PERSON",
                "engine": "llm",
                "model": "gpt-5.5",
            },
            created_at=NOW + timedelta(minutes=2),
        ),
    ]
    return N(
        id=uuid.uuid4(),
        applicant_name="Aparna Das",
        mouza="Shyamnagar",
        jl_number=42,
        dag_number=118,
        khatian_number=7,
        transferor_name="Bimol Das",
        recorded_owner_name="Bimal Das",
        khajna_status="Paid",
        status=ApplicationStatus.SUBMITTED,
        assigned_officer_id=officer.id,
        created_by_officer_id=officer.id,
        created_at=NOW,
        updated_at=NOW,
        history=history,
        documents=[doc],
        ai_runs=runs,
    )


class SerializeTests(unittest.TestCase):
    def test_detail_payload(self) -> None:
        out = _with_flag(_application())
        self.assertEqual([h.actor_name for h in out.history], ["Rina Ghosh", "Rina Ghosh"])
        self.assertEqual(out.history[0].actor_role, OfficerRole.REVENUE_INSPECTOR)
        self.assertEqual(len(out.ai_runs), 2)
        self.assertEqual(out.ai_runs[0].summary, "OCR read dalil.pdf; filled mouza")
        self.assertEqual(out.ai_runs[1].engine, "llm")
        self.assertEqual(out.ai_runs[1].detail["verdict"], "LIKELY_SAME_PERSON")
        # The stored AI verdict is current, so the rule-based exact match does not flag the file.
        self.assertFalse(out.mismatch_flag["flagged"])
        self.assertEqual(out.mismatch_flag["engine"], "llm")
        out.model_dump_json()

    def test_list_payload_omits_ai_runs(self) -> None:
        out = _with_flag(_application(), include_ocr=False)
        self.assertEqual(out.ai_runs, [])
        self.assertEqual(out.ocr_results, [])


if __name__ == "__main__":
    unittest.main()
