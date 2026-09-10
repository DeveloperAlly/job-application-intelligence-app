"""Assertions on what actually shipped: the records in the real store.

Every other file in this directory works in a temporary store. This one reads
CAREER_OS_STORE, defaulting to ./store, because a recorded status is a claim and
the only evidence is the record on disk. It opens files read only and writes
nothing, so running it cannot change what it is checking.

When no extracted advertisement is present the result is VACUOUS, not a pass, and
the tests say so rather than reporting green over an empty set.

Run: CAREER_OS_STORE=./store python3 tests/extract/test_shipped_record.py
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))

from extract import fields as fields_module  # noqa: E402
from extract.store import ExtractionStore  # noqa: E402
from intake import record as intake_record  # noqa: E402

STORE = ExtractionStore()
ALL_RECORDS = STORE.all_records() if os.path.isdir(STORE.collection_dir()) else []
EXTRACTED = [r for r in ALL_RECORDS if r.get("extraction_status")]

VACUOUS = (
    "VACUOUS, not a pass: "
    + str(len(EXTRACTED))
    + " of "
    + str(len(ALL_RECORDS))
    + " advertisements in "
    + STORE.collection_dir()
    + " carry a recorded extraction"
)


@unittest.skipIf(not EXTRACTED, VACUOUS)
class ShippedRecords(unittest.TestCase):
    def test_denominator_is_not_zero(self):
        self.assertGreater(len(EXTRACTED), 0, VACUOUS)

    def test_every_extracted_record_carries_all_seven_fields(self):
        missing = [
            (r.get("id"), f)
            for r in EXTRACTED
            for f in fields_module.FIELD_LIST
            if f not in r
        ]
        self.assertEqual(
            missing,
            [],
            str(len(EXTRACTED) * 7 - len(missing))
            + " of "
            + str(len(EXTRACTED) * 7)
            + " field slots present",
        )

    def test_no_scalar_is_empty_rather_than_the_literal_unknown(self):
        empty = [
            (r.get("id"), f)
            for r in EXTRACTED
            for f in fields_module.SCALAR_FIELDS
            if not r.get(f)
        ]
        self.assertEqual(empty, [], "empty scalars: " + str(empty))

    def test_every_skill_term_occurs_verbatim_in_its_own_source_text(self):
        pairs = [
            (r.get("id"), t, r.get("source_text") or "")
            for r in EXTRACTED
            for t in (r.get("required_skills", []) + r.get("preferred_skills", []))
        ]
        offenders = [(i, t) for i, t, text in pairs if t.lower() not in text.lower()]
        self.assertGreater(len(pairs), 0, "VACUOUS: no skill terms shipped")
        self.assertEqual(
            offenders,
            [],
            str(len(pairs) - len(offenders))
            + " of "
            + str(len(pairs))
            + " shipped terms occur verbatim in their own source text",
        )

    def test_every_shipped_value_is_reproducible_from_its_recorded_span(self):
        checked = 0
        offenders = []
        for record in EXTRACTED:
            text = record.get("source_text") or ""
            spans = record.get("extraction_spans") or {}
            for field in fields_module.SCALAR_FIELDS:
                for span in spans.get(field, []):
                    checked += 1
                    if text[span["start"]:span["end"]] != span["text"]:
                        offenders.append((record.get("id"), field))
            for field in fields_module.LIST_FIELDS:
                terms = record.get(field, [])
                field_spans = spans.get(field, [])
                if len(terms) != len(field_spans):
                    # zip would silently drop the surplus, which is exactly how a
                    # term with no span reaches a resume unnoticed.
                    offenders.append(
                        (
                            record.get("id"),
                            field,
                            str(len(terms)) + " terms against "
                            + str(len(field_spans)) + " spans",
                        )
                    )
                for term, span in zip(terms, field_spans):
                    checked += 1
                    if text[span["start"]:span["end"]] != term:
                        offenders.append((record.get("id"), field, term))
        self.assertGreater(checked, 0, "VACUOUS: no spans shipped")
        self.assertEqual(
            offenders,
            [],
            str(checked - len(offenders))
            + " of "
            + str(checked)
            + " shipped values reproduce from their own span",
        )

    def test_every_non_unknown_scalar_has_a_span(self):
        missing = []
        determined = 0
        for record in EXTRACTED:
            spans = record.get("extraction_spans") or {}
            for field in fields_module.SCALAR_FIELDS:
                if record.get(field) == fields_module.UNKNOWN:
                    continue
                determined += 1
                if not spans.get(field):
                    missing.append((record.get("id"), field))
        self.assertGreater(determined, 0, "VACUOUS: no determined scalars shipped")
        self.assertEqual(
            missing,
            [],
            str(determined - len(missing))
            + " of "
            + str(determined)
            + " determined scalars carry a span",
        )

    def test_source_text_still_hashes_to_its_ingest_digest(self):
        offenders = [
            r.get("id")
            for r in ALL_RECORDS
            if intake_record.digest(r.get("source_text") or "")
            != r.get("source_text_digest")
        ]
        self.assertEqual(
            offenders,
            [],
            str(len(ALL_RECORDS) - len(offenders))
            + " of "
            + str(len(ALL_RECORDS))
            + " advertisements still hash to their ingest digest",
        )

    def test_every_extracted_record_names_its_producer(self):
        """INV-22 of pm/03-data-contract.md, checked on what shipped."""
        offenders = [r.get("id") for r in EXTRACTED if not r.get("model_id")]
        self.assertEqual(offenders, [], "extractions with no producer: " + str(offenders))

    def test_a_detected_injection_is_recorded_with_a_readable_span(self):
        flagged = [r for r in EXTRACTED if r.get("injected_instruction_detected")]
        if not flagged:
            self.skipTest("VACUOUS: no advertisement in the store carries a detection")
        for record in flagged:
            text = record.get("source_text") or ""
            spans = record.get("injected_instruction_spans") or []
            self.assertGreater(len(spans), 0)
            for span in spans:
                self.assertEqual(
                    text[span["start"]:span["end"]], span["quarantined_text"]
                )

    def test_no_skill_term_was_taken_from_inside_a_quarantined_region(self):
        checked = 0
        offenders = []
        for record in EXTRACTED:
            regions = record.get("injected_instruction_spans") or []
            if not regions:
                continue
            spans = record.get("extraction_spans") or {}
            for field in fields_module.FIELD_LIST:
                for span in spans.get(field, []):
                    checked += 1
                    for region in regions:
                        if region["start"] <= span["start"] < region["end"]:
                            offenders.append((record.get("id"), field, span["text"]))
        if not checked:
            self.skipTest("VACUOUS: no spans on any record carrying a detection")
        self.assertEqual(
            offenders,
            [],
            str(checked - len(offenders))
            + " of "
            + str(checked)
            + " shipped spans sit outside every quarantined region",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
