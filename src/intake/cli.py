"""Command line entry to S-01, so that an ingest is a reproducible command.

    PYTHONPATH=src CAREER_OS_STORE=./store python3 -m intake.cli url <URL>
    PYTHONPATH=src CAREER_OS_STORE=./store python3 -m intake.cli paste --file <path>

Prints the receipt as JSON and exits 0 for stored or duplicate, 1 for rejected.
The pasted form reads the text from a file rather than an argument, because a
shell would mangle the byte exact text on the way in.
"""

import argparse
import json
import sys

from . import receive as receive_module
from .store import JobAdStore


def main(argv=None):
    parser = argparse.ArgumentParser(prog="intake.cli", description="S-01 advertisement intake")
    parser.add_argument("kind", choices=["url", "paste"])
    parser.add_argument("value", nargs="?", help="the URL, when kind is url")
    parser.add_argument("--file", help="path to the pasted text, when kind is paste")
    parser.add_argument(
        "--captured-at",
        default=None,
        help="when the caller obtained the advertisement, ISO 8601. Defaults to now",
    )
    parser.add_argument("--store", default=None, help="store root, else CAREER_OS_STORE, else ./store")
    args = parser.parse_args(argv)

    captured_at = args.captured_at or receive_module.utc_now()
    if args.kind == "url":
        source_kind, source_value = "url", args.value
    else:
        if not args.file:
            parser.error("paste requires --file")
        with open(args.file, "r", encoding="utf-8", newline="") as handle:
            source_value = handle.read()
        source_kind = "pasted_text"

    receipt = receive_module.receive(
        source_kind,
        source_value,
        captured_at,
        store=JobAdStore(args.store),
    )
    print(json.dumps(receipt.as_dict(), indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if receipt.intake_status == receive_module.REJECTED else 0


if __name__ == "__main__":
    sys.exit(main())
