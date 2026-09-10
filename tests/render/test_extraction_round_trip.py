"""The extraction round trip. Serves R-127 and D-07 of pm/03-evals.md.

This is the real test of a renderer. A document an applicant tracking system cannot parse
is worthless however it looks, and the only way to know whether the machine can read it is
to render, extract the text back out of the bytes, and compare.

Every assertion below runs on `extracted_text`, which is pypdf's reading of the produced
file, never on the source content.
"""

import unittest

from support import TemporaryStore, cover_letter_blocks, resume_blocks, resume_document

from src.render import inspect as I
from src.render.render import REQUIRED_SECTION_TITLES, render
from src.render.style import CAREER_OS_DEFAULT_ID


def rendered(kind, content=None):
    if content is None:
        content = resume_blocks() if kind == "resume" else cover_letter_blocks()
    with TemporaryStore(approved=True) as store:
        return render(content, CAREER_OS_DEFAULT_ID, kind, styles=store.styles())


class SectionTitles(unittest.TestCase):
    def test_three_standard_section_titles_come_back_out(self):
        """D-07: fail if 1 or more of the three standard section titles is missing.

        The vendor documentation quoted in pm/03-evals.md instructs typical section titles
        such as Education, Work Experience and Personal Details. The rubric's own command
        anchors each title on a whole line, so this does too.
        """
        text = rendered("resume").extracted_text
        present = I.section_titles_present(text, REQUIRED_SECTION_TITLES)
        self.assertGreaterEqual(
            len(present),
            3,
            "only %d of the standard titles survived extraction: %r"
            % (len(present), present),
        )
        self.assertIn("Work Experience", present)
        self.assertIn("Education", present)
        self.assertIn("Skills", present)


class LetterSpacing(unittest.TestCase):
    def test_no_letter_spacing_artefact_in_the_extracted_text(self):
        """D-07: `grep -cE '([A-Za-z] ){3,}[A-Za-z]'` must be 0.

        The vendor documents that unusual character spacing and font choice can create or
        lose spaces. src/render/pdf.py emits one Tj per line and never a TJ array, which
        is the mechanism that makes this hold rather than the hope that it does.
        """
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                text = rendered(kind).extracted_text
                offending = I.letter_spacing_artefact_lines(text)
                self.assertEqual(offending, [], "artefact lines: %r" % (offending[:5],))


class WordIntegrity(unittest.TestCase):
    def test_no_word_is_split_across_lines(self):
        """D-07: "No word is split across lines".

        Checked as: every whitespace separated token in the extracted text is a token of
        the source content. A split word produces two fragments that are not source
        tokens, so this catches it without needing to know where the breaks fell.
        """
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                blocks = resume_blocks() if kind == "resume" else cover_letter_blocks()
                source = "\n".join(block["text"] for block in blocks["blocks"])
                text = rendered(kind).extracted_text
                stray = I.words_only_in_extracted(source, text, ignore=("•",))
                self.assertEqual(stray, [], "fragments in the file, not in the source: %r" % stray)

    def test_no_word_is_lost_in_rendering(self):
        """Dropping content is the same defect class as inventing it."""
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                blocks = resume_blocks() if kind == "resume" else cover_letter_blocks()
                source = "\n".join(block["text"] for block in blocks["blocks"])
                text = rendered(kind).extracted_text
                lost = I.words_lost_in_render(source, text, ignore=("•",))
                self.assertEqual(lost, [], "source words absent from the file: %r" % lost)


class BodyTextSample(unittest.TestCase):
    def test_a_sample_of_body_text_is_recovered_unmangled(self):
        """A named sample of the body, recovered from the bytes as a contiguous string."""
        text = " ".join(rendered("resume").extracted_text.split())
        samples = [
            "Wren Halloway",
            "Staff Engineer, Developer Platform, Nimbus Clearing",
            "cutting median queue wait from 41 seconds to 6 seconds",
            "Grew the partner developer programme from 40 to 900 weekly active builders",
            "Bachelor of Engineering, Mechatronics, Fictional University of Wollongong",
            "wren.halloway@example.invalid",
        ]
        recovered = [sample for sample in samples if sample in text]
        self.assertEqual(
            len(recovered),
            len(samples),
            "%d of %d samples recovered; missing %r"
            % (len(recovered), len(samples), [s for s in samples if s not in recovered]),
        )


class ReadingOrder(unittest.TestCase):
    def test_extraction_order_equals_visual_reading_order(self):
        """D-07: "Extraction order equals visual reading order"."""
        for kind in ("resume", "cover_letter"):
            with self.subTest(kind=kind):
                runs = I.runs(rendered(kind).rendered_file)
                self.assertTrue(I.reading_order_matches_visual(runs))


class BodyTextForm(unittest.TestCase):
    def test_body_text_input_round_trips_its_words(self):
        """E-08 stores only body_text, so the string form must round trip too."""
        document = resume_document()
        result = rendered("resume", content=document["body_text"])
        source_words = set(document["body_text"].split())
        # the bullet markers in body_text are consumed by the classifier and redrawn
        source_words.discard("-")
        text = result.extracted_text
        stray = I.words_only_in_extracted(document["body_text"], text, ignore=("•",))
        self.assertEqual(stray, [])

    def test_body_text_input_cannot_produce_bold_role_titles(self):
        """The stated gap, asserted so it cannot be quietly mistaken for a pass.

        A role title is indistinguishable from a paragraph in plain text, and this
        renderer does not infer, so the D-01 bold title criterion is VACUOUS rather than
        passing whenever content arrives as body_text.
        """
        result = rendered("resume", content=resume_document()["body_text"])
        finding = [
            f for f in result.findings
            if f.criterion == "every role entry begins with a bold title line"
        ][0]
        self.assertEqual(finding.outcome, "vacuous")


if __name__ == "__main__":
    unittest.main()
