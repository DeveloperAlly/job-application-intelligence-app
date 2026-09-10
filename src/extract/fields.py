"""S-02 advertisement field extraction: the seven fields, span anchored.

R-120 names seven fields: employer, role title, seniority, location, work
arrangement, required skills and preferred skills. R-121 says that if extraction
cannot determine a field it must be marked unknown and must not be inferred.

The rule this module is built on, from which everything else follows:

    A value is emitted only when it can be sliced out of source_text by offset.
    Anything else is unknown.

That makes "did not infer" checkable rather than asserted, which is what S-02
means by returning a source_span for every field that is not unknown. Every
scalar except work_arrangement is stored as the exact substring it came from.
work_arrangement is the one field the data contract declares as an enum
(remote, hybrid, onsite, unknown), so the stored value is the enum token while
the span holds the posting's own wording that triggered it. That normalisation
is recorded on the span rather than left implicit.

No language model is called. That choice, and its failure modes, are stated in
the module docstring of vocabulary.py and in the task return. The relevant
consequence here is that the deterministic rules below fail by returning unknown
on a phrasing they do not cover, which is the behaviour R-121 asks for, and by
matching a pattern that is present but does not mean what the field means, which
is the deterministic form of the F-02 failure in pm/05-architecture.md.

Advertisement text is untrusted data. It is never an instruction. Regions that
address a model are quarantined by injection.py before any matching runs, and
the source text itself is left byte identical.
"""

import re

from . import injection as injection_module
from . import vocabulary as vocabulary_module

UNKNOWN = "unknown"

SCALAR_FIELDS = (
    "employer",
    "role_title",
    "seniority",
    "location",
    "work_arrangement",
)
LIST_FIELDS = ("required_skills", "preferred_skills")
FIELD_LIST = SCALAR_FIELDS + LIST_FIELDS

WORK_ARRANGEMENTS = ("remote", "hybrid", "onsite", "unknown")

RULES_VERSION = "career-os-extract-rules/1"

# The producer recorded in model_id. INV-22 of pm/03-data-contract.md requires a
# non-empty model_id on any advertisement carrying a recorded extraction, and
# R-137 requires the model that produced an output be recorded. No model produced
# this output, so the honest value names the deterministic producer instead of
# inventing a model name. The mismatch between that field's name and this value
# is reported as a finding rather than papered over.
PRODUCER_ID = "deterministic:career-os-extract-rules/1 (no language model called)"
EXTRACTION_METHOD = "deterministic_rules"

# ---------------------------------------------------------------------------
# scalar rules
# ---------------------------------------------------------------------------

_ROLE_OPENING = re.compile(
    r"\A\s{0,20}As\s+an?\s+"
    r"([A-Z][A-Za-z0-9/&+.\-]*"
    r"(?:[ ](?:of|and|for|to|the|[A-Z][A-Za-z0-9/&+.\-]*)){0,5}?)"
    r"\s*[,.]"
)
_ROLE_LABEL = re.compile(
    r"(?im)^[ \t]*(?:job[ \t]+)?(?:title|role|position)[ \t]*:[ \t]*(\S.*?)[ \t]*$"
)

_EMPLOYER_LABEL = re.compile(
    r"(?im)^[ \t]*(?:company|employer|organisation|organization)[ \t]*:[ \t]*(\S.*?)[ \t]*$"
)
_EMPLOYER_POSSESSIVE = re.compile(r"([A-Z][A-Za-z0-9&.\-]{1,40})['’]s\b")

# Words that take a possessive in ordinary posting prose and are never the
# employer. Without this the heuristic names the customer, the team or the day.
_EMPLOYER_STOPWORDS = frozenset(
    """
    the a an it its our your their his her this that these those today tomorrow
    yesterday company companies team teams client clients customer customers
    candidate candidates applicant applicants employee employees employer
    manager management prospect prospects user users partner partners
    engineer engineers developer developers world year years week weeks month
    months day days one another everyone someone people person role roles job
    jobs position positions product products business industry market
    """.split()
)

_SENIORITY_TOKENS = (
    "Distinguished",
    "Vice President",
    "Entry-level",
    "Entry level",
    "Mid-level",
    "Mid level",
    "Principal",
    "Associate",
    "Graduate",
    "Director",
    "Senior",
    "Junior",
    "Chief",
    "Staff",
    "Intern",
    "Head",
    "Lead",
    "VP",
)
_SENIORITY_LABEL = re.compile(
    r"(?im)^[ \t]*(?:seniority|level|grade)[ \t]*:[ \t]*(\S.*?)[ \t]*$"
)

_LOCATION_LABEL = re.compile(
    r"(?im)^[ \t]*(?:location|locations|office|based)[ \t]*:[ \t]*(\S.*?)[ \t]*$"
)
_LOCATION_BASED_IN = re.compile(
    r"(?i)\bbased\s+in\s+"
    r"([A-Z][A-Za-z.\-]+(?:[ ][A-Z][A-Za-z.\-]+){0,3}"
    r"(?:,\s*[A-Z][A-Za-z.\-]+(?:[ ][A-Z][A-Za-z.\-]+){0,2}){0,2})"
)

# Every trigger for each arrangement, so the stored enum token can always be
# traced back to a phrase that is actually in the posting.
_ARRANGEMENT_TRIGGERS = (
    (
        "remote",
        re.compile(
            r"(?i)\b(?:fully\s+remote|remote-first|remote|remotely|"
            r"work\s+from\s+home|WFH|fully\s+distributed)\b"
        ),
    ),
    ("hybrid", re.compile(r"(?i)\bhybrid\b")),
    (
        "onsite",
        re.compile(r"(?i)\b(?:on-?site|in-office|in\s+the\s+office)\b"),
    ),
)

# ---------------------------------------------------------------------------
# section rules
# ---------------------------------------------------------------------------


def _normalise_heading(line):
    stripped = line.strip().strip(":").strip()
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped.lower()


_REQUIRED_HEADINGS = frozenset(
    [
        "what you bring",
        "what you'll bring",
        "what you will bring",
        "what we're looking for",
        "what we are looking for",
        "requirements",
        "required",
        "required skills",
        "qualifications",
        "minimum qualifications",
        "basic qualifications",
        "who you are",
        "about you",
        "skills",
        "must have",
        "must haves",
        "you have",
        "your experience",
        "what you'll need",
        "what you will need",
    ]
)

_PREFERRED_HEADINGS = frozenset(
    [
        "nice to have",
        "nice to haves",
        "nice-to-have",
        "nice-to-haves",
        "preferred",
        "preferred qualifications",
        "preferred skills",
        "bonus",
        "bonus points",
        "good to have",
        "desirable",
        "pluses",
    ]
)

_PREFERRED_MARKERS = re.compile(
    r"(?i)\b(?:is\s+a\s+plus|are\s+a\s+plus|a\s+plus\b|nice\s+to\s+have|"
    r"bonus\s+points|is\s+preferred|preferred\b|desirable\b|"
    r"would\s+be\s+great|not\s+required)"
)

_BULLET = re.compile(r"^[ \t]*[-*•‣●]\s+")


class Section:
    def __init__(self, kind, name, start):
        self.kind = kind
        self.name = name
        self.start = start
        self.end = None


def _looks_like_heading(line):
    """A short standalone line that ends a section.

    Over-detection ends the requirements section early and loses terms, which is
    the conservative direction. Under-detection would run the section on into
    boilerplate, which is the direction that invents skills, so this predicate is
    deliberately generous about what counts as a heading.
    """
    stripped = line.strip()
    if not stripped or _BULLET.match(line):
        return False
    if len(stripped) > 60 or "," in stripped:
        return False
    if stripped[-1] in ".;:!?" and stripped[-1] != ":":
        return False
    words = [w for w in re.split(r"\s+", stripped.rstrip(":")) if w]
    if not words or len(words) > 6:
        return False
    return all(w[0].isupper() or not w[0].isalpha() for w in words)


def _line_offsets(text):
    offset = 0
    for line in text.split("\n"):
        yield offset, line
        offset += len(line) + 1


def sections(source_text):
    """The requirements-bearing sections of the posting, with their kinds."""
    found = []
    current = None
    for offset, line in _line_offsets(source_text):
        normalised = _normalise_heading(line)
        kind = None
        if normalised in _REQUIRED_HEADINGS:
            kind = "required"
        elif normalised in _PREFERRED_HEADINGS:
            kind = "preferred"
        is_heading = kind is not None or _looks_like_heading(line)
        if not is_heading:
            continue
        if current is not None:
            current.end = offset
            found.append(current)
            current = None
        if kind is not None:
            current = Section(kind, line.strip(), offset + len(line) + 1)
    if current is not None:
        current.end = len(source_text)
        found.append(current)
    return [s for s in found if s.kind in ("required", "preferred")]


def _units(text, section):
    """Bullets inside a section, or the whole body when it has none."""
    units = []
    open_unit = None
    for offset, line in _line_offsets(text):
        if offset < section.start:
            continue
        if offset >= section.end:
            break
        if _BULLET.match(line):
            if open_unit is not None:
                units.append(open_unit)
            open_unit = [offset, offset + len(line)]
            continue
        if not line.strip():
            if open_unit is not None:
                units.append(open_unit)
                open_unit = None
            continue
        if open_unit is not None:
            open_unit[1] = offset + len(line)
    if open_unit is not None:
        units.append(open_unit)
    if not units:
        units = [[section.start, section.end]]
    return units


# ---------------------------------------------------------------------------
# the extraction
# ---------------------------------------------------------------------------


class Extraction:
    """The S-02 output for one advertisement."""

    def __init__(self):
        self.values = {field: UNKNOWN for field in SCALAR_FIELDS}
        self.required_skills = []
        self.preferred_skills = []
        self.required_skills_determined = False
        self.preferred_skills_determined = False
        self.spans = {field: [] for field in FIELD_LIST}
        self.unknown_reasons = {}
        self.dropped_terms = []
        self.detections = []
        self.malformed = None
        self.raw_proposal = None
        # S-02 requires the record keep the difference between a field answered
        # with the unknown token and a field never answered at all, because the
        # two point at different fixes.
        self.unanswered_fields = []

    @property
    def status(self):
        if self.malformed is not None:
            return "not_attempted"
        complete = all(self.values[f] != UNKNOWN for f in SCALAR_FIELDS)
        complete = (
            complete
            and self.required_skills_determined
            and self.preferred_skills_determined
        )
        return "complete" if complete else "partial"

    def as_record_fields(self):
        """Exactly the keys this extraction contributes to an E-03 record."""
        return {
            "employer": self.values["employer"],
            "role_title": self.values["role_title"],
            "seniority": self.values["seniority"],
            "location": self.values["location"],
            "work_arrangement": self.values["work_arrangement"],
            "required_skills": list(self.required_skills),
            "required_skills_determined": self.required_skills_determined,
            "preferred_skills": list(self.preferred_skills),
            "preferred_skills_determined": self.preferred_skills_determined,
            "model_id": PRODUCER_ID,
            "extraction_method": EXTRACTION_METHOD,
            "extraction_rules_version": RULES_VERSION,
            "extraction_status": self.status,
            "extraction_spans": {k: list(v) for k, v in self.spans.items()},
            "extraction_unknown_reasons": dict(self.unknown_reasons),
            "extraction_unanswered_fields": list(self.unanswered_fields),
            "dropped_terms": list(self.dropped_terms),
            "injected_instruction_detected": bool(self.detections),
            "injected_instruction_spans": [
                d.as_record() for d in self.detections
            ],
        }


def _span(source_text, start, end, rule_id, note=None):
    span = {
        "start": start,
        "end": end,
        "text": source_text[start:end],
        "rule_id": rule_id,
    }
    if note:
        span["note"] = note
    return span


def _set_scalar(extraction, source_text, field, start, end, rule_id):
    extraction.values[field] = source_text[start:end]
    extraction.spans[field] = [_span(source_text, start, end, rule_id)]


def _role_title(extraction, source_text, masked):
    match = _ROLE_LABEL.search(masked)
    if match:
        _set_scalar(
            extraction, source_text, "role_title", match.start(1), match.end(1),
            "RULE-ROLE-02 labelled title field",
        )
        return
    match = _ROLE_OPENING.match(masked)
    if match:
        _set_scalar(
            extraction, source_text, "role_title", match.start(1), match.end(1),
            "RULE-ROLE-01 opening 'As a <title>,' clause",
        )
        return
    extraction.unknown_reasons["role_title"] = (
        "no labelled title field and no opening 'As a <title>,' clause; "
        "no other pattern is trusted to name the role without inferring it"
    )


def _employer(extraction, source_text, masked):
    match = _EMPLOYER_LABEL.search(masked)
    if match:
        _set_scalar(
            extraction, source_text, "employer", match.start(1), match.end(1),
            "RULE-EMP-02 labelled company field",
        )
        return

    counts = {}
    first = {}
    for match in _EMPLOYER_POSSESSIVE.finditer(masked):
        name = match.group(1)
        if name.lower() in _EMPLOYER_STOPWORDS:
            continue
        counts.setdefault(name, 0)
        first.setdefault(name, (match.start(1), match.end(1)))
    if counts:
        for name in list(counts):
            counts[name] = len(
                re.findall(r"\b" + re.escape(name) + r"\b", masked)
            )
        ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
        best, best_count = ranked[0]
        tied = len(ranked) > 1 and ranked[1][1] == best_count
        if best_count >= 2 and not tied:
            start, end = first[best]
            _set_scalar(
                extraction, source_text, "employer", start, end,
                "RULE-EMP-01 possessive name occurring "
                + str(best_count)
                + " times",
            )
            return
        if tied:
            extraction.unknown_reasons["employer"] = (
                "two or more possessive names tie at "
                + str(best_count)
                + " occurrences, so choosing one would be a guess"
            )
            return
        extraction.unknown_reasons["employer"] = (
            "the only possessive name occurs once, which is too weak to "
            "distinguish the employer from a customer or a product mentioned "
            "in passing"
        )
        return
    extraction.unknown_reasons["employer"] = (
        "no labelled company field and no possessive company name in the text"
    )


def _seniority(extraction, source_text, masked):
    match = _SENIORITY_LABEL.search(masked)
    if match:
        _set_scalar(
            extraction, source_text, "seniority", match.start(1), match.end(1),
            "RULE-SEN-02 labelled seniority field",
        )
        return

    title_spans = extraction.spans.get("role_title") or []
    if not title_spans:
        extraction.unknown_reasons["seniority"] = (
            "the role title is unknown, and a seniority token is only trusted "
            "where it sits against the title; a token found elsewhere in the "
            "posting is as likely to be a verb, as 'Lead' is in 'Lead technical "
            "discovery calls'"
        )
        return

    span = title_spans[0]
    title = span["text"]
    for token in _SENIORITY_TOKENS:
        if title.lower().startswith(token.lower() + " "):
            _set_scalar(
                extraction, source_text, "seniority",
                span["start"], span["start"] + len(token),
                "RULE-SEN-01 seniority token leading the role title",
            )
            return

    line_start = masked.rfind("\n", 0, span["start"]) + 1
    before = masked[line_start:span["start"]]
    for token in _SENIORITY_TOKENS:
        pattern = re.compile(r"(?i)(?:^|\W)(" + re.escape(token) + r")\s+$")
        found = pattern.search(before)
        if found:
            start = line_start + found.start(1)
            _set_scalar(
                extraction, source_text, "seniority", start, start + len(token),
                "RULE-SEN-01 seniority token immediately preceding the role title",
            )
            return

    extraction.unknown_reasons["seniority"] = (
        "no labelled seniority field, and no seniority token sits against the "
        "role title; a token elsewhere in the posting is not evidence of the "
        "level of this role"
    )


def _location(extraction, source_text, masked):
    match = _LOCATION_LABEL.search(masked)
    if match:
        _set_scalar(
            extraction, source_text, "location", match.start(1), match.end(1),
            "RULE-LOC-01 labelled location field",
        )
        return
    match = _LOCATION_BASED_IN.search(masked)
    if match:
        _set_scalar(
            extraction, source_text, "location", match.start(1), match.end(1),
            "RULE-LOC-02 'based in <place>' clause",
        )
        return
    extraction.unknown_reasons["location"] = (
        "no labelled location field and no 'based in <place>' clause; place "
        "names are not guessed from the rest of the text"
    )


def _work_arrangement(extraction, source_text, masked):
    hits = []
    for value, pattern in _ARRANGEMENT_TRIGGERS:
        match = pattern.search(masked)
        if match:
            hits.append((value, match.start(), match.end()))
    if len(hits) == 1:
        value, start, end = hits[0]
        extraction.values["work_arrangement"] = value
        extraction.spans["work_arrangement"] = [
            _span(
                source_text, start, end,
                "RULE-ARR-01 arrangement trigger phrase",
                "stored value is the E-03 enum token '"
                + value
                + "'; the span is the posting's own wording that triggered it",
            )
        ]
        return
    if len(hits) > 1:
        for value, start, end in hits:
            extraction.dropped_terms.append(
                {
                    "term": source_text[start:end],
                    "proposed_for": "work_arrangement",
                    "reason": "two or more arrangements are named in the same "
                    "posting, so no single one is determined",
                }
            )
        extraction.unknown_reasons["work_arrangement"] = (
            "the posting names " + str(len(hits)) + " different arrangements"
        )
        return
    extraction.unknown_reasons["work_arrangement"] = (
        "the posting names none of the remote, hybrid or onsite trigger phrases"
    )


def _skills(extraction, source_text, masked):
    found = sections(masked)
    if not found:
        extraction.unknown_reasons["required_skills"] = (
            "no requirements section heading was found, so there is nothing to "
            "read requirements out of"
        )
        extraction.unknown_reasons["preferred_skills"] = (
            extraction.unknown_reasons["required_skills"]
        )
        return

    buckets = {"required": [], "preferred": []}
    seen = set()
    for section in found:
        for start, end in _units(masked, section):
            unit_text = masked[start:end]
            if not unit_text.strip():
                continue
            bucket = section.kind
            if bucket == "required" and _PREFERRED_MARKERS.search(unit_text):
                bucket = "preferred"
            for hit in vocabulary_module.find(masked, start, end, source_text):
                key = hit["term"].lower()
                if key in seen:
                    continue
                seen.add(key)
                buckets[bucket].append(hit)

    for bucket, field in (
        ("required", "required_skills"),
        ("preferred", "preferred_skills"),
    ):
        hits = buckets[bucket]
        terms = [hit["term"] for hit in hits]
        spans = [
            _span(
                source_text, hit["start"], hit["end"],
                "RULE-SKILL-01 vocabulary entry '"
                + hit["vocabulary_entry"]
                + "' inside a "
                + bucket
                + " section unit",
            )
            for hit in hits
        ]
        setattr(extraction, field, terms)
        extraction.spans[field] = spans
        setattr(extraction, field + "_determined", bool(terms))
        if not terms:
            extraction.unknown_reasons[field] = (
                "a requirements section was found but no vocabulary term "
                "occurs in its "
                + bucket
                + " units; an empty list is not claimed as determined, because "
                "this extractor cannot tell a posting that lists no "
                + bucket
                + " skills from one whose wording it does not cover"
            )


def extract(source_text):
    """Run S-02 over one advertisement's source text.

    `source_text` is untrusted data. It is read, matched against and quoted from.
    It is never followed and never modified.
    """
    extraction = Extraction()
    if not isinstance(source_text, str) or not source_text.strip():
        extraction.malformed = "source_text absent or empty"
        for field in FIELD_LIST:
            extraction.unknown_reasons[field] = (
                "no source text, so no field can be anchored to a span"
            )
        return extraction

    extraction.detections = injection_module.detect(source_text)
    masked = injection_module.mask(source_text, extraction.detections)

    _role_title(extraction, source_text, masked)
    _employer(extraction, source_text, masked)
    _seniority(extraction, source_text, masked)
    _location(extraction, source_text, masked)
    _work_arrangement(extraction, source_text, masked)
    _skills(extraction, source_text, masked)

    _enforce_traceability(extraction, source_text)
    return extraction


def ingest_proposal(proposal, source_text, unknown_token=UNKNOWN):
    """Anchor a proposed extraction from any producer against the source text.

    S-02 is a prompt boundary and says the thing on the other side "can return
    anything". The deterministic rules above are one producer. A model behind
    C-03 would be another. Both hand their answer through here, so the error
    cases S-02 lists have exactly one implementation and are reachable from a
    test rather than described in a comment.

    `proposal` is the producer's answer: a mapping of field name to a value or
    the unknown token, with skill fields carrying lists. Anything else is a
    malformed response, which is recorded rather than partially believed.
    """
    extraction = Extraction()
    if not isinstance(source_text, str) or not source_text.strip():
        extraction.malformed = "source_text absent or empty"
        extraction.raw_proposal = proposal
        return extraction
    if not isinstance(proposal, dict):
        extraction.malformed = (
            "the response is not an object carrying one entry per field"
        )
        extraction.raw_proposal = proposal
        return extraction

    extraction.detections = injection_module.detect(source_text)

    for field in SCALAR_FIELDS:
        if field not in proposal:
            extraction.unanswered_fields.append(field)
            extraction.unknown_reasons[field] = (
                "the producer did not answer this field at all, which is not the "
                "same as answering it unknown"
            )
            continue
        value = proposal[field]
        if value is None or value == unknown_token:
            extraction.unknown_reasons[field] = (
                "the producer answered with the unknown token"
            )
            continue
        if not isinstance(value, str):
            extraction.dropped_terms.append(
                {
                    "term": repr(value),
                    "proposed_for": field,
                    "reason": "the proposed value is not text",
                }
            )
            extraction.unknown_reasons[field] = "the proposed value is not text"
            continue
        located = _locate(source_text, value, field)
        if located is None:
            extraction.dropped_terms.append(
                {
                    "term": value,
                    "proposed_for": field,
                    "reason": "the proposed value cannot be located in "
                    "source_text, so it is an inference and R-121 forbids it",
                }
            )
            extraction.unknown_reasons[field] = (
                "a proposed value was refused because it does not occur in "
                "source_text"
            )
            continue
        start, end = located
        if field == "work_arrangement":
            extraction.values[field] = value
            extraction.spans[field] = [
                _span(
                    source_text, start, end,
                    "PROPOSAL anchored to an arrangement trigger phrase",
                    "stored value is the E-03 enum token '" + value + "'",
                )
            ]
        else:
            _set_scalar(
                extraction, source_text, field, start, end,
                "PROPOSAL anchored verbatim in source_text",
            )

    for field in LIST_FIELDS:
        if field not in proposal:
            extraction.unanswered_fields.append(field)
            extraction.unknown_reasons[field] = (
                "the producer did not answer this field at all"
            )
            continue
        terms = proposal[field]
        if not isinstance(terms, (list, tuple)):
            extraction.unknown_reasons[field] = "the proposed value is not a list"
            continue
        kept = []
        spans = []
        for term in terms:
            located = _locate(source_text, term, field) if isinstance(term, str) else None
            if located is None:
                extraction.dropped_terms.append(
                    {
                        "term": term if isinstance(term, str) else repr(term),
                        "proposed_for": field,
                        "reason": "the term does not occur in source_text, so it "
                        "was paraphrased or invented rather than extracted",
                    }
                )
                continue
            start, end = located
            kept.append(source_text[start:end])
            spans.append(
                _span(
                    source_text, start, end,
                    "PROPOSAL anchored verbatim in source_text",
                )
            )
        setattr(extraction, field, kept)
        extraction.spans[field] = spans
        setattr(extraction, field + "_determined", bool(kept))
        if not kept:
            extraction.unknown_reasons[field] = (
                "no proposed term for this field could be located in source_text"
            )

    _enforce_traceability(extraction, source_text)
    return extraction


def _locate(source_text, value, field):
    """The offsets of `value` in `source_text`, case sensitive first.

    Returns None when the value does not occur, which is what forces the field
    to unknown. For work_arrangement the value is an enum token that need not
    appear in the posting at all, so what is located is a trigger phrase for that
    token instead.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    if field == "work_arrangement":
        triggers = dict(_ARRANGEMENT_TRIGGERS)
        if value not in triggers:
            return None
        match = triggers[value].search(source_text)
        return (match.start(), match.end()) if match else None
    index = source_text.find(value)
    if index >= 0:
        return index, index + len(value)
    index = source_text.lower().find(value.lower())
    if index >= 0:
        return index, index + len(value)
    return None


def _enforce_traceability(extraction, source_text):
    """The last gate before anything leaves this module.

    Every value is re-checked against the source text it claims to come from. A
    value whose span does not reproduce it is dropped and the field is forced to
    unknown, so a rule that goes wrong produces a dropped term rather than a
    fabricated field. This is the S-02 error case for a value that cannot be
    located in source_text, applied to this module's own output rather than only
    to a model's.
    """
    for field in SCALAR_FIELDS:
        value = extraction.values[field]
        if value == UNKNOWN:
            extraction.spans[field] = []
            continue
        spans = extraction.spans.get(field) or []
        ok = bool(spans)
        for span in spans:
            if source_text[span["start"]:span["end"]] != span["text"]:
                ok = False
            elif field == "work_arrangement":
                triggers = dict(_ARRANGEMENT_TRIGGERS)
                if value not in triggers or not triggers[value].fullmatch(
                    span["text"]
                ):
                    ok = False
            elif span["text"] != value:
                ok = False
        if not ok:
            extraction.dropped_terms.append(
                {
                    "term": value,
                    "proposed_for": field,
                    "reason": "the value could not be reproduced from its own "
                    "span of source_text, so it is treated as inferred",
                }
            )
            extraction.values[field] = UNKNOWN
            extraction.spans[field] = []
            extraction.unknown_reasons[field] = (
                "a candidate value was rejected because it could not be "
                "located verbatim in source_text"
            )

    for field in LIST_FIELDS:
        terms = list(getattr(extraction, field))
        spans = list(extraction.spans.get(field) or [])
        kept_terms = []
        kept_spans = []
        for term, span in zip(terms, spans):
            if (
                source_text[span["start"]:span["end"]] == term
                and term.lower() in source_text.lower()
            ):
                kept_terms.append(term)
                kept_spans.append(span)
                continue
            extraction.dropped_terms.append(
                {
                    "term": term,
                    "proposed_for": field,
                    "reason": "the term does not occur at the span it claims, "
                    "so it is treated as inferred rather than extracted",
                }
            )
        setattr(extraction, field, kept_terms)
        extraction.spans[field] = kept_spans
        setattr(extraction, field + "_determined", bool(kept_terms))
