"""What ships, read back out of the produced PDF bytes. Serves R-127.

Every assertion in this file parses the bytes the renderer produced. Not one of them
consults the layout, the style spec or the source content to learn what the file contains.
That is the point of the file: a renderer that is asked whether it made one column will
always say yes.
"""

import unittest

from support import TemporaryStore, cover_letter_blocks, resume_blocks

from src.render import inspect as I
from src.render.render import render
from src.render.style import CAREER_OS_DEFAULT_ID, SPECS

STYLE_ID = CAREER_OS_DEFAULT_ID
SPEC = SPECS[STYLE_ID]


def rendered(kind):
    content = resume_blocks() if kind == "resume" else cover_letter_blocks()
    with TemporaryStore(approved=True) as store:
        return render(content, STYLE_ID, kind, styles=store.styles())


class PageGeometry(unittest.TestCase):
    def test_page_count_is_within_the_D01_threshold(self):
        """D-01 pages: fail if more than 2, per pm/03-evals.md Thresholds."""
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                result = rendered(kind)
                observed = I.page_count(result.rendered_file)
                self.assertEqual(observed, result.page_count)
                self.assertLessEqual(observed, 2, "%s rendered %d pages" % (kind, observed))

    def test_page_size_read_from_the_mediabox(self):
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                for width, height in I.page_sizes(rendered(kind).rendered_file):
                    self.assertAlmostEqual(width, SPEC.page_width, places=2)
                    self.assertAlmostEqual(height, SPEC.page_height, places=2)


class Columns(unittest.TestCase):
    def test_body_is_a_single_text_column(self):
        """D-01 columns: fail if more than 1."""
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                counts = I.column_count(rendered(kind).rendered_file)
                self.assertTrue(counts)
                self.assertEqual(max(counts), 1, "column counts per page: %r" % (counts,))


class Fonts(unittest.TestCase):
    def test_font_families_within_the_chosen_ceiling(self):
        """D-01 font families. The rubric records this threshold as UNESTABLISHED.

        The ceiling of 2 is this lane's choice and is not evidence. What the file actually
        uses is asserted here so the number is reproducible either way.
        """
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                families = I.font_families(rendered(kind).rendered_file)
                self.assertLessEqual(len(families), SPEC.max_font_families)
                self.assertEqual(families, ["Helvetica"])

    def test_base_fonts_are_the_two_expected_faces(self):
        faces = I.base_fonts(rendered("resume").rendered_file)
        self.assertEqual(faces, ["/Helvetica", "/Helvetica-Bold"])


class HeaderAndFooter(unittest.TestCase):
    def test_no_content_sits_in_a_header_or_footer_region(self):
        """D-01: "No content sits in a page header or footer region"."""
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                intrusions = I.region_intrusions(
                    rendered(kind).rendered_file,
                    SPEC.header_region_height,
                    SPEC.footer_region_height,
                )
                self.assertEqual(
                    intrusions, [], "runs in a header or footer region: %r" % (intrusions,)
                )


class NoTablesNoImages(unittest.TestCase):
    def test_only_text_operators_appear_in_the_content_stream(self):
        """D-01: "No table objects are used for layout"."""
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                data = rendered(kind).rendered_file
                self.assertEqual(I.non_text_operators(data), [])
                self.assertEqual(I.content_operators(data), ["BT", "ET", "Td", "Tf", "Tj"])

    def test_the_file_is_not_a_scanned_image(self):
        """D-07: the file must never be a scanned image."""
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                self.assertFalse(I.has_image_xobject(rendered(kind).rendered_file))


class BoldRoleTitles(unittest.TestCase):
    def test_every_role_entry_opens_with_a_bold_face_in_the_file(self):
        """D-01: "Every role entry begins with a bold title line".

        The face is read from the PDF font resource the run points at, not from the block
        that asked for it.
        """
        result = rendered("resume")
        runs = I.runs(result.rendered_file)
        titles = [
            block["text"]
            for block in resume_blocks()["blocks"]
            if block["kind"] == "role_title"
        ]
        self.assertEqual(len(titles), 5)
        for title in titles:
            opening = " ".join(title.split()[:4])
            matched = [run for run in runs if " ".join(run.text.split()).startswith(opening)]
            self.assertTrue(matched, "no run in the file opens %r" % opening)
            self.assertIn("Bold", matched[0].font or "", "role title not bold: %r" % title)


class FileSize(unittest.TestCase):
    def test_inside_the_vendor_upload_limit(self):
        """D-07 file size: fail above the 100 MB vendor limit recorded in pm/03-evals.md."""
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                self.assertLess(len(rendered(kind).rendered_file), 100 * 1024 * 1024)


class Determinism(unittest.TestCase):
    def test_the_same_input_produces_byte_identical_output(self):
        """Required by the poison case: a restore has to be provable as exact."""
        first = rendered("resume").rendered_file
        second = rendered("resume").rendered_file
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
