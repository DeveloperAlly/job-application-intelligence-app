"""The job_ads collection on disk.

Physical form, which is a step 5 binding and not a contract decision: the store
is a directory addressed by the environment variable CAREER_OS_STORE, defaulting
to ./store, holding one JSON file per record under a collection directory.
Advertisements live in `<store>/job_ads/<id>.json`, which is the shape the R-119
acceptance command in pm/03-requirements.md and INV-04, INV-05 and INV-06 in
pm/03-data-contract.md read.

Two sidecar directories sit under the collection rather than beside it, so that
`job_ads/*.json` still globs to advertisements and nothing else:

- `<store>/job_ads/submissions/<submission_id>.json` holds one record per intake
  attempt: the URL, the fetch time, the response status, the caller's captured_at
  and where the raw bytes were put. S-01 names a retrieval_record and requires
  that a retrieval whose write failed be observable with no advertisement behind
  it, which is only possible if it is persisted separately and first.
- `<store>/job_ads/submissions/<submission_id>.body` holds the response body or
  the pasted bytes exactly as received, unparsed and undecoded. When source_text
  is a decoded field of that body rather than the whole of it, this file is the
  original the rule about retaining the byte exact original points at.
"""

import glob
import json
import os

from . import record as record_module

COLLECTION = "job_ads"
SUBMISSIONS = os.path.join(COLLECTION, "submissions")
DEFAULT_STORE = "./store"


class WriteRejected(Exception):
    """A write was refused. `fields` names what was absent or wrong."""

    def __init__(self, message, fields):
        super().__init__(message)
        self.fields = tuple(fields)


def store_root(explicit=None):
    """Resolve the store root: an explicit argument, else CAREER_OS_STORE, else ./store."""
    if explicit is not None:
        return explicit
    return os.environ.get("CAREER_OS_STORE") or DEFAULT_STORE


class JobAdStore:
    def __init__(self, root=None):
        self.root = store_root(root)

    # paths

    def collection_dir(self):
        return os.path.join(self.root, COLLECTION)

    def submissions_dir(self):
        return os.path.join(self.root, SUBMISSIONS)

    def record_path(self, advertisement_id):
        return os.path.join(self.collection_dir(), advertisement_id + ".json")

    def submission_path(self, submission_id, suffix=".json"):
        return os.path.join(self.submissions_dir(), submission_id + suffix)

    # reads

    def all_records(self):
        """Every stored advertisement, read back off disk.

        Callers asserting on what shipped must use this rather than the object
        they believe they wrote.
        """
        loaded = []
        for path in sorted(glob.glob(os.path.join(self.collection_dir(), "*.json"))):
            with open(path, "r", encoding="utf-8") as handle:
                loaded.append(json.load(handle))
        return loaded

    def get(self, advertisement_id):
        path = self.record_path(advertisement_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def count(self):
        return len(glob.glob(os.path.join(self.collection_dir(), "*.json")))

    def find_by_source_url(self, source_url):
        """The advertisement already stored for this URL, or None.

        S-01: the same URL submitted twice returns the existing identifier with
        intake_status duplicate rather than issuing a second one.
        """
        if not source_url:
            return None
        for stored in self.all_records():
            if stored.get("source_url") == source_url:
                return stored
        return None

    def submissions(self):
        loaded = []
        for path in sorted(glob.glob(os.path.join(self.submissions_dir(), "*.json"))):
            with open(path, "r", encoding="utf-8") as handle:
                loaded.append(json.load(handle))
        return loaded

    def orphan_submissions(self):
        """Submissions with no advertisement behind them.

        This is the S-01 observable for a retrieval that succeeded while the
        write of source_text failed.
        """
        present = {stored.get("id") for stored in self.all_records()}
        return [
            s
            for s in self.submissions()
            if s.get("advertisement_id") not in present
        ]

    # writes

    def write_submission(self, submission, body_bytes):
        """Persist the intake attempt and its raw bytes, before any advertisement exists."""
        path = self.submission_path(submission["id"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if body_bytes is not None:
            with open(self.submission_path(submission["id"], ".body"), "wb") as handle:
                handle.write(body_bytes)
        _write_json(path, submission)
        return path

    def write(self, candidate):
        """Store one advertisement. Returns its identifier.

        Refuses a record that does not satisfy E-03, in which case no file is
        created and the record count is unchanged.
        """
        problems = record_module.validate(candidate)
        if problems:
            raise WriteRejected(
                "rejected: " + ", ".join(problems) + " absent or invalid", problems
            )
        payload = {f: candidate[f] for f in record_module.FIELDS if f in candidate}
        path = self.record_path(candidate["id"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _write_json(path, payload)
        return candidate["id"]


def _write_json(path, payload):
    """Write JSON through a temporary file and one rename.

    A half written record would fail its own digest check and be indistinguishable
    from tampering, so a record is either wholly there or not there at all.
    """
    temporary = path + ".partial"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)
