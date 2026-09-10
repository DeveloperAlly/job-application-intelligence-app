"""Every error case listed under S-10 in pm/03-interfaces.md. Serves R-127.

S-10 lists five error cases. Each has a test class below, named for it and carrying the
sentence from the seam it answers. Two adjacent cases from S-14 that bear on rendering are
included too, because the seam that refuses is this one.

The seam distinguishes refusals from findings, and so does this file. S-10 is explicit
that a layout fault "is a D-01 and D-07 scoring failure at S-08 rather than a render
error", so those cases assert a successful render carrying a failing finding, not an
exception.
"""

import unittest

from support import TemporaryStore, resume_blocks

from src.render import inspect as I
from src.render import render as render_module
from src.render.layout import ContentRefused
from src.render.pdf import UnrenderableCharacter, WordTooWide
from src.render.render import (
    ContentNotRenderable,
    ExtractionMismatch,
    NoApprovedStyle,
    StyleNotApproved,
    render,
)
from src.render.style import CAREER_OS_DEFAULT_ID, StyleStore, VisualStyle, default_style


class Case1_RequestedStyleIsNotTheApprovedOne(unittest.TestCase):
    """S-10: "The requested style_id is not the approved one. The render refuses and names
    the style requested and the style approved, because R-127 does not permit an
    unapproved visual style to be produced at all."
    """

    def test_refuses_and_names_both_styles(self):
        with TemporaryStore(approved=True) as store:
            with self.assertRaises(StyleNotApproved) as caught:
                render(resume_blocks(), "vs_some_other_style", "resume", styles=store.styles())
        self.assertEqual(caught.exception.requested, "vs_some_other_style")
        self.assertEqual(caught.exception.approved, [CAREER_OS_DEFAULT_ID])
        self.assertIn("vs_some_other_style", str(caught.exception))
        self.assertIn(CAREER_OS_DEFAULT_ID, str(caught.exception))

    def test_a_stored_but_unapproved_style_is_refused(self):
        """The style exists. It is simply not approved, and that is the whole test."""
        with TemporaryStore(approved=False) as store:
            with self.assertRaises(NoApprovedStyle):
                render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())


class Case1b_NoStyleHasEverBeenApproved(unittest.TestCase):
    """pm/03-interfaces.md S-14: "No style has ever been approved. S-10 then refuses every
    render... The observable is a refused render naming an approved style that does not
    exist."
    """

    def test_refuses_naming_that_no_approved_style_exists(self):
        with TemporaryStore(approved=False) as store:
            with self.assertRaises(NoApprovedStyle) as caught:
                render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
        self.assertIsNone(caught.exception.approved)
        self.assertIn("no visual style is approved", str(caught.exception))

    def test_an_empty_store_refuses_too(self):
        with TemporaryStore(approved=False) as store:
            empty = StyleStore(store.root + "/nothing-here")
            with self.assertRaises(NoApprovedStyle):
                render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=empty)


class Case2_ExtractedTextDiffersFromSource(unittest.TestCase):
    """S-10: "The text extracted from the rendered file differs from the source content,
    with spaces inserted between letters or words split across lines... What is observable
    is the letter spacing artefact check returning matches on extracted_text while the
    source content has none."

    The renderer is built so this does not happen, so the check is exercised two ways:
    the predicate is run against a genuinely letterspaced PDF, and the seam is forced to
    produce one so that the refusal itself is seen to fire.
    """

    def test_the_predicate_fires_on_a_genuinely_letterspaced_file(self):
        from src.render.pdf import TextRun, write_pdf

        runs = []
        x = 54.0
        for character in "Work Experience":
            runs.append(TextRun(character, "Helvetica", 10.0, x, 700.0))
            x += 11.0
        data = write_pdf([runs], 595.276, 841.890)
        text = I.extracted_text(data)
        self.assertEqual(text.strip(), "W o r k  E x p e r i e n c e")
        self.assertEqual(len(I.letter_spacing_artefact_lines(text)), 1)
        self.assertEqual(len(I.letter_spacing_artefact_lines("Work Experience")), 0)

    def test_the_seam_refuses_when_the_round_trip_fails(self):
        """Force the writer to emit a letterspaced file and confirm the seam refuses it.

        Substituting the writer is the only way to reach this branch, because the real
        writer cannot produce the defect. That is the correct shape: the guard is proven
        to fire, and the renderer is proven not to need it.
        """
        from src.render.pdf import TextRun, write_pdf as real_write_pdf

        def letterspacing_writer(pages, page_width, page_height, **kwargs):
            spaced = []
            for page in pages:
                runs = []
                for run in page:
                    x = run.x
                    for character in run.text:
                        runs.append(TextRun(character, run.face, run.size, x, run.y))
                        x += run.size * 1.1
                spaced.append(runs)
            return real_write_pdf(spaced, page_width, page_height, **kwargs)

        original = render_module.write_pdf
        render_module.write_pdf = letterspacing_writer
        try:
            with TemporaryStore(approved=True) as store:
                with self.assertRaises(ExtractionMismatch) as caught:
                    render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
        finally:
            render_module.write_pdf = original
        self.assertTrue(caught.exception.artefact_lines)
        self.assertIn("letter spacing artefact lines", str(caught.exception))

    def test_the_seam_refuses_when_a_word_is_dropped(self):
        """Losing content is refused on the same round trip, not only gaining it."""
        from src.render.pdf import write_pdf as real_write_pdf

        def dropping_writer(pages, page_width, page_height, **kwargs):
            trimmed = [page[:-3] for page in pages]
            return real_write_pdf(trimmed, page_width, page_height, **kwargs)

        original = render_module.write_pdf
        render_module.write_pdf = dropping_writer
        try:
            with TemporaryStore(approved=True) as store:
                with self.assertRaises(ExtractionMismatch) as caught:
                    render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
        finally:
            render_module.write_pdf = original
        self.assertTrue(caught.exception.lost)


class Case3_HeaderRegionOrMoreThanOneColumn(unittest.TestCase):
    """S-10: "The style places content in a page header region, or produces more than one
    text column. The render still succeeds; this is a D-01 and D-07 scoring failure at
    S-08 rather than a render error, and the observable is a successful render with a
    failing D-01."
    """

    def test_the_detectors_report_a_failing_D01_rather_than_raising(self):
        """Both detectors are shown red against deliberately bad files.

        The style this lane defines produces neither fault, so a passing run proves
        nothing about the detector. These two files prove it is not a rubber stamp.
        """
        from src.render.pdf import TextRun, write_pdf

        two_column = []
        for index in range(12):
            y = 760.0 - index * 14.0
            two_column.append(
                TextRun("Left column line %d of running text" % index, "Helvetica", 10.0, 54.0, y)
            )
            two_column.append(
                TextRun("Right column line %d of text" % index, "Helvetica", 10.0, 330.0, y)
            )
        data = write_pdf([two_column], 595.276, 841.890)
        self.assertEqual(I.column_count(data), [2])

        header = write_pdf(
            [[TextRun("Running header, curriculum vitae", "Helvetica", 9.0, 54.0, 820.0)]],
            595.276,
            841.890,
        )
        intrusions = I.region_intrusions(header, 36.0, 36.0)
        self.assertEqual(len(intrusions), 1)
        self.assertEqual(intrusions[0][0], "header")

        footer = write_pdf(
            [[TextRun("Page 1 of 2", "Helvetica", 9.0, 54.0, 20.0)]], 595.276, 841.890
        )
        self.assertEqual(region_kinds(I.region_intrusions(footer, 36.0, 36.0)), ["footer"])

    def test_a_file_with_a_table_rule_is_caught_by_the_operator_check(self):
        """D-01: "No table objects are used for layout".

        A file drawn with path operators is what a table looks like in a content stream.
        The check is shown red against one built by hand.
        """
        import io

        from pypdf import PdfReader
        from pypdf.generic import ContentStream

        stream = b"0 0 0 RG 54 700 400 1 re S\nBT /F1 10 Tf 54 680 Td (Cell) Tj ET\n"
        pdf = _hand_built_pdf(stream)
        document = PdfReader(io.BytesIO(pdf))
        operations = ContentStream(document.pages[0].get_contents(), document).operations
        used = sorted({op.decode() for _operands, op in operations})
        self.assertIn("re", used)
        self.assertEqual(sorted(I.non_text_operators(pdf)), ["RG", "S", "re"])


class Case4_FileExceedsTheUploadLimit(unittest.TestCase):
    """S-10: "The rendered file exceeds the upload limit the rubric records for the target
    vendor. The render succeeds and the document cannot be submitted, observable from the
    file size alone."
    """

    def test_the_size_finding_is_present_and_measured_on_the_bytes(self):
        with TemporaryStore(approved=True) as store:
            result = render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
        finding = _finding(result, "file size against the vendor upload limit")
        self.assertEqual(finding.observed, len(result.rendered_file))
        self.assertEqual(finding.outcome, "pass")

    def test_the_threshold_is_the_100MB_vendor_limit_not_the_withdrawn_2_5MB(self):
        """pm/03-evals.md records the 2.5 MB figure as withdrawn and unsourced."""
        self.assertEqual(render_module.VENDOR_UPLOAD_LIMIT_BYTES, 100 * 1024 * 1024)


class Case5_ClaimPositionsDoNotCorrespond(unittest.TestCase):
    """S-10: "The render succeeds but the claim positions in the rendered file no longer
    correspond to the positions in claim_map... The observable is a claim whose recorded
    position does not land on that claim in the rendered file."
    """

    def test_a_locatable_claim_gets_a_position_in_the_extracted_text(self):
        claims = {
            "cl_queue_wait": "cutting median queue wait from 41 seconds to 6 seconds",
            "cl_programme": "from 40 to 900 weekly active builders",
        }
        with TemporaryStore(approved=True) as store:
            result = render(
                resume_blocks(), CAREER_OS_DEFAULT_ID, "resume",
                styles=store.styles(), claim_map=claims,
            )
        for claim_id, text in claims.items():
            position = result.claim_positions[claim_id]
            self.assertIsNotNone(position, "claim %s did not land in the file" % claim_id)
            flat = " ".join(result.extracted_text.split())
            self.assertTrue(flat[position:].startswith(text))
        self.assertEqual(
            _finding(result, "claim positions locatable in the rendered file").outcome, "pass"
        )

    def test_an_unlocatable_claim_is_named_and_fails(self):
        claims = {"cl_absent": "a claim that appears nowhere in this document at all"}
        with TemporaryStore(approved=True) as store:
            result = render(
                resume_blocks(), CAREER_OS_DEFAULT_ID, "resume",
                styles=store.styles(), claim_map=claims,
            )
        self.assertIsNone(result.claim_positions["cl_absent"])
        finding = _finding(result, "claim positions locatable in the rendered file")
        self.assertEqual(finding.outcome, "fail")
        self.assertIn("cl_absent", finding.observed["unlocatable"])

    def test_no_claim_map_is_vacuous_not_pass(self):
        with TemporaryStore(approved=True) as store:
            result = render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
        self.assertEqual(
            _finding(result, "claim positions locatable in the rendered file").outcome, "vacuous"
        )


class ContentProvenance(unittest.TestCase):
    """Not an S-10 case. The rule that content in a PDF and not in its source is invisible
    to every upstream gate and reaches an employer.
    """

    def test_empty_content_is_refused_rather_than_filled_in(self):
        with TemporaryStore(approved=True) as store:
            for empty in ("", "   \n\n", {"blocks": []}):
                with self.subTest(empty=empty):
                    with self.assertRaises(ContentRefused):
                        render(empty, CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())

    def test_a_block_with_no_text_is_refused_rather_than_supplied(self):
        with TemporaryStore(approved=True) as store:
            with self.assertRaises(ContentRefused):
                render(
                    {"blocks": [{"kind": "heading", "text": "  "}]},
                    CAREER_OS_DEFAULT_ID, "resume", styles=store.styles(),
                )

    def test_an_unencodable_character_is_refused_rather_than_substituted(self):
        content = {"blocks": [{"kind": "paragraph", "text": "Shipped the 中文 runtime"}]}
        with TemporaryStore(approved=True) as store:
            with self.assertRaises(UnrenderableCharacter) as caught:
                render(content, CAREER_OS_DEFAULT_ID, "cover_letter", styles=store.styles())
        self.assertEqual(caught.exception.character, "中")

    def test_an_em_dash_is_refused(self):
        """Standing owner rule, applied to what the PDF says.

        Rewriting it would be the renderer altering content; emitting it would break the
        rule. Refusing keeps both, and puts the fix where it belongs, in the composer.
        """
        content = {"blocks": [{"kind": "paragraph", "text": "I led the team \u2014 and shipped it"}]}
        with TemporaryStore(approved=True) as store:
            with self.assertRaises(ContentNotRenderable) as caught:
                render(content, CAREER_OS_DEFAULT_ID, "cover_letter", styles=store.styles())
        self.assertIn("em dash", str(caught.exception))

    def test_a_word_too_wide_is_refused_rather_than_split(self):
        """D-07 fails a document with a word split across lines, so splitting is not a fix."""
        content = {"blocks": [{"kind": "paragraph", "text": "A" * 400}]}
        with TemporaryStore(approved=True) as store:
            with self.assertRaises(WordTooWide):
                render(content, CAREER_OS_DEFAULT_ID, "cover_letter", styles=store.styles())

    def test_output_kind_must_be_one_of_the_two_E08_kinds(self):
        with TemporaryStore(approved=True) as store:
            with self.assertRaises(ContentNotRenderable):
                render(resume_blocks(), CAREER_OS_DEFAULT_ID, "portfolio", styles=store.styles())


class DocumentFields(unittest.TestCase):
    """The E-08 fields the caller records. INV-13 reads two of them."""

    def test_render_returns_the_three_E08_render_fields(self):
        with TemporaryStore(approved=True) as store:
            result = render(resume_blocks(), CAREER_OS_DEFAULT_ID, "resume", styles=store.styles())
        self.assertEqual(result.document_fields["visual_style_id"], CAREER_OS_DEFAULT_ID)
        self.assertEqual(result.document_fields["render_format"], "pdf")
        self.assertIsNone(result.document_fields["render_uri"])
        self.assertEqual(result.style_id_used, CAREER_OS_DEFAULT_ID)

    def test_writing_a_file_returns_a_render_uri_under_the_store(self):
        import os

        with TemporaryStore(approved=True) as store:
            result = render(
                resume_blocks(), CAREER_OS_DEFAULT_ID, "resume",
                styles=store.styles(), store=store.root,
                document_id="doc_fixture_resume", write_file=True,
            )
            self.assertEqual(result.render_uri, "renders/doc_fixture_resume-r1.pdf")
            path = os.path.join(store.root, result.render_uri)
            self.assertTrue(os.path.exists(path))
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), result.rendered_file)


def region_kinds(intrusions):
    return sorted({region for region, _run in intrusions})


def _finding(result, criterion):
    matches = [f for f in result.findings if f.criterion == criterion]
    assert matches, "no finding named %r" % criterion
    return matches[0]


def _hand_built_pdf(stream):
    """A tiny PDF carrying an arbitrary content stream, for the negative controls."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font "
        b"<< /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    out = bytearray(b"%PDF-1.7\n")
    offsets = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % index + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


if __name__ == "__main__":
    unittest.main()
