"""Block model, wrapping and pagination. Serves R-127 through seam S-10.

This module turns document content into positioned text runs. It changes no word of what
it is given.

That last sentence is the whole design constraint. Content that appears in a rendered PDF
and not in the source document is invisible to every upstream gate and reaches an
employer, so this module never supplies, completes, summarises, shortens or improves
anything. Where content will not fit it raises. Where a character cannot be encoded it
raises. It has no fallback text, no placeholder, no ellipsis and no truncation anywhere,
and src/render/render.py asserts the no invented content property against the extracted
bytes afterwards rather than trusting this note.

THE BLOCK CONVENTION, which is this lane's choice and the composers' to conform to.
The composer seams S-06 and S-07 do not exist yet, so the shape of `document_content` was
not settled anywhere this lane could read. Rendering takes either:

  1. `{"blocks": [{"kind": ..., "text": ...}, ...]}`, the explicit form, where kind is one
     of name, contact, heading, role_title, role_meta, paragraph, bullet; or
  2. a plain string, which is E-08's `body_text` field, classified by the rules in
     `blocks_from_body_text` below.

Form 1 is what a composer should emit. Form 2 exists because E-08 stores only
`body_text`, so a document that has been through the store and back is a string. GAP,
reported and not worked around: a role title cannot be told from a paragraph in plain
text without inferring, so under form 2 no line is bolded as a role title and D-01's
"every role entry begins with a bold title line" fails. Guessing which lines are role
titles would be the renderer deciding what the document says, so it does not guess.
"""

import re

from .pdf import TextRun, WordTooWide, text_width

BLOCK_KINDS = ("name", "contact", "heading", "role_title", "role_meta", "paragraph", "bullet")

# Section titles the ATS vendor documentation quoted in pm/03-evals.md D-07 calls typical,
# plus the ones a senior technical resume in this estate's scope actually carries. Matching
# is on the whole stripped line, case insensitively. A line that merely contains one of
# these words is not a heading.
STANDARD_SECTION_TITLES = frozenset(
    {
        "experience",
        "work experience",
        "professional experience",
        "education",
        "skills",
        "personal details",
        "contact",
        "summary",
        "profile",
        "projects",
        "publications",
        "talks",
        "speaking",
        "certifications",
        "awards",
        "open source",
    }
)

_BULLET_LINE = re.compile(r"^\s*[-*•·]\s+(?P<text>\S.*)$")


class ContentRefused(Exception):
    """The content cannot be rendered as given, and altering it is not an option."""

    def __init__(self, message, detail=None):
        super().__init__(message)
        self.detail = detail


class Block:
    __slots__ = ("kind", "text")

    def __init__(self, kind, text):
        if kind not in BLOCK_KINDS:
            raise ValueError("unknown block kind %r, expected one of %s" % (kind, BLOCK_KINDS))
        self.kind = kind
        self.text = text

    def __repr__(self):
        return "Block(%r, %r)" % (self.kind, self.text)


def blocks_from_body_text(body_text):
    """Classify E-08 body_text into blocks without changing a word.

    The rules, in order, applied to each line:

      - a blank line ends the preceding block and is otherwise discarded;
      - a line beginning with a hyphen, asterisk, bullet or middle dot followed by
        whitespace is a bullet, and only that leading marker is removed, because the
        renderer draws its own marker;
      - a line whose stripped text equals a standard section title, case insensitively,
        is a heading;
      - the first non blank line of the document is the name;
      - a line before the first heading that is not the name is contact;
      - everything else is a paragraph.

    No line is dropped, no line is merged with another, and no word is altered. The only
    text removed anywhere is a leading bullet marker, which is re-drawn by the layout.
    """
    blocks = []
    seen_heading = False
    seen_first_line = False
    for raw in body_text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        bullet = _BULLET_LINE.match(raw)
        if bullet:
            blocks.append(Block("bullet", bullet.group("text").strip()))
            continue
        if stripped.lower() in STANDARD_SECTION_TITLES:
            seen_heading = True
            seen_first_line = True
            blocks.append(Block("heading", stripped))
            continue
        if not seen_first_line:
            seen_first_line = True
            blocks.append(Block("name", stripped))
            continue
        if not seen_heading:
            blocks.append(Block("contact", stripped))
            continue
        blocks.append(Block("paragraph", stripped))
    return blocks


def normalise_content(document_content):
    """Accept either explicit blocks or E-08 body_text, and return a list of Block.

    Raises ContentRefused rather than inventing a document out of nothing. An empty
    document is refused: a zero byte PDF sent to an employer is worse than a failed render.
    """
    if isinstance(document_content, str):
        blocks = blocks_from_body_text(document_content)
    elif isinstance(document_content, dict) and "blocks" in document_content:
        blocks = []
        for index, item in enumerate(document_content["blocks"]):
            if isinstance(item, Block):
                blocks.append(item)
                continue
            kind = item.get("kind")
            text = item.get("text")
            if kind not in BLOCK_KINDS:
                raise ContentRefused(
                    "block %d has kind %r, expected one of %s" % (index, kind, BLOCK_KINDS),
                    detail={"index": index, "kind": kind},
                )
            if not isinstance(text, str) or not text.strip():
                raise ContentRefused(
                    "block %d of kind %r has no text; the renderer supplies none"
                    % (index, kind),
                    detail={"index": index, "kind": kind},
                )
            blocks.append(Block(kind, text.strip()))
    elif isinstance(document_content, dict) and "body_text" in document_content:
        blocks = blocks_from_body_text(document_content["body_text"])
    else:
        raise ContentRefused(
            "document_content must be a string, a dict with blocks, or a dict with "
            "body_text; got %s" % type(document_content).__name__
        )
    if not blocks:
        raise ContentRefused("document_content is empty; the renderer has nothing to render")
    return blocks


def wrap(text, face, size, first_width, rest_width):
    """Break text into lines that fit, breaking only at existing spaces.

    Never hyphenates and never splits a word, because D-07 of pm/03-evals.md fails a
    document if any word is split across lines. A word that cannot fit raises WordTooWide.
    """
    words = text.split()
    if not words:
        return []
    lines = []
    current = ""
    available = first_width
    for word in words:
        candidate = word if not current else current + " " + word
        if text_width(candidate, face, size) <= available:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
            available = rest_width
        if text_width(word, face, size) > available:
            raise WordTooWide(word, face, size, available)
        current = word
    if current:
        lines.append(current)
    return lines


class LaidOutDocument:
    def __init__(self, pages, spec):
        self.pages = pages
        self.spec = spec

    @property
    def page_count(self):
        return len(self.pages)


def lay_out(blocks, spec):
    """Place blocks into pages of TextRun, in the order given.

    Order is never changed. D-09 measures whether the strongest material is at the top of
    page one; that is the composer's decision, and a renderer that reordered blocks to
    improve a score would be scoring a document nobody wrote.

    A heading or a role title that would be left alone at the foot of a page moves to the
    next page with the block that follows it. That is typography, not content: no text is
    changed and nothing is dropped.
    """
    pages = []
    runs = []
    y = spec.content_top
    pending_keep = []

    def flush_page():
        nonlocal runs, y
        if runs:
            pages.append(runs)
        runs = []
        y = spec.content_top

    def room_for(height):
        return y - height >= spec.content_bottom

    for index, block in enumerate(blocks):
        block_spec = spec.block(block.kind)
        marker = block_spec.marker
        marker_width = text_width(marker, block_spec.face, block_spec.size) if marker else 0.0
        left = spec.content_left + block_spec.indent
        first_width = spec.content_width - block_spec.indent - marker_width
        rest_width = first_width
        lines = wrap(block.text, block_spec.face, block_spec.size, first_width, rest_width)
        if not lines:
            continue

        space_before = block_spec.space_before if (runs or pages) else 0.0
        if not runs:
            space_before = 0.0
        block_height = space_before + block_spec.leading * len(lines)

        # keep a heading or role title with at least one line of what follows it
        keep_with_next = block.kind in ("heading", "role_title", "name")
        needed = block_height
        if keep_with_next and index + 1 < len(blocks):
            following = spec.block(blocks[index + 1].kind)
            needed += following.space_before + following.leading

        if runs and not room_for(needed):
            flush_page()
            space_before = 0.0
            block_height = block_spec.leading * len(lines)

        y -= space_before
        for line_index, line in enumerate(lines):
            if runs and not room_for(block_spec.leading):
                flush_page()
            y -= block_spec.leading
            baseline = y + block_spec.leading * 0.22  # sit the baseline inside its line box
            if line_index == 0 and marker:
                runs.append(TextRun(marker + line, block_spec.face, block_spec.size, left, baseline))
            elif marker:
                runs.append(
                    TextRun(line, block_spec.face, block_spec.size, left + marker_width, baseline)
                )
            else:
                runs.append(TextRun(line, block_spec.face, block_spec.size, left, baseline))
        pending_keep = []

    flush_page()
    if not pages:
        raise ContentRefused("layout produced no pages")
    return LaidOutDocument(pages, spec)


__all__ = [
    "BLOCK_KINDS",
    "Block",
    "ContentRefused",
    "LaidOutDocument",
    "STANDARD_SECTION_TITLES",
    "blocks_from_body_text",
    "lay_out",
    "normalise_content",
    "wrap",
]
