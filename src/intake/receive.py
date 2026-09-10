"""S-01 Advertisement intake, the seam itself.

Inputs, outputs and every error case are taken from S-01 in pm/03-interfaces.md.

Inputs:  source_kind, one of url or pasted_text; source_value, a single URL or a
         block of text; captured_at, when the caller obtained the advertisement.
Outputs: advertisement_id, source_text, retrieval_record, intake_status.

intake_status is one of stored, duplicate or rejected, which are the three values
S-01 names. A rejection returns a Receipt rather than raising, because the caller
is told which form was expected and, for a URL that could not be retrieved, the
failure kind and the status code, so a dead link reads differently from a paywall.

One S-01 error case is answered differently from the way that file suggests, and
the reason is written out in src/intake/retrieval.py: a login wall, a consent
interstitial or an empty client side shell is refused rather than stored.

Nothing here reads the posting. Employer, role title, seniority, location, work
arrangement and the skill lists are written at their E-03 defaults and are R-120
and R-121's business, at seam S-02.
"""

import datetime
import hashlib

from . import record as record_module
from . import retrieval as retrieval_module
from .retrieval import RetrievalFailed
from .store import JobAdStore

STORED = "stored"
DUPLICATE = "duplicate"
REJECTED = "rejected"

ACCEPTED_FORMS = record_module.INTAKE_KINDS


class Receipt:
    """What S-01 hands back. `rejection` is populated only when status is rejected."""

    def __init__(
        self,
        intake_status,
        advertisement_id=None,
        source_text=None,
        retrieval_record=None,
        rejection=None,
        submission_id=None,
    ):
        self.intake_status = intake_status
        self.advertisement_id = advertisement_id
        self.source_text = source_text
        self.retrieval_record = retrieval_record
        self.rejection = rejection
        self.submission_id = submission_id

    def as_dict(self):
        return {
            "intake_status": self.intake_status,
            "advertisement_id": self.advertisement_id,
            "source_text_chars": len(self.source_text or ""),
            "source_text_bytes": len((self.source_text or "").encode("utf-8")),
            "retrieval_record": self.retrieval_record,
            "rejection": self.rejection,
            "submission_id": self.submission_id,
        }


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def receive(
    source_kind,
    source_value,
    captured_at,
    store=None,
    fetcher=retrieval_module.fetch_bytes,
    now=utc_now,
):
    """Take one submission through S-01. Returns a Receipt."""
    store = store if store is not None else JobAdStore()

    rejection = _check_inputs(source_kind, source_value, captured_at)
    if rejection is not None:
        return Receipt(REJECTED, rejection=rejection)

    if source_kind == "url":
        return _receive_url(source_value.strip(), captured_at, store, fetcher, now)
    return _receive_paste(source_value, captured_at, store, now)


def _check_inputs(source_kind, source_value, captured_at):
    if source_kind is None or source_kind not in ACCEPTED_FORMS:
        return {
            "reason": "source_kind absent or not an accepted form",
            "field": "source_kind",
            "expected": list(ACCEPTED_FORMS),
            "received": source_kind,
        }
    if not isinstance(source_value, str) or not source_value.strip():
        return {
            "reason": "source_value absent or empty",
            "field": "source_value",
            "expected": list(ACCEPTED_FORMS),
            "received": None,
        }
    if source_kind == "url" and not record_module.looks_like_url(source_value):
        return {
            "reason": "source_kind is url but source_value is not a URL",
            "field": "source_value",
            "expected": list(ACCEPTED_FORMS),
            "received": source_value[:200],
        }
    if not _is_timestamp(captured_at):
        return {
            "reason": "captured_at absent or not a timestamp",
            "field": "captured_at",
            "expected": list(ACCEPTED_FORMS),
            "received": captured_at,
        }
    return None


def _is_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _receive_url(url, captured_at, store, fetcher, now):
    existing = store.find_by_source_url(url)
    if existing is not None:
        # S-01: the count of advertisements does not increase and the caller still
        # receives a usable identifier. The posting is not re-fetched.
        return Receipt(
            DUPLICATE,
            advertisement_id=existing["id"],
            source_text=existing.get("source_text"),
            retrieval_record=None,
        )

    try:
        got = retrieval_module.retrieve(url, fetcher=fetcher)
    except RetrievalFailed as failure:
        # Nothing is stored and no advertisement_id is issued. The caller sees the
        # submitted URL back with the failure kind and the status code.
        rejection = failure.as_dict()
        rejection["reason"] = "the URL did not yield a posting"
        rejection["submitted_url"] = url
        return Receipt(REJECTED, rejection=rejection)

    retrieval_record = {
        "submitted_url": url,
        "fetched_url": got.fetched_url,
        "fetched_at": now(),
        "http_status": got.status,
        "content_type": got.content_type,
        "captured_at": captured_at,
        "text_source": got.text_source,
        "source_text_is_whole_body": got.text_is_whole_body,
        "body_bytes": len(got.body),
        "body_digest_sha256": hashlib.sha256(got.body).hexdigest(),
    }
    return _store(
        store,
        intake_kind="url",
        source_text=got.text,
        source_url=url,
        captured_at=captured_at,
        body=got.body,
        retrieval_record=retrieval_record,
        now=now,
    )


def _receive_paste(text, captured_at, store, now):
    body = text.encode("utf-8")
    submission_extras = {
        "submitted_url": None,
        "fetched_url": None,
        "fetched_at": None,
        "http_status": None,
        "content_type": "text/plain; charset=utf-8",
        "captured_at": captured_at,
        "text_source": "pasted by the caller, verbatim",
        "source_text_is_whole_body": True,
        "body_bytes": len(body),
        "body_digest_sha256": hashlib.sha256(body).hexdigest(),
    }
    return _store(
        store,
        intake_kind="pasted_text",
        source_text=text,
        source_url=None,
        captured_at=captured_at,
        body=body,
        retrieval_record=submission_extras,
        now=now,
    )


def _store(
    store,
    intake_kind,
    source_text,
    source_url,
    captured_at,
    body,
    retrieval_record,
    now,
):
    candidate = record_module.build(
        intake_kind=intake_kind,
        source_text=source_text,
        ingested_at=now(),
        source_url=source_url,
    )

    if store.get(candidate["id"]) is not None:
        return Receipt(
            DUPLICATE,
            advertisement_id=candidate["id"],
            source_text=source_text,
            retrieval_record=retrieval_record if intake_kind == "url" else None,
        )

    submission = dict(retrieval_record)
    submission.update(
        {
            "id": _submission_id(intake_kind, source_url, captured_at, body),
            "intake_kind": intake_kind,
            "advertisement_id": candidate["id"],
            "source_text_digest": candidate["source_text_digest"],
            "source_text_chars": len(source_text),
        }
    )
    # Written first and on its own, so that a failed write of source_text leaves a
    # submission with no advertisement behind it, which is the S-01 observable that
    # separates a lost body from a fetch that never happened.
    store.write_submission(submission, body)

    advertisement_id = store.write(candidate)
    return Receipt(
        STORED,
        advertisement_id=advertisement_id,
        source_text=source_text,
        retrieval_record=retrieval_record if intake_kind == "url" else None,
        submission_id=submission["id"],
    )


def _submission_id(intake_kind, source_url, captured_at, body):
    material = "\x00".join([intake_kind, source_url or "", captured_at]).encode("utf-8")
    return "sub_" + hashlib.sha256(material + b"\x00" + body).hexdigest()[:16]
