"""Font metrics, encoding and the pagination rules. Serves R-127.

The metrics matter because every wrap decision rests on them and D-07 fails a document
whose words are split across lines. A wrong width table produces exactly that defect, so
the table is checked against the published Helvetica values rather than trusted.
"""

import unittest

from support import TemporaryStore, resume_blocks

from src.render import inspect as I
from src.render.layout import (
    Block,
    blocks_from_body_text,
    lay_out,
    normalise_content,
    wrap,
)
from src.render.metrics import GLYPH_WIDTHS, WINANSI_ENCODING
from src.render.pdf import UnrenderableCharacter, encode_text, glyph_name, text_width
from src.render.render import render
from src.render.style import CAREER_OS_DEFAULT_ID, SPECS

SPEC = SPECS[CAREER_OS_DEFAULT_ID]


class Metrics(unittest.TestCase):
    def test_every_winansi_glyph_name_resolves_in_both_faces(self):
        """A name in the encoding with no width would crash mid render on real content."""
        names = set(WINANSI_ENCODING.values())
        self.assertEqual(len(names), 216)
        for face, widths in GLYPH_WIDTHS.items():
            missing = sorted(name for name in names if name not in widths)
            self.assertEqual(missing, [], "%s missing %r" % (face, missing))

    def test_the_widths_match_the_published_helvetica_values(self):
        """Spot check against the base-14 metrics, not against the file they came from."""
        self.assertEqual(GLYPH_WIDTHS["Helvetica"]["space"], 278)
        self.assertEqual(GLYPH_WIDTHS["Helvetica"]["A"], 667)
        self.assertEqual(GLYPH_WIDTHS["Helvetica"]["a"], 556)
        self.assertEqual(GLYPH_WIDTHS["Helvetica-Bold"]["space"], 278)
        self.assertEqual(GLYPH_WIDTHS["Helvetica-Bold"]["A"], 722)
        self.assertEqual(GLYPH_WIDTHS["Helvetica-Bold"]["a"], 556)

    def test_text_width_scales_with_point_size(self):
        self.assertAlmostEqual(text_width("A", "Helvetica", 10.0), 6.67, places=2)
        self.assertAlmostEqual(text_width("A", "Helvetica", 20.0), 13.34, places=2)

    def test_the_bullet_glyph_is_encodable_and_survives_extraction(self):
        from src.render.pdf import TextRun, write_pdf

        self.assertEqual(glyph_name("•"), "bullet")
        self.assertEqual(encode_text("•"), b"\x95")
        data = write_pdf(
            [[TextRun("• Shipped the runtime", "Helvetica", 10.0, 54.0, 700.0)]],
            595.276,
            841.890,
        )
        self.assertIn("• Shipped the runtime", I.extracted_text(data))


class Encoding(unittest.TestCase):
    def test_an_unencodable_character_raises_rather_than_dropping(self):
        with self.assertRaises(UnrenderableCharacter) as caught:
            encode_text("café 中")
        self.assertEqual(caught.exception.character, "中")

    def test_latin_accents_and_punctuation_encode(self):
        for text in ("café", "naïve", "Zoë", "±5 percent", "50 percent", "“quoted”", "it’s"):
            with self.subTest(text=text):
                self.assertEqual(len(encode_text(text)), len(text))


class Wrapping(unittest.TestCase):
    def test_wrapping_never_splits_a_word(self):
        text = "Designed the scheduler that placed jobs across heterogeneous nodes"
        lines = wrap(text, "Helvetica", 10.0, 120.0, 120.0)
        self.assertGreater(len(lines), 1)
        self.assertEqual(" ".join(lines).split(), text.split())
        for line in lines:
            self.assertLessEqual(text_width(line, "Helvetica", 10.0), 120.0)

    def test_a_hanging_indent_narrows_only_the_first_line_when_asked(self):
        lines = wrap("alpha beta gamma delta epsilon", "Helvetica", 10.0, 40.0, 200.0)
        self.assertLessEqual(text_width(lines[0], "Helvetica", 10.0), 40.0)


class BodyTextClassifier(unittest.TestCase):
    def test_it_changes_no_word(self):
        body = (
            "Wren Halloway\n"
            "wren.halloway@example.invalid\n"
            "\n"
            "Work Experience\n"
            "- Shipped the runtime to production\n"
            "Ran the developer programme\n"
        )
        blocks = blocks_from_body_text(body)
        rendered_words = " ".join(block.text for block in blocks).split()
        source_words = [word for word in body.split() if word != "-"]
        self.assertEqual(rendered_words, source_words)

    def test_it_finds_headings_only_on_whole_lines(self):
        blocks = blocks_from_body_text(
            "Wren Halloway\ncontact line\nEducation\nStudied education at university\n"
        )
        kinds = [(block.kind, block.text) for block in blocks]
        self.assertEqual(kinds[0][0], "name")
        self.assertEqual(kinds[1][0], "contact")
        self.assertEqual(kinds[2], ("heading", "Education"))
        self.assertEqual(kinds[3][0], "paragraph")

    def test_it_declares_no_role_titles(self):
        """The stated gap, at its source: plain text cannot say which line is a role."""
        blocks = blocks_from_body_text("Name\ncontact\nWork Experience\nStaff Engineer, Nimbus\n")
        self.assertEqual([b.kind for b in blocks if b.kind == "role_title"], [])

    def test_explicit_blocks_are_accepted_unchanged(self):
        blocks = normalise_content({"blocks": [{"kind": "heading", "text": "Skills"}]})
        self.assertEqual([(b.kind, b.text) for b in blocks], [("heading", "Skills")])


class Pagination(unittest.TestCase):
    def test_content_longer_than_one_page_paginates_rather_than_truncating(self):
        """Dropping content to hit a page threshold is the same defect as inventing it."""
        blocks = [Block("heading", "Work Experience")]
        for index in range(120):
            blocks.append(
                Block("bullet", "Delivered measurable outcome number %d for the team" % index)
            )
        laid_out = lay_out(blocks, SPEC)
        self.assertGreater(laid_out.page_count, 1)
        placed = " ".join(run.text for page in laid_out.pages for run in page)
        for index in (0, 59, 119):
            self.assertIn("outcome number %d " % index, placed + " ")

    def test_an_overlong_document_fails_D01_pages_rather_than_being_cut(self):
        content = {
            "blocks": [{"kind": "heading", "text": "Work Experience"}]
            + [
                {"kind": "bullet", "text": "Delivered measurable outcome number %d" % index}
                for index in range(200)
            ]
        }
        with TemporaryStore(approved=True) as store:
            result = render(content, CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
        self.assertGreater(result.page_count, 2)
        pages_finding = [f for f in result.findings if f.criterion == "pages"][0]
        self.assertEqual(pages_finding.outcome, "fail")
        self.assertEqual(pages_finding.observed, I.page_count(result.rendered_file))
        # and nothing was lost on the way
        self.assertIn("outcome number 199", " ".join(result.extracted_text.split()))

    def test_a_heading_is_not_orphaned_at_the_foot_of_a_page(self):
        blocks = [Block("paragraph", "Filler line %d of body text" % i) for i in range(52)]
        blocks.append(Block("heading", "Education"))
        blocks.append(Block("paragraph", "Bachelor of Engineering, Mechatronics"))
        laid_out = lay_out(blocks, SPEC)
        for page in laid_out.pages:
            texts = [run.text for run in page]
            if "Education" in texts:
                self.assertNotEqual(
                    texts[-1], "Education", "heading left alone at the foot of a page"
                )


class NoRunLeavesTheContentBox(unittest.TestCase):
    def test_every_run_sits_inside_the_margins(self):
        with TemporaryStore(approved=True) as store:
            result = render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
        for run in I.runs(result.rendered_file):
            self.assertGreaterEqual(round(run.x, 3), SPEC.content_left - 0.01)
            width = text_width(run.text, (run.font or "/Helvetica").lstrip("/"), run.size)
            self.assertLessEqual(
                run.x + width, SPEC.content_right + 0.01, "run overflows the measure: %r" % run
            )
            self.assertGreaterEqual(run.bottom, SPEC.footer_region_height)


if __name__ == "__main__":
    unittest.main()
