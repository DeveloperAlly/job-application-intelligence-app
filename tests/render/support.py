"""Fixture loading and temporary stores for the render tests. Serves R-127.

INVENTED TEST DATA. Every person, employer, product, URL and number in
tests/render/fixtures/ is a placeholder created for this suite: Wren Halloway, Nimbus
Clearing, Thornfield Systems, Ardley Robotics, Perrin Laboratories and the rest. Nothing
here reads store/evidence/, which holds the owner's real career history and is outside
this lane entirely.

Why fixtures exist at all. The composing seams S-06 and S-07 have not been built, so no
composed document exists to render. The fixtures are contract conformant E-08
GeneratedDocument records so that the renderer can be exercised end to end today against
the shape the composers will have to produce. They deliberately do NOT live in
store/documents/: that collection belongs to the composer tasks, and a fixture written
there would make their acceptance commands report documents that nobody composed.

Every test builds its own temporary store. A test that writes into ./store is a defect,
and tests/render/test_no_store_mutation.py checks that it did not happen.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.join(HERE, "fixtures")
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.render.style import VisualStyle, StyleStore, default_style  # noqa: E402


def load_fixture(name):
    with open(os.path.join(FIXTURE_DIR, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def resume_document():
    """The E-08 resume fixture, as stored."""
    return load_fixture("doc_fixture_resume.json")


def cover_letter_document():
    return load_fixture("doc_fixture_cover_letter.json")


def resume_blocks():
    """The explicit block form of the same content, which is what a composer should emit."""
    return {"blocks": load_fixture("doc_fixture_resume.blocks.json")["blocks"]}


def cover_letter_blocks():
    return {"blocks": load_fixture("doc_fixture_cover_letter.blocks.json")["blocks"]}


class TemporaryStore:
    """A store root in a temporary directory, with styles written into it.

    `approved` decides whether the default style is written with approved true. In the
    repository store it is never true, because approval is the owner's act. In a
    temporary store a test may set it in order to exercise the path beyond the refusal,
    and that is the only place in this codebase where an approved style exists.
    """

    def __init__(self, approved=True, extra_styles=()):
        self.approved = approved
        self.extra_styles = list(extra_styles)
        self._temp = None
        self.root = None

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(prefix="career-os-render-test-")
        self.root = self._temp.name
        styles = StyleStore(self.root)
        styles.write(default_style(approved=self.approved))
        for style in self.extra_styles:
            styles.write(style)
        return self

    def __exit__(self, *exc):
        self._temp.cleanup()
        return False

    def styles(self):
        return StyleStore(self.root)


__all__ = [
    "FIXTURE_DIR",
    "REPO_ROOT",
    "StyleStore",
    "TemporaryStore",
    "VisualStyle",
    "cover_letter_blocks",
    "cover_letter_document",
    "default_style",
    "load_fixture",
    "resume_blocks",
    "resume_document",
]
