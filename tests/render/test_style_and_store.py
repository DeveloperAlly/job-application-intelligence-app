"""E-05 conformance, approval, and the rule that no test touches the repository store.

Serves R-127 and INV-13 of pm/03-data-contract.md.
"""

import glob
import hashlib
import json
import os
import unittest

from support import REPO_ROOT, TemporaryStore, resume_blocks

from src.render.render import render
from src.render.style import (
    CAREER_OS_DEFAULT_ID,
    SPECS,
    SpecNotFound,
    StyleStore,
    VisualStyle,
    default_style,
    store_root,
)


class E05Conformance(unittest.TestCase):
    def test_a_stored_style_carries_exactly_the_four_contract_fields(self):
        """E-05 gives VisualStyle id, name, approved and approved_at. No more, no fewer."""
        with TemporaryStore(approved=False) as store:
            path = StyleStore(store.root).path(CAREER_OS_DEFAULT_ID)
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        self.assertEqual(sorted(payload), ["approved", "approved_at", "id", "name"])
        self.assertIsInstance(payload["approved"], bool)

    def test_the_default_style_is_written_unapproved(self):
        """R-127 says the user's approved visual style. Approval is the owner's act.

        Nothing in the product may set this. The only place approved is ever true is a
        temporary store built by a test.
        """
        style = default_style()
        self.assertFalse(style.approved)
        self.assertIsNone(style.approved_at)

    def test_approved_styles_is_empty_when_nothing_is_approved(self):
        """An empty result is a real state, and it is the state of this repository today."""
        with TemporaryStore(approved=False) as store:
            self.assertEqual(StyleStore(store.root).approved_styles(), [])

    def test_a_style_with_no_layout_specification_cannot_be_rendered_in(self):
        """The stated gap: E-05 has no field that can carry geometry."""
        style = VisualStyle(id="vs_unknown_geometry", name="Unknown", approved=True)
        with self.assertRaises(SpecNotFound):
            _ = style.spec


class Inv13(unittest.TestCase):
    def test_a_rendered_document_can_only_cite_an_approved_style(self):
        """INV-13: "Every rendered GeneratedDocument references a VisualStyle whose
        approved is true." The seam makes this structural: the only style id it will ever
        return in document_fields is one it read as approved.
        """
        with TemporaryStore(approved=True) as store:
            result = render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
            approved = {s.id for s in store.styles().approved_styles()}
        self.assertIn(result.document_fields["visual_style_id"], approved)


class StoreResolution(unittest.TestCase):
    def test_store_root_follows_CAREER_OS_STORE(self):
        """The same resolution the acceptance commands in pm/03-requirements.md use."""
        previous = os.environ.get("CAREER_OS_STORE")
        try:
            os.environ["CAREER_OS_STORE"] = "/somewhere/else"
            self.assertEqual(store_root(), "/somewhere/else")
            self.assertEqual(store_root("/explicit"), "/explicit")
            del os.environ["CAREER_OS_STORE"]
            self.assertEqual(store_root(), "./store")
        finally:
            if previous is None:
                os.environ.pop("CAREER_OS_STORE", None)
            else:
                os.environ["CAREER_OS_STORE"] = previous


class NoRepositoryStoreMutation(unittest.TestCase):
    """A test that mutates ./store is a defect. This is the check, not the promise."""

    def _digest(self):
        root = os.path.join(REPO_ROOT, "store")
        entries = []
        for path in sorted(glob.glob(os.path.join(root, "**", "*"), recursive=True)):
            if os.path.isdir(path):
                entries.append(os.path.relpath(path, root) + "/")
                continue
            with open(path, "rb") as handle:
                entries.append(
                    os.path.relpath(path, root)
                    + ":"
                    + hashlib.sha256(handle.read()).hexdigest()
                )
        return hashlib.sha256("\n".join(entries).encode()).hexdigest(), len(entries)

    def test_rendering_does_not_touch_the_repository_store(self):
        before, count_before = self._digest()
        with TemporaryStore(approved=True) as store:
            render(
                resume_blocks(), CAREER_OS_DEFAULT_ID, "resume",
                styles=store.styles(), store=store.root,
                document_id="doc_fixture_resume", write_file=True,
            )
        after, count_after = self._digest()
        self.assertEqual(count_before, count_after)
        self.assertEqual(before, after)

    def test_no_render_output_exists_under_the_repository_store(self):
        """This lane owns store/visual_styles/ and nothing else under store/."""
        self.assertFalse(os.path.exists(os.path.join(REPO_ROOT, "store", "renders")))


class SpecDerivation(unittest.TestCase):
    """The rubric constraints the style is built to, asserted on the spec itself."""

    def test_the_spec_declares_one_column_and_a_two_page_ceiling(self):
        spec = SPECS[CAREER_OS_DEFAULT_ID]
        self.assertEqual(spec.columns, 1)
        self.assertEqual(spec.max_pages, 2)

    def test_the_margins_exceed_the_header_and_footer_regions(self):
        """Why no content can land in either region: there is no room inside them."""
        spec = SPECS[CAREER_OS_DEFAULT_ID]
        self.assertGreater(spec.margin_top, spec.header_region_height)
        self.assertGreater(spec.margin_bottom, spec.footer_region_height)

    def test_the_font_family_ceiling_is_recorded_as_a_choice(self):
        """D-01 font families is UNESTABLISHED in pm/03-evals.md. 2 is this lane's number."""
        spec = SPECS[CAREER_OS_DEFAULT_ID]
        self.assertEqual(spec.max_font_families, 2)
        self.assertEqual(spec.font_family, "Helvetica")


if __name__ == "__main__":
    unittest.main()
