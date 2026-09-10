"""R-117: every evidence record carries a source and a date.

Every test here builds its own store under a temporary directory and deletes it. None of
them reads or writes ./store, because a test that mutates the shipped store is a defect
and would also make the acceptance command unreproducible.

Run: python3 tests/evidence/test_source_and_date.py
"""

import glob
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
)

from evidence import record as record_module  # noqa: E402
from evidence.record import RecordInvalid  # noqa: E402
from evidence.store import EvidenceStore, WriteRejected  # noqa: E402


def sound_record(**overrides):
    base = {
        "id": "ev_test_role",
        "claim_text": "Test Role, Test Org, Jan 2020.",
        "kind": "role",
        "source": "self-written 2022 CV",
        "source_kind": "document",
        "date": "2020-01",
    }
    base.update(overrides)
    return base


class TemporaryStore(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="career_os_evidence_test_")
        self.store = EvidenceStore(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def stored_files(self):
        return glob.glob(os.path.join(self.root, "evidence", "*.json"))


class TestRecordConformsToE01(TemporaryStore):
    def test_a_sound_record_stores_and_reads_back_with_exactly_the_e01_fields(self):
        status, identifier = self.store.write(sound_record())
        self.assertEqual(status, "stored")
        self.assertEqual(identifier, "ev_test_role")

        # Assert on what shipped, read off disk, not on the object handed to write().
        with open(self.stored_files()[0], "r", encoding="utf-8") as handle:
            shipped = json.load(handle)
        self.assertEqual(sorted(shipped), sorted(record_module.FIELDS))
        self.assertEqual(shipped["source"], "self-written 2022 CV")
        self.assertEqual(shipped["date"], "2020-01")

    def test_an_unknown_field_is_refused_rather_than_silently_stored(self):
        with self.assertRaises(WriteRejected) as caught:
            self.store.write(sound_record(confidence="high"))
        self.assertIn("confidence", caught.exception.fields)
        self.assertEqual(self.stored_files(), [])


class TestSourceIsMandatory(TemporaryStore):
    def test_a_write_with_no_source_is_rejected_and_names_the_field(self):
        candidate = sound_record()
        del candidate["source"]
        with self.assertRaises(WriteRejected) as caught:
            self.store.write(candidate)
        self.assertEqual(caught.exception.fields, ("source",))

    def test_an_empty_source_is_an_absent_source(self):
        for empty in ("", "   ", None):
            with self.subTest(empty=empty):
                with self.assertRaises(WriteRejected) as caught:
                    self.store.write(sound_record(id="ev_empty_source", source=empty))
                self.assertIn("source", caught.exception.fields)

    def test_a_rejected_write_issues_no_identifier_and_leaves_the_count_unchanged(self):
        self.store.write(sound_record(id="ev_first"))
        before = self.store.count()
        status, identifier, reasons = self.store.try_write(
            sound_record(id="ev_second", source="")
        )
        self.assertEqual(status, "rejected")
        self.assertIsNone(identifier)
        self.assertIn("source", reasons)
        self.assertEqual(self.store.count(), before)
        self.assertIsNone(self.store.get("ev_second"))


class TestDateIsMandatory(TemporaryStore):
    def test_a_write_with_no_date_is_rejected_and_names_the_field(self):
        candidate = sound_record()
        del candidate["date"]
        with self.assertRaises(WriteRejected) as caught:
            self.store.write(candidate)
        self.assertEqual(caught.exception.fields, ("date",))

    def test_an_empty_date_is_an_absent_date(self):
        with self.assertRaises(WriteRejected) as caught:
            self.store.write(sound_record(id="ev_empty_date", date="   "))
        self.assertIn("date", caught.exception.fields)

    def test_both_absences_are_reported_together_not_one_at_a_time(self):
        candidate = sound_record()
        del candidate["source"]
        del candidate["date"]
        with self.assertRaises(WriteRejected) as caught:
            self.store.write(candidate)
        self.assertEqual(set(caught.exception.fields), {"source", "date"})

    def test_build_refuses_to_construct_a_record_without_a_source_or_date(self):
        with self.assertRaises(RecordInvalid):
            record_module.build(
                id="ev_no_source",
                claim_text="A claim.",
                kind="role",
                source=None,
                source_kind="document",
                date="2020",
            )


class TestTheR117PredicateFiresOnADeficientStore(TemporaryStore):
    """The gate is not trusted until it has been seen red on this store shape.

    This runs the acceptance predicate from R-117 in pm/03-requirements.md over a
    temporary store, first with a compliant record and then with a deficient one placed
    on disk behind the store's back, which is how a deficient record actually arrives:
    by a hand edit, not through the write path.
    """

    def r117(self):
        records = []
        for path in sorted(self.stored_files()):
            with open(path, "r", encoding="utf-8") as handle:
                records.append(json.load(handle))
        ok = [
            r
            for r in records
            if (r.get("source") or "").strip() and (r.get("date") or "").strip()
        ]
        passed = bool(records) and len(ok) == len(records)
        return passed, len(ok), len(records)

    def test_green_on_a_compliant_store_and_red_when_a_source_is_removed(self):
        self.store.write(sound_record(id="ev_one"))
        self.store.write(sound_record(id="ev_two"))
        self.assertEqual(self.r117(), (True, 2, 2))

        path = self.store.record_path("ev_two")
        with open(path, "r", encoding="utf-8") as handle:
            poisoned = json.load(handle)
        del poisoned["source"]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(poisoned, handle, indent=2)

        passed, ok, total = self.r117()
        self.assertFalse(passed)
        self.assertEqual((ok, total), (1, 2))

    def test_the_predicate_is_vacuous_not_passing_on_an_empty_store(self):
        passed, ok, total = self.r117()
        self.assertEqual(total, 0)
        self.assertFalse(passed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
