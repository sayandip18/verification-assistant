import unittest
from datetime import datetime, timezone

from app.attention import attention_for, attention_sort_key
from app.models import ApplicationStatus


class _App:
    def __init__(self, status, transferor=None, owner=None, updated_at=None):
        self.status = status
        self.transferor_name = transferor
        self.recorded_owner_name = owner
        self.updated_at = updated_at or datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.created_at = self.updated_at


class AttentionTests(unittest.TestCase):
    def test_mismatch_ready_outranks_new_intake(self) -> None:
        ready = _App(ApplicationStatus.READY_FOR_DECISION, "Aparna Das", "Bimal Das")
        intake = _App(ApplicationStatus.SUBMITTED, "Aparna Das", "Aparna Das")
        self.assertEqual(attention_for(ready).rank, 1)
        self.assertEqual(attention_for(intake).rank, 7)
        self.assertLess(attention_sort_key(ready), attention_sort_key(intake))

    def test_ready_without_flag_beats_field_mismatch(self) -> None:
        ready = _App(ApplicationStatus.READY_FOR_DECISION, "Aparna Das", "Aparna Das")
        field = _App(ApplicationStatus.FIELD_VERIFICATION, "Aparna Das", "Bimal Das")
        self.assertEqual(attention_for(ready).rank, 2)
        self.assertEqual(attention_for(field).rank, 3)
        self.assertLess(attention_sort_key(ready), attention_sort_key(field))

    def test_older_file_in_same_band_comes_first(self) -> None:
        older = _App(
            ApplicationStatus.SUBMITTED,
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        newer = _App(
            ApplicationStatus.SUBMITTED,
            updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        self.assertLess(attention_sort_key(older), attention_sort_key(newer))

    def test_closed_files_rank_last(self) -> None:
        closed = _App(ApplicationStatus.APPROVED, "A", "A")
        intake = _App(ApplicationStatus.SUBMITTED)
        self.assertTrue(attention_for(closed).closed)
        self.assertGreater(attention_sort_key(closed), attention_sort_key(intake))

    def test_reasons_and_next_actions(self) -> None:
        mismatch_ready = attention_for(
            _App(ApplicationStatus.READY_FOR_DECISION, "Aparna Das", "Bimal Das")
        )
        self.assertEqual(mismatch_ready.reason, "Ownership mismatch · ready to decide")
        self.assertEqual(mismatch_ready.next_action, "Approve, reject, or return")
        returned = attention_for(_App(ApplicationStatus.RETURNED))
        self.assertEqual(returned.reason, "Returned to applicant")
        self.assertEqual(returned.next_action, "Re-open at intake")


if __name__ == "__main__":
    unittest.main()
