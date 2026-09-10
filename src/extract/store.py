"""Writing an extraction back onto an existing advertisement record.

The one thing this module must never do is change source_text. R-120 requires it
be retained unmodified and checks it by recomputing its digest, so this module
reads the record, verifies the digest it arrived with, merges only extraction
keys, writes, and verifies the digest again off disk. If the digest moves at any
point the write is refused and the record on disk is left as it was.

The E-03 field set, the digest function and the validation predicate are taken
from src/intake/record.py rather than restated, because two copies of a schema
drift and the digest in particular has exactly one correct definition.
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intake import record as intake_record  # noqa: E402

COLLECTION = "job_ads"
DEFAULT_STORE = "./store"

# Keys this module is allowed to write. source_text, source_text_digest, id,
# intake_kind, source_url and ingested_at are not on this list and are carried
# through untouched.
EXTRACTION_KEYS = (
    "employer",
    "role_title",
    "seniority",
    "location",
    "work_arrangement",
    "required_skills",
    "required_skills_determined",
    "preferred_skills",
    "preferred_skills_determined",
    "model_id",
    "extraction_method",
    "extraction_rules_version",
    "extraction_status",
    "extracted_at",
    "extraction_spans",
    "extraction_unknown_reasons",
    "extraction_unanswered_fields",
    "dropped_terms",
    "injected_instruction_detected",
    "injected_instruction_spans",
)


class WriteRefused(Exception):
    """The write was refused. The record on disk is unchanged."""


def store_root(explicit=None):
    if explicit is not None:
        return explicit
    return os.environ.get("CAREER_OS_STORE") or DEFAULT_STORE


class ExtractionStore:
    def __init__(self, root=None):
        self.root = store_root(root)

    def collection_dir(self):
        return os.path.join(self.root, COLLECTION)

    def record_path(self, advertisement_id):
        return os.path.join(self.collection_dir(), advertisement_id + ".json")

    def paths(self):
        return sorted(glob.glob(os.path.join(self.collection_dir(), "*.json")))

    def all_records(self):
        loaded = []
        for path in self.paths():
            with open(path, "r", encoding="utf-8") as handle:
                loaded.append(json.load(handle))
        return loaded

    def get(self, advertisement_id):
        path = self.record_path(advertisement_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def apply(self, advertisement_id, fields, extracted_at):
        """Merge one extraction onto one advertisement. Returns the stored record."""
        path = self.record_path(advertisement_id)
        if not os.path.exists(path):
            raise WriteRefused("no advertisement " + advertisement_id)
        with open(path, "r", encoding="utf-8") as handle:
            stored = json.load(handle)

        text = stored.get("source_text")
        before = stored.get("source_text_digest")
        if not isinstance(text, str) or intake_record.digest(text) != before:
            raise WriteRefused(
                advertisement_id
                + ": source_text does not match the digest it was stored with, "
                "so nothing may be written over it"
            )

        unexpected = [k for k in fields if k not in EXTRACTION_KEYS]
        if unexpected:
            raise WriteRefused(
                advertisement_id
                + ": refusing to write non extraction keys "
                + ", ".join(sorted(unexpected))
            )

        candidate = dict(stored)
        candidate.update(fields)
        candidate["extracted_at"] = extracted_at
        candidate["source_text"] = text
        candidate["source_text_digest"] = before

        problems = intake_record.validate(candidate)
        if problems:
            raise WriteRefused(
                advertisement_id + ": E-03 violated at " + ", ".join(problems)
            )

        _write_json(path, candidate)

        with open(path, "r", encoding="utf-8") as handle:
            written = json.load(handle)
        after = intake_record.digest(written.get("source_text") or "")
        if after != before or written.get("source_text") != text:
            raise WriteRefused(
                advertisement_id
                + ": source_text changed across the write, digest before "
                + before
                + " after "
                + after
            )
        return written


def _write_json(path, payload):
    """Same shape as the intake writer: temporary file, one rename.

    Formatting matches src/intake/store.py exactly, so a record that has been
    extracted and one that has not are byte comparable outside the keys that
    changed.
    """
    temporary = path + ".partial"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)
