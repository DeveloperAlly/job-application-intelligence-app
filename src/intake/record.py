"""E-03 JobAd: the field set, the defaults, the digest, and validation.

Field names, types, required flags and defaults are taken from the E-03 table in
pm/03-data-contract.md and from nowhere else. Two fields the contract marks
optional, model_id and posting_group_id, are deliberately absent at intake: note
10 of that file records that an advertisement is stored before extraction runs,
so there is nothing to write in them yet.

The extracted fields (employer, role_title, seniority, location,
work_arrangement, the two skill lists and their determined flags) are written at
the defaults the contract states. Nothing here reads the posting to fill them.
"""

import hashlib
import re

UNKNOWN = "unknown"

INTAKE_KINDS = ("url", "pasted_text")
WORK_ARRANGEMENTS = ("remote", "hybrid", "onsite", "unknown")

# E-03, in the order the data contract lists them. model_id and posting_group_id
# are omitted at intake, see the module docstring.
FIELDS = (
    "id",
    "intake_kind",
    "source_url",
    "source_text",
    "source_text_digest",
    "ingested_at",
    "employer",
    "role_title",
    "seniority",
    "location",
    "work_arrangement",
    "required_skills",
    "required_skills_determined",
    "preferred_skills",
    "preferred_skills_determined",
)

REQUIRED_FIELDS = tuple(f for f in FIELDS if f != "source_url")

EXTRACTION_DEFAULTS = {
    "employer": UNKNOWN,
    "role_title": UNKNOWN,
    "seniority": UNKNOWN,
    "location": UNKNOWN,
    "work_arrangement": UNKNOWN,
    "required_skills": [],
    "required_skills_determined": False,
    "preferred_skills": [],
    "preferred_skills_determined": False,
}

_URL_PATTERN = re.compile(r"^https?://[^\s/?#]+[^\s]*$", re.IGNORECASE)


class RecordInvalid(Exception):
    """A candidate JobAd does not satisfy E-03. `fields` names what is at fault."""

    def __init__(self, message, fields):
        super().__init__(message)
        self.fields = tuple(fields)


def looks_like_url(value):
    """True for an http or https address. Deliberately narrow.

    S-01 rejects a submission whose kind is url and whose value is not a URL, so
    this predicate decides a rejection and is kept strict rather than generous.
    """
    return bool(isinstance(value, str) and _URL_PATTERN.match(value.strip()))


def digest(text):
    """The fingerprint E-03 names as source_text_digest.

    sha256 over the UTF-8 encoding of source_text, which is exactly what the
    R-120 acceptance command and INV-05 recompute. Any other encoding here would
    make the stored digest fail a check it is supposed to pass.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def advertisement_id(intake_kind, source_url, source_text):
    """A stable identifier derived from the submission.

    Content addressed, so the same posting submitted the same way twice lands on
    the same identifier rather than on two records. Kind and URL are part of the
    key, so the same text submitted by URL and by paste are two records, which is
    what R-119 requires to be possible.
    """
    material = "\x00".join([intake_kind, source_url or "", source_text])
    return "ad_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def build(intake_kind, source_text, ingested_at, source_url=None):
    """Assemble one E-03 record. Raises RecordInvalid rather than storing a wrong shape."""
    if intake_kind not in INTAKE_KINDS:
        raise RecordInvalid(
            "intake_kind must be one of " + ", ".join(INTAKE_KINDS), ["intake_kind"]
        )
    if not isinstance(source_text, str) or not source_text.strip():
        raise RecordInvalid("source_text absent or empty", ["source_text"])
    if intake_kind == "url" and not looks_like_url(source_url):
        raise RecordInvalid("intake_kind url requires a source_url", ["source_url"])
    if intake_kind == "pasted_text" and source_url:
        raise RecordInvalid(
            "source_url is present only when intake_kind is url", ["source_url"]
        )

    candidate = {
        "id": advertisement_id(intake_kind, source_url, source_text),
        "intake_kind": intake_kind,
        "source_text": source_text,
        "source_text_digest": digest(source_text),
        "ingested_at": ingested_at,
    }
    if intake_kind == "url":
        candidate["source_url"] = source_url
    candidate.update({k: _copy_default(v) for k, v in EXTRACTION_DEFAULTS.items()})
    problems = validate(candidate)
    if problems:
        raise RecordInvalid("invalid record: " + ", ".join(problems), problems)
    return candidate


def _copy_default(value):
    return list(value) if isinstance(value, list) else value


def validate(candidate):
    """Return the field names at fault, empty when the record satisfies E-03."""
    problems = []
    for field in REQUIRED_FIELDS:
        if field not in candidate:
            problems.append(field)
    if candidate.get("intake_kind") not in INTAKE_KINDS:
        problems.append("intake_kind")
    if candidate.get("work_arrangement") not in WORK_ARRANGEMENTS:
        problems.append("work_arrangement")

    # INV-04, enforced at write rather than audited afterwards.
    if (candidate.get("intake_kind") == "url") != bool(candidate.get("source_url")):
        problems.append("source_url")

    text = candidate.get("source_text")
    if not isinstance(text, str) or not text.strip():
        problems.append("source_text")
    elif candidate.get("source_text_digest") != digest(text):
        # INV-05. A record whose digest does not match its own text is refused at
        # the door, because once written it is indistinguishable from tampering.
        problems.append("source_text_digest")

    if not isinstance(candidate.get("required_skills"), list):
        problems.append("required_skills")
    if not isinstance(candidate.get("preferred_skills"), list):
        problems.append("preferred_skills")
    if not isinstance(candidate.get("required_skills_determined"), bool):
        problems.append("required_skills_determined")
    if not isinstance(candidate.get("preferred_skills_determined"), bool):
        problems.append("preferred_skills_determined")

    # Deduplicate while keeping the order they were found in.
    seen = []
    for field in problems:
        if field not in seen:
            seen.append(field)
    return seen
