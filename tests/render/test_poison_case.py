"""The poison case: the R-127 gate must go red when a rendered document cites an
unapproved style, and must come back green on an exact restore.

A gate that has only ever been seen green is not evidence. This file runs the real
acceptance command out of pm/03-requirements.md, and the real INV-13 command out of
pm/03-data-contract.md, against a store that is first compliant, then deliberately
poisoned, then restored, and asserts the exit code and the named document at each step.

The store here is a temporary one. This lane owns store/visual_styles/ and does not own
store/documents/, which belongs to the composer tasks, so the poison cannot be planted in
the repository store without polluting a collection that is not this lane's to write. The
temporary store is built to the same shape the repository store will have once the
composers run: the same collection names, the same E-05 and E-08 field sets, and the same
CAREER_OS_STORE resolution.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

from support import (
    REPO_ROOT,
    cover_letter_blocks,
    cover_letter_document,
    resume_blocks,
    resume_document,
)

from src.render.render import render
from src.render.style import CAREER_OS_DEFAULT_ID, StyleStore, default_style

REQUIREMENTS = os.path.join(REPO_ROOT, "pm", "03-requirements.md")
DATA_CONTRACT = os.path.join(REPO_ROOT, "pm", "03-data-contract.md")
UNAPPROVED_STYLE_ID = "vs_poisoned_not_approved"


def acceptance_command(path, row_id):
    """Pull a row's command out of a register table, the way the done command does.

    Escaped pipes inside a cell are protected before the row is split on the column
    separator, so a command containing a pipe survives extraction intact. The command
    column differs between the two registers, R-127 being the fifth cell and INV-13 the
    fourth, so the cell is found by looking for the backticked python3 command rather than
    by a hardcoded index that would silently read the wrong column.
    """
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()
    matching = [line for line in lines if line.startswith("| " + row_id + " ")]
    assert matching, "no row %r in %s" % (row_id, path)
    for cell in matching[0].replace("\\|", "\0").split("|"):
        found = re.search("`(python3 .+?)`", cell.strip().replace("\0", "|"), re.S)
        if found:
            return found.group(1)
    raise AssertionError("no python3 command in row %r of %s" % (row_id, path))


def run(command, store):
    environment = dict(os.environ, CAREER_OS_STORE=store)
    completed = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, env=environment
    )
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def digest_tree(root):
    entries = {}
    for directory, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(directory, name)
            with open(path, "rb") as handle:
                entries[os.path.relpath(path, root)] = hashlib.sha256(handle.read()).hexdigest()
    return entries


def build_compliant_store(root):
    """A store in the state the R-127 command is written to pass over.

    An approved style exists here and nowhere else. Approval is the owner's act, so the
    repository store carries the same style with approved false.
    """
    StyleStore(root).write(default_style(approved=True))
    written = {}
    for document, content in (
        (resume_document(), resume_blocks()),
        (cover_letter_document(), cover_letter_blocks()),
    ):
        result = render(
            content,
            CAREER_OS_DEFAULT_ID,
            document["document_kind"],
            store=root,
            document_id=document["id"],
            revision=document["revision"],
            write_file=True,
        )
        document.update(result.document_fields)
        path = os.path.join(root, "documents", document["id"] + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        written[document["id"]] = path
    return written


class PoisonCase(unittest.TestCase):
    def test_gate_green_then_red_on_an_unapproved_style_then_green_on_restore(self):
        r127 = acceptance_command(REQUIREMENTS, "R-127")
        inv13 = acceptance_command(DATA_CONTRACT, "INV-13")

        with tempfile.TemporaryDirectory(prefix="career-os-poison-") as root:
            documents = build_compliant_store(root)
            target = documents["doc_fixture_resume"]

            code, output = run(r127, root)
            self.assertEqual(code, 0, "R-127 should be green on a compliant store: %s" % output)
            self.assertIn("2 of 2 rendered documents", output)
            self.assertIn("2 of 2 document kinds", output)
            self.assertEqual(run(inv13, root)[0], 0)

            before_tree = digest_tree(root)
            with open(target, "rb") as handle:
                before_bytes = handle.read()

            # poison: point one rendered document at a style that is not approved
            poisoned = json.loads(before_bytes.decode("utf-8"))
            poisoned["visual_style_id"] = UNAPPROVED_STYLE_ID
            with open(target, "w", encoding="utf-8") as handle:
                json.dump(poisoned, handle, indent=2, ensure_ascii=False, sort_keys=True)
                handle.write("\n")

            code, output = run(r127, root)
            self.assertEqual(code, 1, "R-127 stayed green over a poisoned store: %s" % output)
            self.assertIn("1 of 2 rendered documents", output)

            code, output = run(inv13, root)
            self.assertEqual(code, 1, "INV-13 stayed green over a poisoned store: %s" % output)
            self.assertIn("doc_fixture_resume", output, "INV-13 did not name the document")
            self.assertIn("violations 1", output)

            # restore
            with open(target, "wb") as handle:
                handle.write(before_bytes)

            code, output = run(r127, root)
            self.assertEqual(code, 0, "R-127 did not return green after restore: %s" % output)
            self.assertIn("2 of 2 rendered documents", output)
            self.assertEqual(run(inv13, root)[0], 0)
            self.assertEqual(digest_tree(root), before_tree, "restore was not byte identical")


class GateSeenRedForOtherReasons(unittest.TestCase):
    """The R-127 command has three failure modes. All three are exercised."""

    def test_an_empty_store_is_red_and_vacuous(self):
        r127 = acceptance_command(REQUIREMENTS, "R-127")
        with tempfile.TemporaryDirectory(prefix="career-os-empty-") as root:
            code, output = run(r127, root)
        self.assertEqual(code, 1)
        self.assertIn("over 0 documents", output)

    def test_only_one_document_kind_rendered_is_red(self):
        r127 = acceptance_command(REQUIREMENTS, "R-127")
        with tempfile.TemporaryDirectory(prefix="career-os-onekind-") as root:
            documents = build_compliant_store(root)
            os.remove(documents["doc_fixture_cover_letter"])
            code, output = run(r127, root)
        self.assertEqual(code, 1)
        self.assertIn("1 of 2 document kinds", output)

    def test_a_non_pdf_render_format_is_red(self):
        r127 = acceptance_command(REQUIREMENTS, "R-127")
        with tempfile.TemporaryDirectory(prefix="career-os-format-") as root:
            documents = build_compliant_store(root)
            target = documents["doc_fixture_cover_letter"]
            with open(target, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            payload["render_format"] = "docx"
            with open(target, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
            code, output = run(r127, root)
        self.assertEqual(code, 1)
        self.assertIn("1 of 2 rendered documents", output)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
