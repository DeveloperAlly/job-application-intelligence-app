"""Minimal PDF writer. Serves R-127 through seam S-10 of pm/03-interfaces.md.

Why this exists rather than a library. Nothing on this machine can write a PDF from
Python: reportlab, fpdf2, weasyprint, xhtml2pdf, borb, pikepdf and cairo are all absent
(recorded by command in the task return). ADR-001 puts the estate's layout
implementations, templates and rendering pipelines on an absolute denylist, so the
working renderer elsewhere on this machine cannot be reused, adapted or read. Nothing may
be installed. What remains is the PDF file format itself, which is writable from the
standard library, so that is what this module does.

Scope. This module places text runs at absolute positions on pages and serialises the
result. It knows nothing about resumes, sections or styles; that is src/render/layout.py
and src/render/style.py. It draws no paths, no rules, no tables and no images, which is
not an omission but the point: D-01 of pm/03-evals.md fails a document that uses table
objects for layout, and D-07 fails a document that is a scanned image. A writer that
cannot emit either cannot fail those two criteria.

Text model. Every run is emitted as one BT/ET pair with one Tf, one Td and one Tj. There
are no TJ arrays and no per character positioning anywhere in this module. That is
deliberate: D-07 fails a document if any letter spacing artefact appears in the extracted
text, and TJ arrays with tight kerning are how that artefact is normally produced. The
extraction round trip in src/render/render.py asserts the result rather than trusting it.

Fonts. The base-14 Type1 fonts, referenced by name and not embedded, with
WinAnsiEncoding. Base-14 fonts are present in every conforming reader by definition, so
nothing is lost by not embedding, and no font file is copied from anywhere.

Determinism. The same input produces byte identical output. There is no creation date and
no document identifier derived from the clock. That is what makes the poison case in this
task's acceptance able to prove a restore was exact.
"""

from .metrics import GLYPH_WIDTHS, WINANSI_ENCODING

PDF_HEADER = b"%PDF-1.7\n"

# unicode codepoint -> WinAnsi byte, inverted from the encoding table so that a
# character with no glyph in the encoding is a refusal rather than a silent drop.
_UNICODE_TO_BYTE = {}
for _code, _name in WINANSI_ENCODING.items():
    try:
        _char = bytes([_code]).decode("cp1252")
    except UnicodeDecodeError:
        continue
    _UNICODE_TO_BYTE.setdefault(_char, _code)
# cp1252 leaves 0x81, 0x8d, 0x8f, 0x90 and 0x9d undefined; those codes therefore
# never enter the map above and no character can address them.


class UnrenderableCharacter(Exception):
    """A character in the content has no glyph in WinAnsiEncoding.

    Raised rather than substituted. Substituting a character changes what the employer
    reads, and a renderer that quietly rewrites content is the failure mode the content
    provenance rule exists to prevent.
    """

    def __init__(self, character, index, context):
        super().__init__(
            "no WinAnsiEncoding glyph for %r (U+%04X) at index %d in %r"
            % (character, ord(character), index, context)
        )
        self.character = character
        self.index = index
        self.context = context


class WordTooWide(Exception):
    """A single word is wider than the line it must fit on.

    Raised rather than split. D-07 of pm/03-evals.md fails a document if any word is
    split across lines, so splitting would produce a file that scores worse than no file.
    """

    def __init__(self, word, face, size, available):
        super().__init__(
            "word %r at %s %.2fpt needs %.2fpt but only %.2fpt is available"
            % (word, face, size, text_width(word, face, size), available)
        )
        self.word = word
        self.face = face
        self.size = size
        self.available = available


def glyph_name(character):
    """The WinAnsi glyph name for a character, or None if the encoding has no glyph."""
    code = _UNICODE_TO_BYTE.get(character)
    if code is None:
        return None
    return WINANSI_ENCODING[code]


def encode_text(text, context=None):
    """Encode a string to WinAnsi bytes, refusing anything the encoding cannot carry."""
    out = bytearray()
    for index, character in enumerate(text):
        code = _UNICODE_TO_BYTE.get(character)
        if code is None:
            raise UnrenderableCharacter(character, index, context if context is not None else text)
        out.append(code)
    return bytes(out)


def text_width(text, face, size):
    """Width of a string in points, from the real font metrics.

    Every wrap decision in src/render/layout.py rests on this. Estimating it would put
    words off the right edge or split them, and D-07 fails on a split word.
    """
    widths = GLYPH_WIDTHS[face]
    total = 0
    for character in text:
        name = glyph_name(character)
        if name is None:
            raise UnrenderableCharacter(character, text.index(character), text)
        total += widths[name]
    return total * size / 1000.0


class TextRun:
    """One string, one face, one size, at one baseline position.

    x and y are PDF user space points measured from the bottom left of the page, which is
    the coordinate system the read back inspection in src/render/inspect.py reports in.
    """

    __slots__ = ("text", "face", "size", "x", "y")

    def __init__(self, text, face, size, x, y):
        if face not in GLYPH_WIDTHS:
            raise ValueError("unknown face %r, expected one of %s" % (face, sorted(GLYPH_WIDTHS)))
        self.text = text
        self.face = face
        self.size = size
        self.x = x
        self.y = y

    @property
    def width(self):
        return text_width(self.text, self.face, self.size)

    def __repr__(self):
        return "TextRun(%r, %r, %s, %.2f, %.2f)" % (self.text, self.face, self.size, self.x, self.y)


def _escape(raw):
    out = bytearray()
    for byte in raw:
        if byte in (0x28, 0x29, 0x5C):  # ( ) backslash
            out.append(0x5C)
            out.append(byte)
        elif byte < 32 or byte > 126:
            out.extend(("\\%03o" % byte).encode("ascii"))
        else:
            out.append(byte)
    return bytes(out)


def _number(value):
    """Format a coordinate. Fixed precision keeps output byte identical across runs."""
    formatted = "%.3f" % float(value)
    formatted = formatted.rstrip("0").rstrip(".")
    return formatted if formatted not in ("", "-0") else "0"


def build_content_stream(runs):
    """Serialise text runs to a page content stream.

    One BT/ET, one Tf, one Td and one Tj per run, emitted in the order given. The caller
    is responsible for giving them in visual reading order, because extraction order
    follows emission order and D-07 requires the two to agree.
    """
    parts = []
    for run in runs:
        encoded = _escape(encode_text(run.text, context=run.text))
        parts.append(
            b"BT /%s %s Tf %s %s Td (%s) Tj ET\n"
            % (
                _font_resource_name(run.face).encode("ascii"),
                _number(run.size).encode("ascii"),
                _number(run.x).encode("ascii"),
                _number(run.y).encode("ascii"),
                encoded,
            )
        )
    return b"".join(parts)


def _font_resource_name(face):
    return "F" + str(sorted(GLYPH_WIDTHS).index(face) + 1)


def write_pdf(pages, page_width, page_height, language=None, producer="Career OS renderer"):
    """Serialise pages of text runs to PDF bytes.

    `pages` is a list of lists of TextRun. Only the faces actually used are declared, so
    the font count read back out of the file is the font count the document really uses,
    which is what D-01 is measured on.
    """
    used_faces = sorted({run.face for page in pages for run in page})
    if not used_faces:
        used_faces = []

    objects = []  # list of bytes, object n is objects[n - 1]

    def add(body):
        objects.append(body)
        return len(objects)

    font_numbers = {}
    for face in used_faces:
        font_numbers[face] = add(
            b"<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>"
            % face.encode("ascii")
        )

    font_entries = b" ".join(
        b"/%s %d 0 R" % (_font_resource_name(face).encode("ascii"), font_numbers[face])
        for face in used_faces
    )
    resources = b"<< /Font << %s >> >>" % font_entries

    pages_number = add(b"PLACEHOLDER")  # patched below once kids are known
    page_numbers = []
    for runs in pages:
        stream = build_content_stream(runs)
        contents_number = add(
            b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream)
        )
        page_numbers.append(
            add(
                b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %s %s] /Resources %s "
                b"/Contents %d 0 R >>"
                % (
                    pages_number,
                    _number(page_width).encode("ascii"),
                    _number(page_height).encode("ascii"),
                    resources,
                    contents_number,
                )
            )
        )

    kids = b" ".join(b"%d 0 R" % n for n in page_numbers)
    objects[pages_number - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        kids,
        len(page_numbers),
    )

    catalog_body = b"<< /Type /Catalog /Pages %d 0 R" % pages_number
    if language:
        catalog_body += b" /Lang (%s)" % _escape(encode_text(language))
    catalog_body += b" >>"
    catalog_number = add(catalog_body)

    info_number = add(b"<< /Producer (%s) >>" % _escape(encode_text(producer)))

    out = bytearray(PDF_HEADER)
    offsets = {}
    for index, body in enumerate(objects, start=1):
        offsets[index] = len(out)
        out += b"%d 0 obj\n" % index
        out += body
        out += b"\nendobj\n"

    xref_offset = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for index in range(1, len(objects) + 1):
        out += b"%010d 00000 n \n" % offsets[index]
    out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        catalog_number,
        info_number,
        xref_offset,
    )
    return bytes(out)


__all__ = [
    "TextRun",
    "UnrenderableCharacter",
    "WordTooWide",
    "build_content_stream",
    "encode_text",
    "glyph_name",
    "text_width",
    "write_pdf",
]
