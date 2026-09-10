"""Every error case S-01 lists for advertisement intake, one test each.

The error cases, verbatim from pm/03-interfaces.md S-01:

1. The URL cannot be retrieved because the host does not resolve, the response is
   not a success, or the fetch times out. Nothing is stored, no advertisement_id
   is issued, and the caller sees the submitted URL returned with the failure kind
   and status code, so a person can tell a dead link from a paywall.
2. The URL retrieves a login wall, a consent interstitial or an empty client side
   shell rather than a posting.
3. source_kind is url but source_value is not a URL, or source_kind is missing.
4. The same URL is submitted twice.
5. The retrieval succeeds and the write of source_text fails.

Case 2 is answered differently from the behaviour S-01 suggests. S-01 says store
what was retrieved and let extraction mark every field unknown; F-01 of
pm/05-architecture.md names that as this component's failure mode, and the owner's
instruction for this task is that a shell must not be stored as the advertisement.
The test below asserts the refusal, so the deviation is visible in the test suite
rather than only in a comment.

No test touches the network or ./store.

Run: python3 tests/intake/test_intake_errors.py
"""

import os
import shutil
import socket
import sys
import tempfile
import unittest
import urllib.error
import urllib.request

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "src",
    ),
)

from intake import receive as receive_module  # noqa: E402
from intake import retrieval as retrieval_module  # noqa: E402
from intake.retrieval import Response, RetrievalFailed  # noqa: E402
from intake.store import JobAdStore  # noqa: E402

from test_url_and_paste import ASHBY_URL, POSTING_TEXT, ashby_board_bytes, board_fetcher  # noqa: E402

GENERIC_URL = "https://careers.example.com/jobs/1234"


class TemporaryStore(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="career-os-intake-errors-")
        self.store = JobAdStore(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)


class Case1UrlCannotBeRetrieved(TemporaryStore):
    def test_host_does_not_resolve(self):
        def raising(url, **_kwargs):
            raise RetrievalFailed("host did not resolve", "unreachable", url, None)

        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=raising
        )
        self.assertEqual("rejected", receipt.intake_status)
        self.assertIsNone(receipt.advertisement_id)
        self.assertEqual("unreachable", receipt.rejection["failure_kind"])
        self.assertIsNone(receipt.rejection["http_status"])
        self.assertEqual(ASHBY_URL, receipt.rejection["submitted_url"])
        self.assertEqual(0, self.store.count())

    def test_response_is_not_a_success(self):
        def paywalled(url, **_kwargs):
            return Response(url, 403, b"forbidden", "text/html")

        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=paywalled
        )
        self.assertEqual("rejected", receipt.intake_status)
        self.assertEqual("http_error", receipt.rejection["failure_kind"])
        self.assertEqual(403, receipt.rejection["http_status"])
        self.assertEqual(0, self.store.count())

    def test_a_dead_link_is_distinguishable_from_a_paywall(self):
        """The point of the failure kind and the status code being separate."""
        def dead(url, **_kwargs):
            raise RetrievalFailed("host did not resolve", "unreachable", url, None)

        def paywall(url, **_kwargs):
            return Response(url, 401, b"login", "text/html")

        one = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=dead
        )
        two = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=paywall
        )
        self.assertNotEqual(
            (one.rejection["failure_kind"], one.rejection["http_status"]),
            (two.rejection["failure_kind"], two.rejection["http_status"]),
        )

    def test_fetch_bytes_maps_a_timeout_to_the_timeout_kind(self):
        original = urllib.request.urlopen

        def timing_out(*_args, **_kwargs):
            raise socket.timeout("timed out")

        urllib.request.urlopen = timing_out
        try:
            with self.assertRaises(RetrievalFailed) as caught:
                retrieval_module.fetch_bytes(GENERIC_URL)
        finally:
            urllib.request.urlopen = original
        self.assertEqual("timeout", caught.exception.kind)

    def test_fetch_bytes_maps_an_unresolvable_host_to_unreachable(self):
        original = urllib.request.urlopen

        def failing(*_args, **_kwargs):
            raise urllib.error.URLError(socket.gaierror(8, "nodename nor servname provided"))

        urllib.request.urlopen = failing
        try:
            with self.assertRaises(RetrievalFailed) as caught:
                retrieval_module.fetch_bytes(GENERIC_URL)
        finally:
            urllib.request.urlopen = original
        self.assertEqual("unreachable", caught.exception.kind)
        self.assertIsNone(caught.exception.status)

    def test_fetch_bytes_carries_the_status_code_of_an_http_error(self):
        original = urllib.request.urlopen

        def erroring(*_args, **_kwargs):
            raise urllib.error.HTTPError(GENERIC_URL, 404, "Not Found", {}, None)

        urllib.request.urlopen = erroring
        try:
            with self.assertRaises(RetrievalFailed) as caught:
                retrieval_module.fetch_bytes(GENERIC_URL)
        finally:
            urllib.request.urlopen = original
        self.assertEqual("http_error", caught.exception.kind)
        self.assertEqual(404, caught.exception.status)


class Case2ShellOrWall(TemporaryStore):
    SHELL = (
        b"<!doctype html><html><head><title>Careers</title></head>"
        b"<body><div id=\"root\"></div><script>window.__data={};</script></body></html>"
    )

    def test_a_client_side_shell_is_refused_and_nothing_is_stored(self):
        def shell(url, **_kwargs):
            return Response(url, 200, self.SHELL, "text/html; charset=utf-8")

        receipt = receive_module.receive(
            "url", GENERIC_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=shell
        )
        self.assertEqual("rejected", receipt.intake_status)
        self.assertEqual("client_side_shell", receipt.rejection["failure_kind"])
        self.assertEqual(0, self.store.count())
        self.assertEqual([], self.store.submissions())

    def test_an_ashby_board_missing_the_posting_is_refused(self):
        body = ashby_board_bytes(posting_id="1111bbbb-1111-1111-1111-111111111111")
        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher(body)
        )
        self.assertEqual("rejected", receipt.intake_status)
        self.assertEqual("posting_not_found", receipt.rejection["failure_kind"])
        self.assertEqual(0, self.store.count())

    def test_a_malformed_posting_api_response_is_refused(self):
        receipt = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher(b"<html>nope")
        )
        self.assertEqual("rejected", receipt.intake_status)
        self.assertEqual("malformed_response", receipt.rejection["failure_kind"])
        self.assertEqual(0, self.store.count())

    def test_a_real_html_posting_on_a_generic_host_is_stored_as_visible_text(self):
        document = (
            "<!doctype html><html><body><h1>Senior Engineer</h1><p>"
            + ("We are hiring a senior engineer to work on the platform. " * 8)
            + "</p><script>var x=1;</script></body></html>"
        ).encode("utf-8")

        def page(url, **_kwargs):
            return Response(url, 200, document, "text/html; charset=utf-8")

        receipt = receive_module.receive(
            "url", GENERIC_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=page
        )
        self.assertEqual("stored", receipt.intake_status)
        shipped = self.store.get(receipt.advertisement_id)
        self.assertIn("Senior Engineer", shipped["source_text"])
        self.assertNotIn("var x=1", shipped["source_text"])
        # The normalised text is what ships; the undecoded body is retained beside it.
        with open(self.store.submission_path(receipt.submission_id, ".body"), "rb") as handle:
            self.assertEqual(document, handle.read())


class Case3RejectedSubmission(TemporaryStore):
    def test_source_kind_url_with_a_value_that_is_not_a_url(self):
        receipt = receive_module.receive(
            "url", "not a url at all", "2026-09-10T00:00:00Z", store=self.store
        )
        self.assertEqual("rejected", receipt.intake_status)
        self.assertIsNone(receipt.advertisement_id)
        self.assertEqual(["url", "pasted_text"], receipt.rejection["expected"])
        self.assertEqual(0, self.store.count())

    def test_source_kind_missing(self):
        receipt = receive_module.receive(None, ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store)
        self.assertEqual("rejected", receipt.intake_status)
        self.assertEqual("source_kind", receipt.rejection["field"])
        self.assertEqual(["url", "pasted_text"], receipt.rejection["expected"])
        self.assertEqual(0, self.store.count())

    def test_source_kind_is_not_one_of_the_two_forms(self):
        receipt = receive_module.receive("pdf", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store)
        self.assertEqual("rejected", receipt.intake_status)
        self.assertEqual(["url", "pasted_text"], receipt.rejection["expected"])

    def test_empty_paste_is_rejected(self):
        receipt = receive_module.receive(
            "pasted_text", "   \n  ", "2026-09-10T00:00:00Z", store=self.store
        )
        self.assertEqual("rejected", receipt.intake_status)
        self.assertEqual("source_value", receipt.rejection["field"])
        self.assertEqual(0, self.store.count())

    def test_captured_at_is_required(self):
        receipt = receive_module.receive("pasted_text", POSTING_TEXT, None, store=self.store)
        self.assertEqual("rejected", receipt.intake_status)
        self.assertEqual("captured_at", receipt.rejection["field"])
        self.assertEqual(0, self.store.count())


class Case4SameUrlTwice(TemporaryStore):
    def test_second_submission_returns_the_existing_identifier(self):
        first = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher()
        )
        before = self.store.count()
        second = receive_module.receive(
            "url", ASHBY_URL, "2026-09-10T01:00:00Z", store=self.store, fetcher=board_fetcher()
        )
        self.assertEqual("duplicate", second.intake_status)
        self.assertEqual(first.advertisement_id, second.advertisement_id)
        self.assertEqual(before, self.store.count())
        self.assertIsNotNone(self.store.get(second.advertisement_id))


class Case5WriteFails(TemporaryStore):
    def test_no_identifier_is_issued_and_the_submission_is_left_orphaned(self):
        def refuse(_candidate):
            raise OSError("disk full")

        self.store.write = refuse
        with self.assertRaises(OSError):
            receive_module.receive(
                "url", ASHBY_URL, "2026-09-10T00:00:00Z", store=self.store, fetcher=board_fetcher()
            )
        self.assertEqual(0, self.store.count())
        orphans = self.store.orphan_submissions()
        self.assertEqual(1, len(orphans), "the retrieval should be visible with no advertisement behind it")
        self.assertEqual(ASHBY_URL, orphans[0]["submitted_url"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
