"""R-120: the seven fields are stored, and the source text survives the write.

R-120, verbatim from pm/03-requirements.md:

    When an advertisement is ingested, the system shall extract employer, role
    title, seniority, location, work arrangement, required skills and preferred
    skills, and shall retain the full source text unmodified.

Every assertion here reads the record back off disk rather than inspecting the
object that was written, because the record on disk is what ships and what every
acceptance command ranges over.

Run: python3 tests/extract/test_seven_fields.py
"""

import datetime
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from support import COMPLETE_POSTING, SPARSE_POSTING, TemporaryStore  # noqa: E402

from extract import fields as fields_module  # noqa: E402
from intake import record as intake_record  # noqa: E402

STAMP = "2026-09-10T01:00:00Z"

SEVEN = (
    "employer",
    "role_title",
    "seniority",
    "location",
    "work_arrangement",
    "required_skills",
    "preferred_skills",
)


class SevenFields(TemporaryStore):
    def run_extraction(self, posting, **kwargs):
        identifier = self.ingest(posting, **kwargs)
        extraction = fields_module.extract(posting)
        self.store.apply(identifier, extraction.as_record_fields(), STAMP)
        return self.store.get(identifier)

    def test_all_seven_fields_are_present_on_the_stored_record(self):
        stored = self.run_extraction(COMPLETE_POSTING)
        present = [f for f in SEVEN if f in stored]
        self.assertEqual(
            len(present), 7, str(len(present)) + " of 7 fields present: " + str(present)
        )

    def test_the_two_determined_flags_are_present_and_boolean(self):
        stored = self.run_extraction(COMPLETE_POSTING)
        for flag in ("required_skills_determined", "preferred_skills_determined"):
            self.assertIn(flag, stored)
            self.assertIsInstance(stored[flag], bool)

    def test_all_seven_are_determined_on_a_posting_that_states_all_seven(self):
        stored = self.run_extraction(COMPLETE_POSTING)
        undetermined = [
            f
            for f in fields_module.SCALAR_FIELDS
            if stored.get(f) == fields_module.UNKNOWN
        ]
        self.assertEqual(undetermined, [], "undetermined scalars: " + str(undetermined))
        self.assertTrue(stored["required_skills_determined"])
        self.assertTrue(stored["preferred_skills_determined"])
        self.assertEqual(stored["extraction_status"], "complete")

    def test_the_seven_fields_are_still_present_when_none_can_be_determined(self):
        stored = self.run_extraction(SPARSE_POSTING)
        present = [f for f in SEVEN if f in stored]
        self.assertEqual(len(present), 7, str(len(present)) + " of 7 fields present")
        for field in fields_module.SCALAR_FIELDS:
            self.assertEqual(stored[field], fields_module.UNKNOWN)
        self.assertEqual(stored["required_skills"], [])
        self.assertEqual(stored["preferred_skills"], [])

    def test_source_text_is_byte_identical_across_extraction(self):
        identifier = self.ingest(COMPLETE_POSTING)
        before = self.store.get(identifier)
        extraction = fields_module.extract(COMPLETE_POSTING)
        self.store.apply(identifier, extraction.as_record_fields(), STAMP)
        after = self.store.get(identifier)
        self.assertEqual(after["source_text"], before["source_text"])
        self.assertEqual(
            after["source_text"].encode("utf-8"), COMPLETE_POSTING.encode("utf-8")
        )

    def test_source_text_still_hashes_to_the_digest_taken_at_ingest(self):
        stored = self.run_extraction(COMPLETE_POSTING)
        self.assertEqual(
            intake_record.digest(stored["source_text"]), stored["source_text_digest"]
        )

    def test_non_ascii_and_whitespace_survive_the_write(self):
        posting = (
            "Company: Acme Systems\nTitle: Data Engineer\n"
            "Location: Zurich\n\nWe are remote.\n\n"
            "What You Bring\n\n - Python and SQL\n"
        )
        stored = self.run_extraction(posting)
        self.assertEqual(stored["source_text"], posting)
        self.assertIn(" ", stored["source_text"])
        self.assertEqual(
            intake_record.digest(stored["source_text"]), stored["source_text_digest"]
        )

    def test_the_write_is_refused_if_the_incoming_digest_does_not_match(self):
        identifier = self.ingest(COMPLETE_POSTING)
        path = self.store.record_path(identifier)
        with open(path, "r", encoding="utf-8") as handle:
            tampered = json.load(handle)
        tampered["source_text"] = tampered["source_text"] + " and one more word"
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(tampered, handle, indent=2, ensure_ascii=False, sort_keys=True)
        extraction = fields_module.extract(COMPLETE_POSTING)
        with self.assertRaises(Exception) as caught:
            self.store.apply(identifier, extraction.as_record_fields(), STAMP)
        self.assertIn("digest", str(caught.exception))

    def test_the_store_refuses_to_write_anything_but_extraction_keys(self):
        identifier = self.ingest(COMPLETE_POSTING)
        with self.assertRaises(Exception) as caught:
            self.store.apply(identifier, {"source_text": "rewritten"}, STAMP)
        self.assertIn("non extraction keys", str(caught.exception))

    def test_extraction_records_that_it_happened(self):
        """The data contract names no field meaning 'extraction has run'.

        E-03 in pm/03-data-contract.md carries model_id, which note 10 of that
        file says is absent before extraction. That is the nearest thing to a
        marker and it is optional, so this build records extracted_at as well.
        Both are asserted here so the gap is visible in the suite rather than
        only in the task return.
        """
        stored = self.run_extraction(COMPLETE_POSTING)
        self.assertTrue(stored.get("model_id"))
        self.assertEqual(stored.get("extracted_at"), STAMP)
        datetime.datetime.strptime(stored["extracted_at"], "%Y-%m-%dT%H:%M:%SZ")

    def test_a_record_that_has_not_been_extracted_carries_no_producer(self):
        identifier = self.ingest(COMPLETE_POSTING)
        stored = self.store.get(identifier)
        self.assertNotIn("model_id", stored)
        self.assertNotIn("extracted_at", stored)


if __name__ == "__main__":
    unittest.main(verbosity=2)
