"""Run S-02 over the advertisements in a store and report what was determined.

Usage:
    CAREER_OS_STORE=./store python3 src/extract/cli.py --apply
    CAREER_OS_STORE=./store python3 src/extract/cli.py --report

--report reads the store and prints what is already recorded. It writes nothing.
--apply runs extraction and writes the result back. Both print denominators, not
counts alone, because a count with no denominator cannot be read.
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extract import fields as fields_module  # noqa: E402
from extract.store import ExtractionStore  # noqa: E402


def _now():
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _summarise(record):
    scalars = fields_module.SCALAR_FIELDS
    unknown = [f for f in scalars if record.get(f) == fields_module.UNKNOWN]
    spans = record.get("extraction_spans") or {}
    anchored = sum(1 for f in scalars if spans.get(f))
    lists_determined = sum(
        1
        for f in ("required_skills", "preferred_skills")
        if record.get(f + "_determined")
    )
    return {
        "id": record.get("id"),
        "scalars_determined": str(len(scalars) - len(unknown)) + " of " + str(len(scalars)),
        "scalars_unknown": unknown,
        "scalars_with_span": str(anchored) + " of " + str(len(scalars) - len(unknown)),
        "skill_lists_determined": str(lists_determined) + " of 2",
        "required_skills": record.get("required_skills"),
        "preferred_skills": record.get("preferred_skills"),
        "extraction_status": record.get("extraction_status"),
        "injected_instruction_detected": record.get("injected_instruction_detected"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--store", default=None)
    args = parser.parse_args(argv)

    store = ExtractionStore(args.store)
    records = store.all_records()
    print("advertisements in store:", len(records))
    if not records:
        print("VACUOUS: no advertisements to extract from")
        return 1

    if args.apply:
        stamp = _now()
        for record in records:
            extraction = fields_module.extract(record.get("source_text"))
            if extraction.malformed is not None:
                print(record.get("id"), "not attempted:", extraction.malformed)
                continue
            store.apply(record.get("id"), extraction.as_record_fields(), stamp)
        records = store.all_records()

    for record in records:
        print(json.dumps(_summarise(record), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
