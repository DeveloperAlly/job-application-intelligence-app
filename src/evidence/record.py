"""E-01 EvidenceRecord.

Written from pm/03-data-contract.md, entity E-01, and from nothing else. No schema,
model definition or code from resume-system, resume-editor-v0 or any predecessor copy
was opened for this module, per ADR-001.

E-01 has exactly six fields, all required, none with a default:

    id           string
    claim_text   string
    kind         enum(role, achievement, skill, education, metric, publication, other)
    source       string
    source_kind  enum(document, url, system_record, person_attestation, self_reported)
    date         timestamp

R-117 is the requirement that makes source and date mandatory. A record missing either
is not a deficient record, it is not a record at all, and this module refuses to build one.
"""

FIELDS = ("id", "claim_text", "kind", "source", "source_kind", "date")

REQUIRED_FIELDS = FIELDS

KINDS = (
    "role",
    "achievement",
    "skill",
    "education",
    "metric",
    "publication",
    "other",
)

SOURCE_KINDS = (
    "document",
    "url",
    "system_record",
    "person_attestation",
    "self_reported",
)


class RecordInvalid(Exception):
    """Raised when a candidate record does not conform to E-01.

    Carries the field names at fault so the caller can name them, which is what the
    S-04 seam requires of a rejection: the missing field is named, not merely counted.
    """

    def __init__(self, message, fields):
        super().__init__(message)
        self.fields = tuple(fields)


def _is_present(value):
    """A field is present when it is a string with at least one non-space character.

    R-117's own acceptance command tests `(r.get('source') or '').strip()`, so an empty
    string and a whitespace string are absences. This function is the same predicate,
    applied at write time instead of at audit time.
    """
    return isinstance(value, str) and value.strip() != ""


def validate(candidate):
    """Return the list of field names that make `candidate` non-conforming to E-01.

    An empty list means the candidate conforms. The list is ordered by FIELDS so that
    two runs over the same defect report it identically.
    """
    problems = []
    if not isinstance(candidate, dict):
        return ["record"]

    for field in FIELDS:
        if not _is_present(candidate.get(field)):
            problems.append(field)

    kind = candidate.get("kind")
    if _is_present(kind) and kind not in KINDS:
        problems.append("kind")

    source_kind = candidate.get("source_kind")
    if _is_present(source_kind) and source_kind not in SOURCE_KINDS:
        problems.append("source_kind")

    unknown = sorted(set(candidate) - set(FIELDS))
    problems.extend(unknown)

    return problems


def build(id, claim_text, kind, source, source_kind, date):
    """Build one E-01 record, or raise RecordInvalid naming every field at fault.

    There is no partial construction and no default. A caller that cannot supply a
    source or a date does not get a record with a placeholder in it, because a
    placeholder is the failure R-117 exists to prevent.
    """
    candidate = {
        "id": id,
        "claim_text": claim_text,
        "kind": kind,
        "source": source,
        "source_kind": source_kind,
        "date": date,
    }
    problems = validate(candidate)
    if problems:
        raise RecordInvalid(
            "record does not conform to E-01: " + ", ".join(problems), problems
        )
    return candidate
