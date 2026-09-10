"""R-119: a job advertisement enters by URL or by pasted text.

Every test builds its own store under a temporary directory and deletes it. None
of them reads or writes ./store, because a test that mutates the shipped store is
a defect and would also make the acceptance command unreproducible. No test here
touches the network: the fetcher is injected.

Assertions are made on records read back off disk, never on the object the test
believes it wrote.

Run: python3 tests/intake/test_url_and_paste.py
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "src",
    ),
)

from intake import record as record_module  # noqa: E402
from intake import receive as receive_module  # noqa: E402
from intake.retrieval import Response  # noqa: E402
from intake.store import JobAdStore  # noqa: E402

ASHBY_URL = "https://jobs.ashbyhq.com/exampleorg/9f38ecfe-ee22-4338-863b-a01e43a481bc"
POSTING_ID = "9f38ecfe-ee22-4338-863b-a01e43a481bc"

# Long enough to clear the shell floor, and shaped like a posting.
POSTING_TEXT = (
    "As a Customer Engineer, you will be the technical lead on enterprise sales cycles.\n"
    "\n"
    "What You'll Do\n"
    " - Lead technical discovery with prospects and their platform teams\n"
    " - Build demo environments against the public API\n"
    " - Write integration guides in Python and TypeScript\n"
    "\n"
    "What We're Looking For\n"
    " - 4+ years in a customer facing engineering role\n"
    " - Comfortable reading and writing production code\n"
)


def ashby_board_bytes(text=POSTING_TEXT, posting_id=POSTING_ID):
    payload = {
        "jobs": [
            {"id": "0000aaaa-0000-0000-0000-000000000000", "descriptionPlain": "another posting"},
            {
                "id": posting_id,
                "title": "Customer Engineer",
                "location": "Remote (US)",
                "descriptionPlain": text,
            },
        ],
        "apiVersion": "1",
    }
    return json.dumps(payload).encode("utf-8")


def board_fetcher(body=None, status=200):
    body = ashby_board_bytes() if body is None else body

    def fetch(url, **_kwargs):
        return Response(url, status, body, "application/json")

    return fetch


class TemporaryStore(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="career-os-intake-test-")
        self.store = JobAdStore(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def stored_ads(self):
        return self.store.all_records()


class UrlIntake(TemporaryStore):
    def test_url_submission_stores_the_posting_text_the_server_returned(self):
        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher()
        )
        self.assertEqual("stored", receipt.intake_status)

        shipped = self.store.get(receipt.advertisement_id)
        self.assertIsNotNone(shipped, "no record was written to disk")
        self.assertEqual("url", shipped["intake_kind"])
        self.assertEqual(ASHBY_URL, shipped["source_url"])
        self.assertEqual(POSTING_TEXT, shipped["source_text"])

    def test_stored_text_hashes_to_what_the_server_returned(self):
        body = ashby_board_bytes()
        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher(body)
        )
        from_server = json.loads(body.decode("utf-8"))["jobs"][1]["descriptionPlain"]
        shipped = self.store.get(receipt.advertisement_id)
        self.assertEqual(
            hashlib.sha256(from_server.encode("utf-8")).hexdigest(),
            hashlib.sha256(shipped["source_text"].encode("utf-8")).hexdigest(),
        )
        # INV-05: the digest stored at ingest still matches the text on disk.
        self.assertEqual(
            shipped["source_text_digest"],
            hashlib.sha256(shipped["source_text"].encode("utf-8")).hexdigest(),
        )

    def test_the_raw_response_is_retained_beside_the_record(self):
        body = ashby_board_bytes()
        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher(body)
        )
        path = self.store.submission_path(receipt.submission_id, ".body")
        with open(path, "rb") as handle:
            self.assertEqual(body, handle.read())
        with open(self.store.submission_path(receipt.submission_id), encoding="utf-8") as handle:
            submission = json.load(handle)
        self.assertEqual(hashlib.sha256(body).hexdigest(), submission["body_digest_sha256"])
        self.assertIn("descriptionPlain", submission["text_source"])
        self.assertFalse(submission["source_text_is_whole_body"])

    def test_the_seam_returns_a_retrieval_record_for_a_url(self):
        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher()
        )
        self.assertIsNotNone(receipt.retrieval_record)
        self.assertEqual(ASHBY_URL, receipt.retrieval_record["submitted_url"])
        self.assertEqual(200, receipt.retrieval_record["http_status"])
        self.assertTrue(receipt.retrieval_record["fetched_at"])


class PasteIntake(TemporaryStore):
    def test_pasted_submission_stores_no_source_url(self):
        receipt = receive_module.receive(
            "pasted_text", POSTING_TEXT, "2026-09-10T00:00:00Z", store=self.store
        )
        self.assertEqual("stored", receipt.intake_status)
        shipped = self.store.get(receipt.advertisement_id)
        self.assertEqual("pasted_text", shipped["intake_kind"])
        self.assertNotIn("source_url", shipped)
        self.assertEqual(POSTING_TEXT, shipped["source_text"])

    def test_the_seam_returns_no_retrieval_record_for_pasted_text(self):
        receipt = receive_module.receive(
            "pasted_text", POSTING_TEXT, "2026-09-10T00:00:00Z", store=self.store
        )
        self.assertIsNone(receipt.retrieval_record)

    def test_pasted_bytes_are_retained_exactly(self):
        awkward = "Role: Senior Engineer\r\n\tTabbed line   \nQ&A &amp; more … café 你好 €\n\n" + POSTING_TEXT
        receipt = receive_module.receive(
            "pasted_text", awkward, "2026-09-10T00:00:00Z", store=self.store
        )
        shipped = self.store.get(receipt.advertisement_id)
        self.assertEqual(awkward, shipped["source_text"])
        self.assertEqual(record_module.digest(awkward), shipped["source_text_digest"])
        with open(self.store.submission_path(receipt.submission_id, ".body"), "rb") as handle:
            self.assertEqual(awkward.encode("utf-8"), handle.read())


class BothKinds(TemporaryStore):
    def setUp(self):
        super().setUp()
        self.url_receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher()
        )
        self.paste_receipt = receive_module.receive(
            "pasted_text", POSTING_TEXT, "2026-09-10T00:00:00Z", store=self.store
        )

    def test_the_same_text_by_two_kinds_is_two_records(self):
        self.assertNotEqual(self.url_receipt.advertisement_id, self.paste_receipt.advertisement_id)
        self.assertEqual(2, self.store.count())

    def test_r119_predicate_holds_over_the_store(self):
        """The R-119 acceptance predicate, restated over records read off disk."""
        ads = self.stored_ads()
        legal = [
            a
            for a in ads
            if a.get("intake_kind") in ("url", "pasted_text")
            and (a.get("intake_kind") == "url") == bool(a.get("source_url"))
        ]
        kinds = {a.get("intake_kind") for a in ads} & {"url", "pasted_text"}
        self.assertEqual(len(ads), len(legal), str(len(legal)) + " of " + str(len(ads)) + " legal")
        self.assertEqual(2, len(kinds), "both intake kinds must be exercised")

    def test_intake_does_not_extract_any_field(self):
        """R-120 and R-121 are S-02's work. Intake writes the E-03 defaults only."""
        for shipped in self.stored_ads():
            self.assertEqual("unknown", shipped["employer"])
            self.assertEqual("unknown", shipped["role_title"])
            self.assertEqual("unknown", shipped["seniority"])
            self.assertEqual("unknown", shipped["location"])
            self.assertEqual("unknown", shipped["work_arrangement"])
            self.assertEqual([], shipped["required_skills"])
            self.assertEqual([], shipped["preferred_skills"])
            self.assertFalse(shipped["required_skills_determined"])
            self.assertFalse(shipped["preferred_skills_determined"])

    def test_stored_records_carry_no_field_outside_e03(self):
        allowed = set(record_module.FIELDS)
        for shipped in self.stored_ads():
            self.assertEqual(set(), set(shipped) - allowed, "field written that E-03 does not name")

    def test_no_ad_carries_a_model_id_before_extraction_has_run(self):
        for shipped in self.stored_ads():
            self.assertNotIn("model_id", shipped)
            self.assertNotIn("posting_group_id", shipped)


class PoisonedStore(TemporaryStore):
    """The gate must be seen red against a real defect, not only green."""

    def test_removing_source_url_from_a_url_record_breaks_the_predicate(self):
        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher()
        )
        path = self.store.record_path(receipt.advertisement_id)
        with open(path, encoding="utf-8") as handle:
            poisoned = json.load(handle)
        del poisoned["source_url"]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(poisoned, handle)

        ads = self.stored_ads()
        legal = [
            a
            for a in ads
            if a.get("intake_kind") in ("url", "pasted_text")
            and (a.get("intake_kind") == "url") == bool(a.get("source_url"))
        ]
        self.assertNotEqual(len(ads), len(legal), "predicate stayed green over a poisoned record")

    def test_the_store_refuses_to_write_that_record_in_the_first_place(self):
        from intake.store import WriteRejected

        candidate = record_module.build(
            "url", POSTING_TEXT, "2026-09-10T00:00:00Z", source_url=ASHBY_URL
        )
        del candidate["source_url"]
        with self.assertRaises(WriteRejected) as caught:
            self.store.write(candidate)
        self.assertIn("source_url", caught.exception.fields)
        self.assertEqual(0, self.store.count())


if __name__ == "__main__":
    unittest.main(verbosity=2)
