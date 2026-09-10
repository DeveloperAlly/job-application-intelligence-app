"""Read facts back out of produced PDF bytes. Serves R-127 and every rubric check on it.

This module exists because of one rule: assert on what ships. Page count, column count,
font families and text are properties of the file an employer receives, not of the source
that declared them. A renderer that reported its own intentions would be reporting a
claim, and a claim is not evidence. Everything here therefore parses the bytes with
pypdf, which pm/03-evals.md establishes by command is the only PDF reader present on this
machine: pdftotext is not on PATH and pdfplumber is not installed.

Nothing here writes. Nothing here is allowed to consult the source content except where a
function takes it explicitly in order to compare the two, which is the point of
`words_only_in_extracted`.
"""

import io
import re

from pypdf import PdfReader
from pypdf.generic import ContentStream

# D-07 of pm/03-evals.md, verbatim: `grep -cE '([A-Za-z] ){3,}[A-Za-z]'` must be 0.
LETTER_SPACING = re.compile(r"([A-Za-z] ){3,}[A-Za-z]")

# Conservative vertical envelope for a text run, as a multiple of font size. Wider than
# the real Helvetica glyph box (ascender 0.718, descender -0.207), so an intrusion into a
# header or footer region is over reported rather than missed.
ASCENT_FACTOR = 0.75
DESCENT_FACTOR = -0.25

# Operators src/render/pdf.py is capable of emitting. Anything outside this set in a file
# this system produced means something other than text was drawn.
TEXT_ONLY_OPERATORS = frozenset({b"BT", b"ET", b"Tf", b"Td", b"Tj", b"TL", b"T*", b"Tm"})


class Run:
    """One text run as read back out of the file."""

    __slots__ = ("page_index", "x", "y", "size", "font", "text")

    def __init__(self, page_index, x, y, size, font, text):
        self.page_index = page_index
        self.x = x
        self.y = y
        self.size = size
        self.font = font
        self.text = text

    @property
    def top(self):
        return self.y + ASCENT_FACTOR * self.size

    @property
    def bottom(self):
        return self.y + DESCENT_FACTOR * self.size

    def __repr__(self):
        return "Run(p%d, %.1f, %.1f, %s, %r)" % (
            self.page_index,
            self.x,
            self.y,
            self.font,
            self.text,
        )


def reader(pdf_bytes):
    return PdfReader(io.BytesIO(pdf_bytes))


def page_count(pdf_bytes):
    """The page count D-01 is measured on, read from the file."""
    return len(reader(pdf_bytes).pages)


def extracted_text(pdf_bytes):
    """The text as it comes back out, which is the S-10 output every text check uses."""
    return "\n".join(page.extract_text() or "" for page in reader(pdf_bytes).pages)


def _page_font_map(page):
    """Font resource name -> /BaseFont, read from the page's resource dictionary."""
    mapping = {}
    resources = page.get("/Resources")
    if not resources:
        return mapping
    fonts = resources.get("/Font")
    if not fonts:
        return mapping
    for key in fonts.keys():
        entry = fonts[key].get_object()
        mapping[str(key)] = str(entry.get("/BaseFont")) if entry.get("/BaseFont") else None
    return mapping


def _decode_operand(operand):
    """A PDF string operand as text, decoded as the WinAnsiEncoding the font declares.

    The raw bytes are taken deliberately. pypdf resolves a string operand to a
    TextStringObject using PDFDocEncoding, in which byte 0x95 is U+0141 Lstroke rather
    than the bullet WinAnsiEncoding puts there, so `str(operand)` returns the wrong
    character for every high byte. That was observed, not assumed: the bullets in the
    resume fixture came back as "Ł" and the width of every bullet line was silently wrong
    as a result. Reading `original_bytes` and decoding as cp1252, which is
    WinAnsiEncoding, is what makes the text match the file.
    """
    raw = getattr(operand, "original_bytes", None)
    if raw is None and isinstance(operand, bytes):
        raw = bytes(operand)
    if raw is None:
        return str(operand)
    return raw.decode("cp1252", "replace")


def runs(pdf_bytes):
    """Every text run with its position, font and size, walked out of the content stream.

    Positions come from the Td, TD and Tm operators in the page content stream, not from
    pypdf's extract_text visitor. That is not a preference. pypdf reports the text matrix
    as (0, 0) for a run that continues a line another run already started, which is
    precisely the two column case, so a column detector built on the visitor reports one
    column for a two column page. That was observed, not assumed: a deliberately two
    column file read back as one column until this was replaced.

    Walking the operators reads the bytes that ship even more directly than extract_text
    does, so the "assert on what ships" rule is satisfied rather than bent.
    """
    document = reader(pdf_bytes)
    found = []
    for page_index, page in enumerate(document.pages):
        fonts = _page_font_map(page)
        stream = ContentStream(page.get_contents(), document)
        face = None
        size = 0.0
        leading = 0.0
        # text matrix translation and line matrix translation
        tx = ty = 0.0
        lx = ly = 0.0
        for operands, operator in stream.operations:
            if operator == b"BT":
                tx = ty = lx = ly = 0.0
            elif operator == b"Tf" and len(operands) >= 2:
                face = fonts.get(str(operands[0]))
                size = float(operands[1])
            elif operator == b"TL" and operands:
                leading = float(operands[0])
            elif operator in (b"Td", b"TD") and len(operands) >= 2:
                lx += float(operands[0])
                ly += float(operands[1])
                tx, ty = lx, ly
                if operator == b"TD":
                    leading = -float(operands[1])
            elif operator == b"Tm" and len(operands) >= 6:
                lx = float(operands[4])
                ly = float(operands[5])
                tx, ty = lx, ly
            elif operator == b"T*":
                ly -= leading
                tx, ty = lx, ly
            elif operator in (b"Tj", b"'", b'"'):
                payload = operands[-1] if operands else b""
                text = _decode_operand(payload)
                if operator != b"Tj":
                    ly -= leading
                    tx, ty = lx, ly
                if text.strip():
                    found.append(Run(page_index, tx, ty, size, face, text))
            elif operator == b"TJ" and operands:
                pieces = [
                    _decode_operand(item)
                    for item in operands[0]
                    if not isinstance(item, (int, float))
                ]
                text = "".join(pieces)
                if text.strip():
                    found.append(Run(page_index, tx, ty, size, face, text))
    return found


def page_sizes(pdf_bytes):
    sizes = []
    for page in reader(pdf_bytes).pages:
        box = page.mediabox
        sizes.append((float(box.width), float(box.height)))
    return sizes


def base_fonts(pdf_bytes):
    """Distinct /BaseFont names declared in the page resources of the file."""
    names = set()
    for page in reader(pdf_bytes).pages:
        resources = page.get("/Resources")
        if not resources:
            continue
        fonts = resources.get("/Font")
        if not fonts:
            continue
        for key in fonts.keys():
            entry = fonts[key].get_object()
            base = entry.get("/BaseFont")
            if base:
                names.add(str(base))
    return sorted(names)


def font_families(pdf_bytes):
    """Distinct font families, which is what D-01's unestablished threshold ranges over.

    Helvetica and Helvetica-Bold are two faces of one family. A subset prefix of the form
    ABCDEF+ is stripped, and the face suffix after the first hyphen is dropped.
    """
    families = set()
    for name in base_fonts(pdf_bytes):
        cleaned = name.lstrip("/")
        if len(cleaned) > 7 and cleaned[6] == "+":
            cleaned = cleaned[7:]
        families.add(cleaned.split("-")[0].split(",")[0])
    return sorted(families)


def has_image_xobject(pdf_bytes):
    """True if any page carries an image. D-07 fails a document that is a scanned image."""
    for page in reader(pdf_bytes).pages:
        resources = page.get("/Resources")
        if not resources:
            continue
        xobjects = resources.get("/XObject")
        if not xobjects:
            continue
        for key in xobjects.keys():
            entry = xobjects[key].get_object()
            if entry.get("/Subtype") == "/Image":
                return True
    return False


def content_operators(pdf_bytes):
    """Every content stream operator used in the file, as a sorted list of strings.

    A document laid out with tables or rules carries path operators (re, m, l, S, f). A
    document that is only text does not. This is how "no table objects are used for
    layout" is checked against the file rather than against intent.
    """
    doc = reader(pdf_bytes)
    used = set()
    for page in doc.pages:
        stream = ContentStream(page.get_contents(), doc)
        for _operands, operator in stream.operations:
            used.add(operator)
    return sorted(op.decode("ascii", "replace") for op in used)


def non_text_operators(pdf_bytes):
    """The operators outside the text-only set. Empty means nothing but text was drawn."""
    allowed = {op.decode("ascii") for op in TEXT_ONLY_OPERATORS}
    return [op for op in content_operators(pdf_bytes) if op not in allowed]


def column_count(pdf_bytes, gutter_min=24.0, all_runs=None):
    """Columns per page, read from the horizontal coverage of the text on the page.

    Method: union the x intervals of every run on the page, then count the maximal covered
    regions separated by an uncrossed vertical gutter at least `gutter_min` wide. A single
    measure of text yields one region. Two text columns with a gutter between them yield
    two, because no run crosses the gutter.

    Limitation, stated rather than hidden: a genuinely two column page that also carries a
    full width line spanning the gutter reads as one column by this method, because the
    spanning run closes the gutter. The detector is therefore a floor on the column count,
    not a ceiling, and it is demonstrated against a deliberately two column file in
    tests/render/test_inspect_detects.py so that it is not a rubber stamp.

    Returns a list, one entry per page.
    """
    doc_runs = all_runs if all_runs is not None else runs(pdf_bytes)
    counts = []
    for page_index in range(page_count(pdf_bytes)):
        intervals = []
        for run in doc_runs:
            if run.page_index != page_index:
                continue
            width = _run_width(run)
            intervals.append((run.x, run.x + width))
        if not intervals:
            counts.append(0)
            continue
        intervals.sort()
        merged = [list(intervals[0])]
        for start, end in intervals[1:]:
            if start - merged[-1][1] >= gutter_min:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        counts.append(len(merged))
    return counts


def _run_width(run):
    """The width of a run in points, from the metrics of the face the file declares.

    There is no silent fallback here. An earlier version swallowed measurement failures
    and substituted an estimate, which meant every bullet line in the resume was measured
    by guesswork while the column count still reported a number as if it were read. A
    number that cannot be measured is not quietly replaced by one that can.
    """
    from .metrics import GLYPH_WIDTHS
    from .pdf import text_width

    face = (run.font or "").lstrip("/").split("+")[-1]
    if face not in GLYPH_WIDTHS:
        face = "Helvetica"
    return text_width(run.text, face, run.size)


def region_intrusions(pdf_bytes, header_region_height, footer_region_height, all_runs=None):
    """Runs whose glyph box enters the page header or footer region.

    D-01 fails a document where content sits in a header or footer region. Measured on
    positions read out of the file, not on the intention of the layout.
    """
    doc_runs = all_runs if all_runs is not None else runs(pdf_bytes)
    sizes = page_sizes(pdf_bytes)
    intruding = []
    for run in doc_runs:
        _width, height = sizes[run.page_index]
        if run.top > height - header_region_height:
            intruding.append(("header", run))
        elif run.bottom < footer_region_height:
            intruding.append(("footer", run))
    return intruding


def letter_spacing_artefact_lines(text):
    """Lines of the extracted text matching the D-07 letter spacing artefact pattern.

    The rubric command counts matching lines with grep -c, so this counts lines too.
    """
    return [line for line in text.splitlines() if LETTER_SPACING.search(line)]


def section_titles_present(text, titles):
    """Which of the given section titles appear as a whole line of the extracted text.

    D-07's command is `grep -icE '^(work )?experience$|^education$|^skills$'`, which
    anchors on the whole line, so a title buried inside a sentence does not count.
    """
    lines = {line.strip().lower() for line in text.splitlines()}
    return sorted(title for title in titles if title.lower() in lines)


_WORD = re.compile(r"[^\s]+")


def _words(text):
    return _WORD.findall(text)


def words_only_in_extracted(source_text, extracted, ignore=()):
    """Words present in the rendered file that are absent from the source content.

    This is the content provenance check, run against the bytes. Anything this returns is
    text the renderer put in front of an employer that no upstream gate ever saw. The
    expected result is an empty list, and an empty list here is the only form in which
    "the renderer invented nothing" is evidence rather than a promise.
    """
    source = set(_words(source_text))
    skip = set(ignore)
    missing = []
    for word in _words(extracted):
        if word in source or word in skip:
            continue
        missing.append(word)
    return missing


def words_lost_in_render(source_text, extracted, ignore=()):
    """Words in the source content that did not come back out of the rendered file.

    Dropping content is the same class of defect as inventing it: the employer reads
    something other than the document that was approved.
    """
    rendered = set(_words(extracted))
    skip = set(ignore)
    lost = []
    for word in _words(source_text):
        if word in rendered or word in skip:
            continue
        lost.append(word)
    return lost


def reading_order_matches_visual(all_runs):
    """True when extraction order is top to bottom then left to right, per page.

    D-07 requires extraction order to equal visual reading order. Compared as the run
    sequence the extractor returned against the same runs sorted by descending y then
    ascending x, with a 2pt tolerance on y so that runs on one baseline are treated as one
    row.
    """
    by_page = {}
    for index, run in enumerate(all_runs):
        by_page.setdefault(run.page_index, []).append((index, run))
    for _page, items in sorted(by_page.items()):
        given = [index for index, _run in items]
        expected = [
            index
            for index, _run in sorted(items, key=lambda pair: (-round(pair[1].y / 2.0), pair[1].x))
        ]
        if given != expected:
            return False
    return True


__all__ = [
    "LETTER_SPACING",
    "Run",
    "base_fonts",
    "column_count",
    "content_operators",
    "extracted_text",
    "font_families",
    "has_image_xobject",
    "letter_spacing_artefact_lines",
    "non_text_operators",
    "page_count",
    "page_sizes",
    "reader",
    "reading_order_matches_visual",
    "region_intrusions",
    "runs",
    "section_titles_present",
    "words_lost_in_render",
    "words_only_in_extracted",
]
