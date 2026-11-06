import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import mock

from app import llm
from app.attention import attention_for, current_chain
from app.models import ApplicationStatus, PipelineName, PipelineStatus

CHAIN_ARGS = dict(
    transferor="Bimol Kumar Das",
    owner="Bimal Das",
    applicant="Aparna Das",
    khajna="Paid up to 2025",
    mouza="Shyamnagar",
    dag=118,
    khatian=7,
    excerpts={"SALE_DEED": "Seller: Bimol Kumar Das"},
)


def run(coro):
    return asyncio.run(coro)


class ChainCheckTests(unittest.TestCase):
    def test_falls_back_to_rules_without_api_key(self) -> None:
        with mock.patch.object(llm, "llm_enabled", return_value=False):
            result = run(llm.assess_chain(**CHAIN_ARGS))
        self.assertEqual(result["engine"], "rules")
        self.assertEqual(result["verdict"], "MISMATCH")
        self.assertTrue(result["flagged"])
        self.assertIn("not configured", result["warning"])

    def test_llm_variant_name_is_not_flagged(self) -> None:
        reply = {
            "verdict": "LIKELY_SAME_PERSON",
            "confidence": "high",
            "summary": "Bimol Kumar Das is a spelling variant of Bimal Das.",
            "summary_bn": "একই ব্যক্তি।",
            "reasons": ["Bimol/Bimal spelling", "middle name added"],
            "suggested_checks": [],
            "documents_to_request": [],
        }
        with mock.patch.object(llm, "llm_enabled", return_value=True), mock.patch.object(
            llm, "_structured_call", new=mock.AsyncMock(return_value=reply)
        ) as call:
            result = run(llm.assess_chain(**CHAIN_ARGS))
        self.assertEqual(result["engine"], "llm")
        self.assertFalse(result["flagged"])
        self.assertEqual(result["severity"], "ok")
        self.assertEqual(result["message"], reply["summary"])
        prompt = call.await_args.args[1]
        self.assertIn('<document type="SALE_DEED">', prompt)

    def test_possible_link_is_flagged_medium(self) -> None:
        reply = {
            "verdict": "POSSIBLE_LINK",
            "confidence": "medium",
            "summary": "Same surname; likely inheritance.",
            "summary_bn": "",
            "reasons": [],
            "suggested_checks": ["Check succession"],
            "documents_to_request": ["Legal heir certificate"],
        }
        with mock.patch.object(llm, "llm_enabled", return_value=True), mock.patch.object(
            llm, "_structured_call", new=mock.AsyncMock(return_value=reply)
        ):
            result = run(llm.assess_chain(**CHAIN_ARGS))
        self.assertTrue(result["flagged"])
        self.assertEqual(result["severity"], "medium")
        self.assertEqual(result["documents_to_request"], ["Legal heir certificate"])

    def test_api_failure_falls_back_with_warning(self) -> None:
        with mock.patch.object(llm, "llm_enabled", return_value=True), mock.patch.object(
            llm, "_structured_call", new=mock.AsyncMock(side_effect=llm.LlmError("AI service error (529)."))
        ):
            result = run(llm.assess_chain(**CHAIN_ARGS))
        self.assertEqual(result["engine"], "rules")
        self.assertIn("529", result["warning"])


class NoticeTests(unittest.TestCase):
    NOTICE_ARGS = dict(
        applicant="Aparna Das",
        mouza="Shyamnagar",
        dag=118,
        khatian=7,
        officer_notes="Legal heir certificate\nKhajna receipt for 2025",
        language="bn",
        chain=None,
    )

    def test_template_fallback_lists_items(self) -> None:
        with mock.patch.object(llm, "llm_enabled", return_value=False):
            result = run(llm.compose_notice(**self.NOTICE_ARGS))
        self.assertEqual(result["engine"], "rules")
        self.assertIn("Legal heir certificate", result["notice"])
        self.assertIn("Khajna receipt for 2025", result["notice"])

    def test_llm_notice(self) -> None:
        with mock.patch.object(llm, "llm_enabled", return_value=True), mock.patch.object(
            llm, "_structured_call", new=mock.AsyncMock(return_value={"notice": "  নোটিশ  "})
        ) as call:
            result = run(llm.compose_notice(**self.NOTICE_ARGS))
        self.assertEqual(result, {"notice": "নোটিশ", "engine": "llm", "model": llm.settings.openai_model, "warning": None})
        self.assertIn("Language: Bengali", call.await_args.args[1])


def _run(created_at, transferor, owner, output):
    return SimpleNamespace(
        pipeline=PipelineName.CHAIN_CHECK,
        status=PipelineStatus.SUCCEEDED,
        created_at=created_at,
        input_payload={"transferor_name": transferor, "recorded_owner_name": owner},
        output_payload=output,
    )


class CurrentChainTests(unittest.TestCase):
    def _app(self, transferor, owner, runs):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        return SimpleNamespace(
            status=ApplicationStatus.FIELD_VERIFICATION,
            transferor_name=transferor,
            recorded_owner_name=owner,
            ai_runs=runs,
            updated_at=now,
            created_at=now,
        )

    def test_uses_latest_matching_llm_verdict(self) -> None:
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ok = {"flagged": False, "severity": "ok", "message": "Same person", "engine": "llm"}
        application = self._app("Bimol Das", "Bimal Das", [_run(t0, "Bimol Das", "Bimal Das", ok)])
        chain = current_chain(application)
        self.assertEqual(chain["engine"], "llm")
        self.assertFalse(chain["stale"])
        # Rule-based check alone would flag this as a mismatch.
        self.assertEqual(attention_for(application).rank, 5)

    def test_edited_names_make_verdict_stale(self) -> None:
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ok = {"flagged": False, "severity": "ok", "message": "Same person", "engine": "llm"}
        application = self._app(
            "Someone Else",
            "Bimal Das",
            [_run(t0, "Bimol Das", "Bimal Das", ok), _run(t0 - timedelta(days=1), "x", "y", ok)],
        )
        chain = current_chain(application)
        self.assertEqual(chain["engine"], "rules")
        self.assertTrue(chain["stale"])
        self.assertTrue(chain["flagged"])


if __name__ == "__main__":
    unittest.main()
