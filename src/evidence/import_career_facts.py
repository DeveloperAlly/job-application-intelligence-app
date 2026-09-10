"""Import the owner's career facts into the evidence store as E-01 records.

ADR-001 puts career facts on the reuse allowlist and every line of resume-system's code,
schema and layout on the denylist. The only file this module opens from that estate is the
JSON data file named on the command line. Nothing about the shape below is copied from
resume-system's schema. The target shape is E-01 in pm/03-data-contract.md and it is
written from that document.

R-117 makes source and date mandatory. Two rules follow, and they are the substance of
this module rather than a detail of it:

  1. A fact with no defensible source is not imported. A defensible source is a real
     artefact outside the record itself. The bank's own provenance legend, read at
     resume-system/docs/m11/architecture/DATA_MODEL.md lines 195 to 208, distinguishes
     these from the two circular tokens: `base_json`, which is the resume file itself,
     and `app_n8n` / `app_nvidia`, which are application documents produced from this
     same bank. Citing either answers the question "was it in the resume" and not the
     question "where did the fact come from", which is exactly the substitution R-117
     forbids. This is the same class of defect R-140 names, one system removed.

  2. A fact with no defensible date is not imported. A date is not invented, not guessed,
     and not back-filled from the bank's own compilation date. Precision is never added:
     a source that says "2024" yields the ISO 8601 reduced-precision date "2024", not a
     fabricated January the first.

Rejections are reported, never silently dropped, because the owner can supply a missing
source or date in two minutes and this program cannot supply either at all.
"""

import argparse
import json
import os
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from evidence.store import EvidenceStore
    from evidence import record as record_module
else:
    from .store import EvidenceStore
    from . import record as record_module


# Provenance legend, transcribed from resume-system/docs/m11/architecture/DATA_MODEL.md
# lines 199 to 207. Each entry resolves a bank token to the artefact it names and to the
# E-01 source_kind that artefact is.
DEFENSIBLE_SOURCES = {
    "cv2022": ("document", "self-written 2022 CV"),
    "n8nv4": ("document", "detailed GitHub resume (n8n variant)"),
    "nvidia": ("document", "detailed GitHub resume (NVIDIA variant)"),
    "base": ("document", "campaign_career_relaunch/resume_n8n_devrel.md"),
    "bank_md": ("document", "content/master_achievement_bank.md"),
    "mem": ("system_record", "AI-Ally work records, Jun 2026 (Livepeer docs sessions)"),
    "verified_by_ally": (
        "person_attestation",
        "explicit Ally sign-off recorded in a decision file",
    ),
}

# Tokens that do not answer where the fact came from. Listing them is the whole point:
# a silent acceptance here is a lie on a resume with a provenance trail that loops.
NON_DEFENSIBLE_SOURCES = {
    "base_json": "the resume base file itself, so the citation is circular",
    "app_n8n": "an application document generated from this same bank, so the citation is circular",
    "app_nvidia": "an application document generated from this same bank, so the citation is circular",
    "flagged_unverified": "the bank's own marker for a provenance gap",
}

# person_attestation outranks a document, a document outranks a derived system record.
SOURCE_KIND_PRECEDENCE = ("person_attestation", "document", "system_record")

SECTION_KIND = {
    "experience": "role",
    "education": "education",
    "skills": "skill",
    "recognition": "achievement",
    "highlights": "achievement",
    "research": "publication",
    "talks": "other",
    "hosting": "other",
    "projects": "other",
    "n8nWorkflows": "other",
}

MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}

YEAR = r"(?:19|20)[0-9]{2}"
MONTH_YEAR_RE = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(" + YEAR + r")\b")
YEAR_RE = re.compile(r"\b(" + YEAR + r")\b")
TRAILING_YEAR_RE = re.compile(r",\s*(" + YEAR + r")\s*$")

# Per-record date rulings. Each names the flag in the owner's own bank that makes the
# date indefensible. These are not judgements invented here, they are her recorded
# open questions, honoured rather than overridden.
DATE_NOT_DEFENSIBLE = {
    "edu_anu_ppa": (
        "bank flag anu_dates_unverified: the date range appears only in the AI-era files "
        "and the 2022 CV lists no dates for it, marked confirm with Ally"
    ),
    "talk_smartcon_barcelona": (
        "bank flag year_conflict: the year carried on the record comes only from base_json, "
        "which is not a defensible source, and the defensible source bank_md gives a different year"
    ),
}

STATUS_BLOCKS_IMPORT = "excluded_until_verified"


class Rejection(object):
    def __init__(self, section, fact_id, missing, detail):
        self.section = section
        self.fact_id = fact_id
        self.missing = missing
        self.detail = detail

    def as_row(self):
        return {
            "section": self.section,
            "id": self.fact_id,
            "missing": self.missing,
            "detail": self.detail,
        }


def resolve_source(tokens):
    """Return (source_string, source_kind) or (None, None) when nothing defensible remains."""
    kept = [t for t in tokens if t in DEFENSIBLE_SOURCES]
    if not kept:
        return None, None
    descriptions = []
    kinds = set()
    for token in kept:
        kind, description = DEFENSIBLE_SOURCES[token]
        kinds.add(kind)
        if description not in descriptions:
            descriptions.append(description)
    for candidate in SOURCE_KIND_PRECEDENCE:
        if candidate in kinds:
            source_kind = candidate
            break
    else:
        source_kind = "self_reported"
    return "; ".join(descriptions), source_kind


def parse_date(text):
    """Return an ISO 8601 date at exactly the precision the text states, or None.

    "Nov 2025 - Present" gives "2025-11". "2012 - 2017" gives "2012". "2024" gives "2024".
    No month is added to a bare year and no day is added to anything, because added
    precision is invented content.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    month_match = MONTH_YEAR_RE.search(text)
    year_match = YEAR_RE.search(text)
    if month_match and (
        not year_match or month_match.start(2) <= year_match.start(1)
    ):
        month = MONTHS.get(month_match.group(1)[:3].lower())
        if month:
            return month_match.group(2) + "-" + month
    if year_match:
        return year_match.group(1)
    return None


def parse_trailing_year(text):
    """Return the year when the text ends in ", YYYY", else None.

    Used for the recognition section, whose entries carry no date field and state their
    date as a trailing token on the claim itself. Anything looser would harvest a year
    that the sentence merely mentions.
    """
    if not isinstance(text, str):
        return None
    match = TRAILING_YEAR_RE.search(text.strip())
    return match.group(1) if match else None


def join_parts(parts):
    """Join the owner's own strings with punctuation and nothing else.

    No connective word is added anywhere in this module. Every substantive token in a
    claim_text came out of her file.
    """
    cleaned = []
    for part in parts:
        if not isinstance(part, str):
            continue
        part = part.strip()
        if not part:
            continue
        cleaned.append(part if part.endswith((".", "!", "?")) else part + ".")
    return " ".join(cleaned)


def claim_text_for(section, item):
    if section == "experience":
        head = ", ".join(
            p for p in (item.get("role"), item.get("org"), item.get("dates")) if p
        )
        return join_parts([head, item.get("lede")] + list(item.get("bullets") or []))
    if section == "education":
        head = ", ".join(
            p for p in (item.get("degree"), item.get("org"), item.get("dates")) if p
        )
        return join_parts([head, item.get("note")])
    if section == "recognition":
        return join_parts([item.get("text")])
    if section in ("research", "talks"):
        head = ", ".join(
            p for p in (item.get("type"), item.get("venue"), item.get("year")) if p
        )
        return join_parts([item.get("topic"), head])
    if section == "hosting":
        head = ", ".join(
            p
            for p in (item.get("name"), item.get("type"), item.get("meta"), item.get("year"))
            if p
        )
        return join_parts([head])
    if section in ("projects", "n8nWorkflows"):
        return join_parts([item.get("name"), item.get("meta"), item.get("body")])
    if section == "skills":
        return join_parts([item.get("label"), item.get("items")])
    if section == "highlights":
        return join_parts([item.get("title"), item.get("body")])
    return ""


def date_for(section, item):
    if section == "recognition":
        return parse_trailing_year(item.get("text"))
    if section in ("experience", "education"):
        return parse_date(item.get("dates"))
    if section in ("research", "talks", "hosting"):
        return parse_date(item.get("year"))
    if section in ("projects", "n8nWorkflows"):
        return parse_date(item.get("meta"))
    return None


def assess(section, item):
    """Return (record_or_None, rejection_or_None) for one fact."""
    fact_id = item.get("id")
    if not fact_id:
        return None, Rejection(section, "(no id)", ["id"], "the fact carries no identifier")

    if item.get("status") == STATUS_BLOCKS_IMPORT:
        return None, Rejection(
            section,
            fact_id,
            ["verified source"],
            "the owner's bank marks this status excluded_until_verified, a declared provenance gap",
        )

    missing = []
    details = []

    source, source_kind = resolve_source(item.get("source") or [])
    if source is None:
        missing.append("source")
        offending = sorted(set(item.get("source") or []) & set(NON_DEFENSIBLE_SOURCES))
        if offending:
            details.append(
                "every source token is non-defensible: "
                + ", ".join(t + " (" + NON_DEFENSIBLE_SOURCES[t] + ")" for t in offending)
            )
        else:
            details.append("no source token at all")

    if fact_id in DATE_NOT_DEFENSIBLE:
        missing.append("date")
        details.append(DATE_NOT_DEFENSIBLE[fact_id])
    else:
        date = date_for(section, item)
        if date is None:
            missing.append("date")
            details.append(
                "no date field on this fact and none stated in its own text, so any date would be invented"
            )

    claim_text = claim_text_for(section, item)
    if not claim_text.strip():
        missing.append("claim_text")
        details.append("the fact carries no text to assert")

    if missing:
        return None, Rejection(section, fact_id, missing, "; ".join(details))

    built = record_module.build(
        id=fact_id,
        claim_text=claim_text,
        kind=SECTION_KIND[section],
        source=source,
        source_kind=source_kind,
        date=date_for(section, item),
    )
    return built, None


def run(source_path, store_root, apply_changes):
    with open(source_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    store = EvidenceStore(store_root)
    imported = []
    rejected = []
    available = 0

    for section in SECTION_KIND:
        for item in data.get(section) or []:
            available += 1
            built, rejection = assess(section, item)
            if rejection is not None:
                rejected.append(rejection)
                continue
            if apply_changes:
                store.write(built, overwrite=True)
            imported.append(built["id"])

    # Entries in the file that are not facts about the owner's history, counted so the
    # denominator is the whole file and not the part that happened to work.
    non_record = []
    for section in ("contact",):
        for index, item in enumerate(data.get(section) or []):
            available += 1
            non_record.append(
                Rejection(
                    section,
                    section + "[" + str(index) + "]",
                    ["id", "source", "date"],
                    "contact detail, carries no identifier, no source and no date, and is not a claim about history",
                )
            )
    rejected.extend(non_record)

    return {
        "available": available,
        "imported": sorted(imported),
        "rejected": [r.as_row() for r in rejected],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="path to the owner's career facts JSON")
    parser.add_argument("--store", default=None, help="store root, default CAREER_OS_STORE or ./store")
    parser.add_argument("--apply", action="store_true", help="write records, otherwise report only")
    args = parser.parse_args(argv)

    result = run(args.source, args.store, args.apply)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
