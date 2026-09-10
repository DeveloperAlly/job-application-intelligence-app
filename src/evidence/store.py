"""S-04 Evidence record store.

Serves R-117 and R-140. Written from pm/03-interfaces.md seam S-04 and
pm/03-data-contract.md entity E-01, per ADR-001.

Physical form, which is a step 5 binding and not a contract decision: the store is a
directory addressed by the environment variable CAREER_OS_STORE, defaulting to ./store,
holding one JSON file per record under a collection directory. Evidence records live in
`<store>/evidence/<id>.json`. That is the shape the acceptance commands for R-117 and
R-140 in pm/03-requirements.md read, and the shape INV-01 and INV-26 in
pm/03-data-contract.md read.

Two rules are enforced here rather than audited later.

R-117. A write with no source or no date is rejected, no identifier is issued, the record
count does not change, and the rejection names the absent field. That is the S-04 error
case verbatim.

R-140. A record whose source_kind is `document` and whose source resolves to a document
this system generated is not accepted as provenance for a claim. The record may exist,
because R-117 does not forbid it, but `provenance_records()` will not return it and
`assert_acceptable_as_provenance()` refuses it. The set of generated documents is read
from the `documents` collection, by id and by render_uri, which is the same resolution
INV-26 performs.
"""

import glob
import json
import os

from . import record as record_module
from .record import RecordInvalid

EVIDENCE_COLLECTION = "evidence"
DOCUMENTS_COLLECTION = "documents"

DEFAULT_STORE = "./store"


class WriteRejected(Exception):
    """A write was refused. `fields` names what was absent or wrong."""

    def __init__(self, message, fields):
        super().__init__(message)
        self.fields = tuple(fields)


class ProvenanceRefused(Exception):
    """A record exists but may not stand as provenance for a claim, per R-140."""

    def __init__(self, message, record_id, source):
        super().__init__(message)
        self.record_id = record_id
        self.source = source


def store_root(explicit=None):
    """Resolve the store root: an explicit argument, else CAREER_OS_STORE, else ./store."""
    if explicit is not None:
        return explicit
    return os.environ.get("CAREER_OS_STORE") or DEFAULT_STORE


class EvidenceStore:
    def __init__(self, root=None):
        self.root = store_root(root)

    # paths

    def collection_dir(self, collection):
        return os.path.join(self.root, collection)

    def record_path(self, record_id, collection=EVIDENCE_COLLECTION):
        return os.path.join(self.collection_dir(collection), record_id + ".json")

    # reads

    def _load_collection(self, collection):
        pattern = os.path.join(self.collection_dir(collection), "*.json")
        loaded = []
        for path in sorted(glob.glob(pattern)):
            with open(path, "r", encoding="utf-8") as handle:
                loaded.append(json.load(handle))
        return loaded

    def all_records(self):
        """Every stored evidence record, read back off disk.

        Callers that want to assert on what shipped must use this rather than the
        objects they believe they wrote.
        """
        return self._load_collection(EVIDENCE_COLLECTION)

    def get(self, record_id):
        path = self.record_path(record_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def count(self):
        return len(glob.glob(os.path.join(self.collection_dir(EVIDENCE_COLLECTION), "*.json")))

    def query(self, term=None, kind=None, date_prefix=None):
        """The S-04 read seam. Returns matching records, possibly empty.

        An empty result is a result, not an error. S-04 requires the selection seam to
        convert an empty result into a stated omission rather than silence, so this
        returns a list and never raises on no match.
        """
        results = []
        for stored in self.all_records():
            if kind is not None and stored.get("kind") != kind:
                continue
            if date_prefix is not None and not str(stored.get("date", "")).startswith(date_prefix):
                continue
            if term is not None and term.lower() not in stored.get("claim_text", "").lower():
                continue
            results.append(stored)
        return results

    # R-140

    def generated_document_identifiers(self):
        """Identifiers and addresses of documents this system generated.

        Read from the `documents` collection by id and by render_uri, the same two keys
        INV-26 and the R-140 acceptance command join on. When no document has ever been
        generated this set is empty and the R-140 predicate is vacuous, which is a
        different statement from the predicate passing.
        """
        documents = self._load_collection(DOCUMENTS_COLLECTION)
        identifiers = {str(d.get("id")) for d in documents if d.get("id") is not None}
        identifiers |= {
            str(d.get("render_uri")) for d in documents if d.get("render_uri")
        }
        return identifiers

    def is_self_generated_provenance(self, candidate, generated=None):
        """True when this record cites a document this system generated as its source."""
        if generated is None:
            generated = self.generated_document_identifiers()
        return (
            candidate.get("source_kind") == "document"
            and str(candidate.get("source")) in generated
        )

    def assert_acceptable_as_provenance(self, candidate):
        """Raise ProvenanceRefused when R-140 forbids this record standing behind a claim."""
        if self.is_self_generated_provenance(candidate):
            raise ProvenanceRefused(
                "R-140: source resolves to a document this system generated",
                candidate.get("id"),
                candidate.get("source"),
            )
        return candidate

    def provenance_records(self):
        """The records that may stand as provenance for a claim, per R-140."""
        generated = self.generated_document_identifiers()
        return [
            stored
            for stored in self.all_records()
            if not self.is_self_generated_provenance(stored, generated)
        ]

    # writes

    def write(self, candidate, overwrite=False):
        """Store one evidence record. Returns (write_status, evidence_record_id_or_None).

        write_status is "stored" or "rejected", which are the two values S-04 names.
        On rejection no identifier is issued and no file is created, so the record count
        is unchanged. WriteRejected carries the field names at fault.
        """
        problems = record_module.validate(candidate)
        if problems:
            raise WriteRejected(
                "rejected: " + ", ".join(problems) + " absent or invalid", problems
            )

        # R-140 is a provenance rule, not a storage rule. The record is refused at write
        # time as well, because a store that accepts it has already made the circular
        # claim reachable and every downstream check will pass on it.
        self.assert_acceptable_as_provenance(candidate)

        path = self.record_path(candidate["id"])
        if os.path.exists(path) and not overwrite:
            raise WriteRejected("rejected: id already stored", ["id"])

        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {field: candidate[field] for field in record_module.FIELDS}
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        return "stored", candidate["id"]

    def try_write(self, candidate, overwrite=False):
        """write() without the exception. Returns (status, identifier, reasons)."""
        try:
            status, identifier = self.write(candidate, overwrite=overwrite)
            return status, identifier, []
        except WriteRejected as rejection:
            return "rejected", None, list(rejection.fields)
        except ProvenanceRefused as refusal:
            return "rejected", None, ["source:" + str(refusal.source)]


__all__ = [
    "EvidenceStore",
    "WriteRejected",
    "ProvenanceRefused",
    "RecordInvalid",
    "store_root",
    "EVIDENCE_COLLECTION",
    "DOCUMENTS_COLLECTION",
]
