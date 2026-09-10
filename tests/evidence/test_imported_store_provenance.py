"""Content provenance for the shipped store.

The failure this file exists to catch is the unrecoverable one: a sentence that reaches
an employer and is not in the file its provenance cites. It is invisible, it survives
every other gate, and no downstream check can find it, because every downstream check
takes the evidence store as ground truth.

So these tests do not assert on objects the importer believes it wrote. They read
store/evidence/ off disk and check every word of every claim against the owner's source
file, and every date against the field it was taken from.

This module is read only with respect to store/evidence/. It writes nothing anywhere.

Run: python3 tests/evidence/test_imported_store_provenance.py
Environment:
  CAREER_OS_STORE     store root, default ./store
  CAREER_OS_FACTS     the owner's career facts JSON. When absent, the provenance tests
                      skip rather than pass, because a check that cannot run has not run.
"""

import glob
import json
import os
import re
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
)

from evidence import record as record_module  # noqa: E402
from evidence.store import EvidenceStore  # noqa: E402

DEFAULT_FACTS = "/Users/alisonhaire/Documents/My-Projects/resume-system/resume.base.json"
WORD = re.compile(r"[A-Za-z0-9']+")
YEAR = re.compile(r"(?:19|20)[0-9]{2}")

FACT_SECTIONS = (
    "experience", "education", "skills", "recognition", "highlights",
    "research", "talks", "hosting", "projects", "n8nWorkflows",
)


def facts_path():
    return os.environ.get("CAREER_OS_FACTS", DEFAULT_FACTS)


def load_facts():
    path = facts_path()
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_shipped():
    store = EvidenceStore(os.environ.get("CAREER_OS_STORE") or "./store")
    return store.all_records()


class TestShippedRecordsConformToE01(unittest.TestCase):
    def setUp(self):
        self.shipped = load_shipped()
        if not self.shipped:
            self.skipTest("no records in the store, so there is nothing shipped to check")

    def test_every_shipped_record_has_exactly_the_six_e01_fields(self):
        for stored in self.shipped:
            with self.subTest(record=stored.get("id")):
                self.assertEqual(sorted(stored), sorted(record_module.FIELDS))

    def test_every_shipped_record_validates(self):
        for stored in self.shipped:
            with self.subTest(record=stored.get("id")):
                self.assertEqual(record_module.validate(stored), [])

    def test_every_shipped_record_carries_a_non_empty_source_and_date(self):
        deficient = [
            r.get("id")
            for r in self.shipped
            if not (r.get("source") or "").strip() or not (r.get("date") or "").strip()
        ]
        self.assertEqual(deficient, [], "R-117 violated by these records")

    def test_the_denominator_is_stated_and_not_zero(self):
        self.assertGreater(len(self.shipped), 0)

    def test_identifiers_are_unique(self):
        identifiers = [r["id"] for r in self.shipped]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_the_filename_matches_the_record_identifier(self):
        root = os.environ.get("CAREER_OS_STORE") or "./store"
        for path in sorted(glob.glob(os.path.join(root, "evidence", "*.json"))):
            with open(path, "r", encoding="utf-8") as handle:
                stored = json.load(handle)
            with self.subTest(path=path):
                self.assertEqual(
                    os.path.basename(path), stored["id"] + ".json"
                )


class TestClaimTextIsNotInvented(unittest.TestCase):
    def setUp(self):
        self.facts = load_facts()
        if self.facts is None:
            self.skipTest("facts file not present at " + facts_path())
        self.shipped = load_shipped()
        if not self.shipped:
            self.skipTest("no records in the store")
        with open(facts_path(), "r", encoding="utf-8") as handle:
            self.vocabulary = set(WORD.findall(handle.read().lower()))
        self.by_id = {}
        for section in FACT_SECTIONS:
            for item in self.facts.get(section) or []:
                if item.get("id"):
                    self.by_id[item["id"]] = (section, item)

    def test_no_claim_text_contains_a_word_absent_from_the_owners_file(self):
        invented = {}
        for stored in self.shipped:
            words = set(WORD.findall(stored["claim_text"].lower()))
            missing = sorted(words - self.vocabulary)
            if missing:
                invented[stored["id"]] = missing
        self.assertEqual(invented, {}, "words in a claim that are in no source fact")

    def test_every_shipped_record_traces_to_a_fact_that_exists_in_the_file(self):
        orphans = [r["id"] for r in self.shipped if r["id"] not in self.by_id]
        self.assertEqual(orphans, [], "records with no matching fact in the source file")

    def test_every_date_appears_in_the_fact_it_was_taken_from(self):
        """The date's year must be literally present in the fact's own fields.

        A year that is not in the source fact is a guessed year, which is the specific
        fabrication R-117 exists to stop.
        """
        drifted = {}
        for stored in self.shipped:
            section, item = self.by_id[stored["id"]]
            candidate_text = " ".join(
                str(item.get(field, ""))
                for field in ("dates", "year", "meta", "text")
            )
            year = YEAR.search(stored["date"])
            self.assertIsNotNone(year, stored["id"] + " has no year in its date")
            if year.group(0) not in YEAR.findall(candidate_text):
                drifted[stored["id"]] = (stored["date"], candidate_text.strip())
        self.assertEqual(drifted, {}, "dates not present in the fact they came from")

    def test_no_shipped_record_rests_only_on_a_circular_source_token(self):
        """base_json and app_* answer whether the fact was in a resume, not where it
        came from. A record resting only on those has no provenance outside the estate's
        own output, which is the class of defect R-140 names."""
        circular = {"base_json", "app_n8n", "app_nvidia", "flagged_unverified"}
        offenders = []
        for stored in self.shipped:
            _, item = self.by_id[stored["id"]]
            tokens = set(item.get("source") or [])
            if tokens and tokens <= circular:
                offenders.append(stored["id"])
        self.assertEqual(offenders, [])

    def test_no_shipped_record_was_marked_excluded_until_verified(self):
        offenders = [
            r["id"]
            for r in self.shipped
            if self.by_id[r["id"]][1].get("status") == "excluded_until_verified"
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
