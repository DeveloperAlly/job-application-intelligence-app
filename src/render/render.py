"""S-10 Render to output document. Serves R-127.

Written against seam S-10 of pm/03-interfaces.md, which names four inputs, four outputs
and five error cases. Every one of the five is answered below and each is labelled with
the sentence from the seam it answers, so that the coverage is checkable rather than
asserted.

Inputs, per S-10: document_content, style_id, output_kind.
Outputs, per S-10: rendered_file, page_count, extracted_text, style_id_used.

The seam's outputs are all read back out of the produced bytes. page_count is not the
number of pages the layout believed it made and extracted_text is not the source content;
both are parsed from the file with pypdf. This is the module where "assert on what ships"
is enforced in the product rather than only in the tests, because a caller that trusts a
renderer's self report has no way to find out it was wrong.

WHAT THIS MODULE WILL NOT DO. It will not supply, complete, summarise, shorten or improve
a document's content. Where content does not fit it reports the page count and lets D-01
fail; it never truncates. Where a character cannot be encoded it refuses; it never
substitutes. Where the extracted text does not match the source it refuses; it never ships
a file that reads differently from the document that was approved.

WHAT IT DOES NOT WRITE. It does not write to the `documents` collection. E-08's
visual_style_id, render_format and render_uri are returned in `document_fields` for the
caller to apply, because the document record belongs to the composing seams and a renderer
that edited it would be two owners on one file.
"""

import os

from . import inspect as inspect_pdf
from .layout import ContentRefused, lay_out, normalise_content
from .pdf import UnrenderableCharacter, WordTooWide, write_pdf
from .style import SpecNotFound, StyleStore, VisualStyle, store_root

RENDER_COLLECTION = "renders"
RENDER_FORMAT = "pdf"
DOCUMENT_KINDS = ("resume", "cover_letter")

# D-07 of pm/03-evals.md: "Extracted text contains the contact block and section titles
# drawn from the standard set". The rubric's own command anchors on three titles.
REQUIRED_SECTION_TITLES = ("Experience", "Work Experience", "Education", "Skills")
REQUIRED_SECTION_TITLE_COUNT = 3

# D-07 file size: "fail above the vendor upload limit of 100 MB stated in the fetched
# vendor documentation". The widely repeated 2.5 MB figure is recorded as withdrawn in
# pm/03-evals.md and is not used here.
VENDOR_UPLOAD_LIMIT_BYTES = 100 * 1024 * 1024

# The bullet marker the layout draws. It is not part of the source content, so the content
# provenance comparison has to know to ignore it or it would report the renderer as having
# invented a word.
RENDERER_SUPPLIED_TOKENS = ("•",)

# Owner standing rule: no em dashes anywhere, including in what a rendered document says.
# Refusing is the only resolution that keeps both that rule and content provenance: the
# renderer must not rewrite the character, so the composer has to.
# Written as a codepoint escape rather than the literal character, because the standing
# rule is that the character appears nowhere in this codebase, and a detector that has to
# contain what it forbids would otherwise be the one exception.
FORBIDDEN_CHARACTERS = {"\u2014": "em dash"}


class RenderError(Exception):
    """Base for every refusal in this seam."""


class NoApprovedStyle(RenderError):
    """No style has ever been approved, so nothing may be rendered.

    S-10, and pm/03-interfaces.md S-14: "No style has ever been approved. S-10 then
    refuses every render, so nothing can be scored on the dimensions measured over the
    rendered artefact and nothing reaches approval. The observable is a refused render
    naming an approved style that does not exist."
    """

    def __init__(self, requested):
        super().__init__(
            "render refused: style %r was requested and no visual style is approved; "
            "R-127 admits only the user's approved visual style" % (requested,)
        )
        self.requested = requested
        self.approved = None


class StyleNotApproved(RenderError):
    """The requested style is not the approved one.

    S-10 error case, verbatim: "The requested style_id is not the approved one. The render
    refuses and names the style requested and the style approved, because R-127 does not
    permit an unapproved visual style to be produced at all."
    """

    def __init__(self, requested, approved):
        super().__init__(
            "render refused: style requested %r, style approved %s"
            % (requested, ", ".join(repr(a) for a in approved) if approved else "none")
        )
        self.requested = requested
        self.approved = list(approved)


class ExtractionMismatch(RenderError):
    """The text that comes back out of the file is not the text that went in.

    S-10 error case, verbatim: "The text extracted from the rendered file differs from the
    source content, with spaces inserted between letters or words split across lines.
    Every text check then runs against text the reader will never see, and the rendered
    document may fail an applicant tracking system while the source content looks clean."

    The seam records the observable as the letter spacing check matching on extracted_text
    while the source is clean. This raises rather than only reporting, because a file whose
    text a machine reads differently from the approved document is not a lesser version of
    the document, it is a different one.
    """

    def __init__(self, artefact_lines, invented, lost):
        super().__init__(
            "render refused: extracted text does not match source content. "
            "letter spacing artefact lines %d, words only in the rendered file %s, "
            "words lost in rendering %s"
            % (len(artefact_lines), invented[:10], lost[:10])
        )
        self.artefact_lines = artefact_lines
        self.invented = invented
        self.lost = lost


class ContentNotRenderable(RenderError):
    """The content carries something the renderer must not silently change."""

    def __init__(self, message, detail=None):
        super().__init__(message)
        self.detail = detail


class Finding:
    """One rubric observation about the file that shipped.

    A finding is not an error. S-10 is explicit that a layout fault is "a D-01 and D-07
    scoring failure at S-08 rather than a render error", so those are reported here and
    scored there.
    """

    __slots__ = ("dimension", "criterion", "observed", "threshold", "outcome")

    def __init__(self, dimension, criterion, observed, threshold, outcome):
        self.dimension = dimension
        self.criterion = criterion
        self.observed = observed
        self.threshold = threshold
        self.outcome = outcome

    def __repr__(self):
        return "Finding(%s, %s, observed=%r, threshold=%r, %s)" % (
            self.dimension,
            self.criterion,
            self.observed,
            self.threshold,
            self.outcome,
        )


class RenderResult:
    """The S-10 outputs, plus what the caller needs to record and to score."""

    def __init__(
        self,
        rendered_file,
        page_count,
        extracted_text,
        style_id_used,
        findings,
        document_fields,
        claim_positions,
        render_uri=None,
    ):
        self.rendered_file = rendered_file
        self.page_count = page_count
        self.extracted_text = extracted_text
        self.style_id_used = style_id_used
        self.findings = findings
        self.document_fields = document_fields
        self.claim_positions = claim_positions
        self.render_uri = render_uri

    @property
    def failing_findings(self):
        return [finding for finding in self.findings if finding.outcome == "fail"]

    @property
    def byte_size(self):
        return len(self.rendered_file)


def _source_text_of(blocks):
    return "\n".join(block.text for block in blocks)


def _check_forbidden_characters(blocks):
    for index, block in enumerate(blocks):
        for character, label in FORBIDDEN_CHARACTERS.items():
            position = block.text.find(character)
            if position >= 0:
                raise ContentNotRenderable(
                    "render refused: block %d of kind %s contains an %s at position %d. "
                    "The renderer will not rewrite it, because content that differs "
                    "between the document and the PDF is invisible to every upstream gate."
                    % (index, block.kind, label, position),
                    detail={"index": index, "kind": block.kind, "character": character},
                )


def resolve_style(style_id, styles):
    """Return the approved VisualStyle for this render, or refuse.

    Answers the first S-10 error case. There is no path through this function that returns
    an unapproved style.
    """
    approved = styles.approved_styles()
    if not approved:
        raise NoApprovedStyle(style_id)
    approved_ids = [style.id for style in approved]
    for style in approved:
        if style.id == style_id:
            return style
    raise StyleNotApproved(style_id, approved_ids)


def render(
    document_content,
    style_id,
    output_kind,
    styles=None,
    store=None,
    claim_map=None,
    document_id=None,
    revision=1,
    write_file=False,
):
    """The S-10 seam.

    `styles` is a StyleStore; when absent one is built over `store` or CAREER_OS_STORE.
    `write_file` is off by default: this lane does not own the `renders` collection in the
    repository store, so nothing is written unless a caller asks for it, and tests pass a
    temporary root.
    """
    if output_kind not in DOCUMENT_KINDS:
        raise ContentNotRenderable(
            "output_kind must be one of %s, got %r" % (DOCUMENT_KINDS, output_kind)
        )
    if styles is None:
        styles = StyleStore(store)

    style = resolve_style(style_id, styles)
    spec = style.spec

    blocks = normalise_content(document_content)
    _check_forbidden_characters(blocks)
    source_text = _source_text_of(blocks)

    laid_out = lay_out(blocks, spec)
    pdf_bytes = write_pdf(
        laid_out.pages, spec.page_width, spec.page_height, language=spec.language
    )

    # Everything below reads the produced bytes. Nothing below consults `laid_out`.
    observed_runs = inspect_pdf.runs(pdf_bytes)
    observed_page_count = inspect_pdf.page_count(pdf_bytes)
    text = inspect_pdf.extracted_text(pdf_bytes)

    artefact_lines = inspect_pdf.letter_spacing_artefact_lines(text)
    invented = inspect_pdf.words_only_in_extracted(
        source_text, text, ignore=RENDERER_SUPPLIED_TOKENS
    )
    lost = inspect_pdf.words_lost_in_render(source_text, text, ignore=RENDERER_SUPPLIED_TOKENS)
    if artefact_lines or invented or lost:
        raise ExtractionMismatch(artefact_lines, invented, lost)

    findings = _score_file(
        pdf_bytes, text, observed_runs, observed_page_count, spec, output_kind, blocks
    )

    claim_positions = _locate_claims(text, claim_map, findings)

    render_uri = None
    if write_file:
        render_uri = _write_render(pdf_bytes, store, styles, document_id, revision)

    document_fields = {
        "visual_style_id": style.id,
        "render_format": RENDER_FORMAT,
        "render_uri": render_uri,
    }

    return RenderResult(
        rendered_file=pdf_bytes,
        page_count=observed_page_count,
        extracted_text=text,
        style_id_used=style.id,
        findings=findings,
        document_fields=document_fields,
        claim_positions=claim_positions,
        render_uri=render_uri,
    )


def _bold_title_finding(observed_runs, blocks, output_kind):
    """D-01: "Every role entry begins with a bold title line", checked against the file.

    For each role_title block, the run carrying its opening words is located in the runs
    read back out of the PDF and its /BaseFont is required to be a bold face. The source
    block's declared face is never consulted; only what the file says.

    When the content arrived as E-08 body_text there are no role_title blocks, because a
    role title cannot be told from a paragraph in plain text without inferring and this
    renderer does not infer. The verdict is then VACUOUS, not pass: the criterion has
    nothing to range over, and a document rendered from body_text has no bold role titles
    at all. That is the gap recorded in src/render/layout.py, surfaced here so it cannot
    be mistaken for a passing document.
    """
    role_titles = [block for block in blocks if block.kind == "role_title"]
    if output_kind != "resume":
        return Finding(
            "D-01",
            "every role entry begins with a bold title line",
            "not applicable to a cover letter",
            "resume only",
            "not_applicable",
        )
    if not role_titles:
        return Finding(
            "D-01",
            "every role entry begins with a bold title line",
            "no role_title blocks in the content; content arrived without declared role "
            "entries, so no line was set as a role title",
            "every role entry bold",
            "vacuous",
        )
    not_bold = []
    for block in role_titles:
        opening = " ".join(block.text.split()[:4])
        matched = None
        for run in observed_runs:
            if " ".join(run.text.split()).startswith(opening):
                matched = run
                break
        if matched is None:
            not_bold.append((block.text[:50], "no run found"))
        elif "Bold" not in (matched.font or ""):
            not_bold.append((block.text[:50], matched.font))
    return Finding(
        "D-01",
        "every role entry begins with a bold title line",
        {"role_entries": len(role_titles), "not_bold_in_file": not_bold},
        "every role entry bold",
        "pass" if not not_bold else "fail",
    )


def _score_file(pdf_bytes, text, observed_runs, observed_page_count, spec, output_kind, blocks):
    """Rubric observations, every one measured on the produced bytes."""
    findings = [_bold_title_finding(observed_runs, blocks, output_kind)]

    findings.append(
        Finding(
            "D-01",
            "pages",
            observed_page_count,
            "at most %d" % spec.max_pages,
            "pass" if observed_page_count <= spec.max_pages else "fail",
        )
    )

    columns = inspect_pdf.column_count(pdf_bytes, all_runs=observed_runs)
    worst_columns = max(columns) if columns else 0
    findings.append(
        Finding(
            "D-01",
            "columns",
            columns,
            "at most %d" % spec.columns,
            "pass" if worst_columns <= spec.columns else "fail",
        )
    )

    # S-10 error case, verbatim: "The style places content in a page header region, or
    # produces more than one text column. The render still succeeds; this is a D-01 and
    # D-07 scoring failure at S-08 rather than a render error."
    intrusions = inspect_pdf.region_intrusions(
        pdf_bytes, spec.header_region_height, spec.footer_region_height, all_runs=observed_runs
    )
    findings.append(
        Finding(
            "D-01",
            "header or footer region occupancy",
            [(region, run.text[:40]) for region, run in intrusions],
            "no content in either region",
            "pass" if not intrusions else "fail",
        )
    )

    families = inspect_pdf.font_families(pdf_bytes)
    findings.append(
        Finding(
            "D-01",
            "font families",
            families,
            "at most %d, which is this lane's choice and not evidence; pm/03-evals.md "
            "records this threshold as unestablished" % spec.max_font_families,
            "pass" if len(families) <= spec.max_font_families else "fail",
        )
    )

    non_text = inspect_pdf.non_text_operators(pdf_bytes)
    findings.append(
        Finding(
            "D-01",
            "no table objects used for layout",
            non_text,
            "no operators outside the text set",
            "pass" if not non_text else "fail",
        )
    )

    findings.append(
        Finding(
            "D-07",
            "not a scanned image",
            inspect_pdf.has_image_xobject(pdf_bytes),
            "no image xobject",
            "pass" if not inspect_pdf.has_image_xobject(pdf_bytes) else "fail",
        )
    )

    findings.append(
        Finding(
            "D-07",
            "letter spacing artefact lines",
            len(inspect_pdf.letter_spacing_artefact_lines(text)),
            "0",
            "pass" if not inspect_pdf.letter_spacing_artefact_lines(text) else "fail",
        )
    )

    findings.append(
        Finding(
            "D-07",
            "extraction order equals visual reading order",
            inspect_pdf.reading_order_matches_visual(observed_runs),
            "true",
            "pass" if inspect_pdf.reading_order_matches_visual(observed_runs) else "fail",
        )
    )

    if output_kind == "resume":
        present = inspect_pdf.section_titles_present(text, REQUIRED_SECTION_TITLES)
        findings.append(
            Finding(
                "D-07",
                "standard section titles in extracted text",
                present,
                "at least %d of %s" % (REQUIRED_SECTION_TITLE_COUNT, list(REQUIRED_SECTION_TITLES)),
                "pass" if len(present) >= REQUIRED_SECTION_TITLE_COUNT else "fail",
            )
        )
    else:
        findings.append(
            Finding(
                "D-07",
                "standard section titles in extracted text",
                "not applicable to a cover letter",
                "resume only",
                "not_applicable",
            )
        )

    # S-10 error case, verbatim: "The rendered file exceeds the upload limit the rubric
    # records for the target vendor. The render succeeds and the document cannot be
    # submitted, observable from the file size alone."
    findings.append(
        Finding(
            "D-07",
            "file size against the vendor upload limit",
            len(pdf_bytes),
            "at most %d bytes" % VENDOR_UPLOAD_LIMIT_BYTES,
            "pass" if len(pdf_bytes) <= VENDOR_UPLOAD_LIMIT_BYTES else "fail",
        )
    )

    return findings


def _locate_claims(text, claim_map, findings):
    """Where each mapped claim landed in the extracted text.

    S-10 error case, verbatim: "The render succeeds but the claim positions in the
    rendered file no longer correspond to the positions in claim_map, so the approval
    surface cannot point at the right place in the document. The observable is a claim
    whose recorded position does not land on that claim in the rendered file."

    A claim whose text cannot be found in the extracted text is that observable, and it is
    named rather than silently dropped. With no claim_map the result is an empty mapping
    and the finding below is vacuous, which is stated rather than passed.
    """
    if not claim_map:
        findings.append(
            Finding(
                "D-08",
                "claim positions locatable in the rendered file",
                "no claim_map supplied",
                "every claim locatable",
                "vacuous",
            )
        )
        return {}

    positions = {}
    unlocatable = []
    for claim_id, claim_text in claim_map.items():
        needle = " ".join(str(claim_text).split())
        haystack = " ".join(text.split())
        position = haystack.find(needle)
        if position < 0:
            unlocatable.append(claim_id)
            positions[claim_id] = None
        else:
            positions[claim_id] = position
    findings.append(
        Finding(
            "D-08",
            "claim positions locatable in the rendered file",
            {"located": len(claim_map) - len(unlocatable), "of": len(claim_map),
             "unlocatable": unlocatable},
            "every claim locatable",
            "pass" if not unlocatable else "fail",
        )
    )
    return positions


def _write_render(pdf_bytes, store, styles, document_id, revision):
    """Write the PDF and return its render_uri.

    GAP, reported and not worked around: pm/03-data-contract.md defines render_uri as
    "where the rendered file is" and says nothing about where that is. `<store>/renders/`
    is this lane's choice, taken because the task brief names it as the fallback when the
    contract is silent. Nothing in the contract or the acceptance commands validates it,
    so a later decision can move it without any gate noticing.
    """
    root = store if store is not None else store_root()
    if not document_id:
        raise ContentNotRenderable("write_file needs a document_id to address the render by")
    directory = os.path.join(root, RENDER_COLLECTION)
    os.makedirs(directory, exist_ok=True)
    name = "%s-r%d.pdf" % (document_id, revision)
    path = os.path.join(directory, name)
    with open(path, "wb") as handle:
        handle.write(pdf_bytes)
    return os.path.join(RENDER_COLLECTION, name)


__all__ = [
    "ContentNotRenderable",
    "ContentRefused",
    "DOCUMENT_KINDS",
    "ExtractionMismatch",
    "Finding",
    "NoApprovedStyle",
    "RENDER_COLLECTION",
    "RENDER_FORMAT",
    "RenderError",
    "RenderResult",
    "SpecNotFound",
    "StyleNotApproved",
    "UnrenderableCharacter",
    "VENDOR_UPLOAD_LIMIT_BYTES",
    "VisualStyle",
    "WordTooWide",
    "render",
    "resolve_style",
]
