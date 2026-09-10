"""E-05 VisualStyle records and the layout specification behind them. Serves R-127.

Two separate things live here, and the split is forced by the data contract rather than
chosen.

The record. E-05 in pm/03-data-contract.md gives VisualStyle exactly four fields: id,
name, approved and approved_at. `VisualStyle` stores exactly those four and nothing else,
because the R-127 acceptance command and INV-13 both read `approved` off this record and
an invented schema would put this lane's storage out of step with the contract every
other lane reads.

The specification. E-05 has no field that can carry a margin, a font size or a page size,
so the geometry a style actually is cannot be stored under the current contract. It lives
here in code as `StyleSpec`, bound to a record by id. GAP, reported and not worked
around: two visual styles cannot differ without a code change, and the stored record
carries no evidence of what it looked like, so a style approved today and a style
approved after an edit to this file are indistinguishable in the store.

APPROVAL. Nothing in this module ever sets `approved` to true. R-127 says "the user's
approved visual style", and pm/03-interfaces.md S-10 says the render refuses a style that
is not the approved one. Approval is the owner's act. `CAREER_OS_DEFAULT` below is
written with approved false and stays that way until she says otherwise.

Where the style came from. ADR-001 denylists the estate's layout implementations,
templates and rendering pipelines, and allowlists estate PDFs only as reference exemplars
for scoring, never as templates. No estate file was opened. Every number in
`CAREER_OS_DEFAULT` is derived below from a criterion in pm/03-evals.md or is marked as a
choice with no evidence behind it.
"""

import glob
import json
import os

COLLECTION = "visual_styles"
DEFAULT_STORE = "./store"

# A4. Choice, not evidence: no fetched source in pm/03-evals.md specifies a page size.
# A4 rather than US Letter because the owner applies from Australia.
A4_WIDTH = 595.276
A4_HEIGHT = 841.890


class StyleNotFound(Exception):
    """No VisualStyle with that id is stored."""


class SpecNotFound(Exception):
    """A stored VisualStyle has no layout specification in this module.

    This is the shape of the gap above made loud. A record whose geometry is unknown
    cannot be rendered in, and guessing one would mean the file does not look like the
    style the owner approved.
    """


class BlockSpec:
    """Typography for one block kind. Points throughout."""

    __slots__ = ("face", "size", "leading", "space_before", "indent", "marker")

    def __init__(self, face, size, leading, space_before, indent=0.0, marker=""):
        self.face = face
        self.size = size
        self.leading = leading
        self.space_before = space_before
        self.indent = indent
        self.marker = marker


class StyleSpec:
    """The geometry and typography a VisualStyle id resolves to."""

    def __init__(
        self,
        page_width,
        page_height,
        margin_left,
        margin_right,
        margin_top,
        margin_bottom,
        header_region_height,
        footer_region_height,
        columns,
        blocks,
        default_block,
        language,
        max_pages,
        max_font_families,
        font_family,
    ):
        self.page_width = page_width
        self.page_height = page_height
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.header_region_height = header_region_height
        self.footer_region_height = footer_region_height
        self.columns = columns
        self.blocks = blocks
        self.default_block = default_block
        self.language = language
        self.max_pages = max_pages
        self.max_font_families = max_font_families
        self.font_family = font_family

    @property
    def content_left(self):
        return self.margin_left

    @property
    def content_right(self):
        return self.page_width - self.margin_right

    @property
    def content_width(self):
        return self.content_right - self.content_left

    @property
    def content_top(self):
        return self.page_height - self.margin_top

    @property
    def content_bottom(self):
        return self.margin_bottom

    def block(self, kind):
        return self.blocks.get(kind, self.default_block)


# The default style, derived criterion by criterion.
#
# D-01 "the body is a single text column"          -> columns = 1, one full width measure.
# D-01 "no content sits in a page header or footer
#       region"                                    -> header_region_height and
#                                                     footer_region_height are 36pt and
#                                                     the margins are 54pt, so no run can
#                                                     land in either band. Nothing is
#                                                     drawn there at all: no page number,
#                                                     no running header, no rule.
# D-01 "every role entry begins with a bold title
#       line"                                      -> the role_title block is the only
#                                                     block below the name that is bold,
#                                                     so a role entry is visually the
#                                                     bold line that opens it.
# D-01 "no table objects are used for layout"      -> src/render/pdf.py cannot emit one.
# D-01 "at most 2 pages"                           -> max_pages = 2. This renderer does
#                                                     not truncate to reach it; it reports
#                                                     the page count it produced, because
#                                                     dropping content to hit a threshold
#                                                     is the same defect as inventing it.
# D-01 font families, threshold unestablished      -> max_font_families = 2 is MY CHOICE
#                                                     and not evidence. The fetched
#                                                     evidence says only "a clear font".
#                                                     The style itself uses one family,
#                                                     Helvetica, in two faces; the ceiling
#                                                     of 2 leaves room for a second family
#                                                     if the owner wants one, and fails
#                                                     the ransom note case.
# D-07 section titles must survive extraction      -> headings are ordinary text runs in
#                                                     the flow, not header regions, not
#                                                     images and not letterspaced, and the
#                                                     titles are rendered in the exact
#                                                     case they were given, because
#                                                     uppercasing them would be the
#                                                     renderer altering content.
# D-07 no letter spacing artefact, no split word   -> one Tj per line, no TJ arrays, and
#                                                     wrapping refuses rather than splits.
# D-09 front loading                               -> the renderer preserves the order it
#                                                     is given and never reorders. Whether
#                                                     the strongest material is first is
#                                                     the composer's job, not this one's.
#
# Sizes and spacing below are a typographic choice within those constraints. They rest on
# no fetched source and are not presented as evidence.
_BASE_BLOCKS = {
    "name": BlockSpec("Helvetica-Bold", 17.0, 20.0, 0.0),
    "contact": BlockSpec("Helvetica", 9.5, 12.0, 3.0),
    "heading": BlockSpec("Helvetica-Bold", 11.5, 14.0, 13.0),
    "role_title": BlockSpec("Helvetica-Bold", 10.5, 13.0, 7.5),
    "role_meta": BlockSpec("Helvetica", 9.5, 12.0, 1.0),
    "paragraph": BlockSpec("Helvetica", 10.0, 13.2, 6.0),
    "bullet": BlockSpec("Helvetica", 10.0, 13.2, 2.5, indent=4.0, marker="• "),
}

CAREER_OS_DEFAULT_ID = "vs_career_os_default_v1"

SPECS = {
    CAREER_OS_DEFAULT_ID: StyleSpec(
        page_width=A4_WIDTH,
        page_height=A4_HEIGHT,
        margin_left=54.0,
        margin_right=54.0,
        margin_top=54.0,
        margin_bottom=54.0,
        header_region_height=36.0,
        footer_region_height=36.0,
        columns=1,
        blocks=_BASE_BLOCKS,
        default_block=_BASE_BLOCKS["paragraph"],
        language="en-AU",
        max_pages=2,
        max_font_families=2,
        font_family="Helvetica",
    )
}


class VisualStyle:
    """E-05, exactly the four contract fields."""

    FIELDS = ("id", "name", "approved", "approved_at")

    def __init__(self, id, name, approved=False, approved_at=None):
        self.id = id
        self.name = name
        self.approved = bool(approved)
        self.approved_at = approved_at

    @classmethod
    def from_dict(cls, payload):
        return cls(
            id=payload.get("id"),
            name=payload.get("name"),
            approved=payload.get("approved", False),
            approved_at=payload.get("approved_at"),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "approved": self.approved,
            "approved_at": self.approved_at,
        }

    @property
    def spec(self):
        if self.id not in SPECS:
            raise SpecNotFound(
                "visual style %r has no layout specification in src/render/style.py; "
                "E-05 cannot store geometry, so a style with no spec cannot be rendered in"
                % (self.id,)
            )
        return SPECS[self.id]

    def __repr__(self):
        return "VisualStyle(%r, approved=%r)" % (self.id, self.approved)


def store_root(explicit=None):
    """Resolve the store root: an explicit argument, else CAREER_OS_STORE, else ./store.

    Same resolution as src/evidence/store.py, which is the shape the acceptance commands
    in pm/03-requirements.md read.
    """
    if explicit is not None:
        return explicit
    return os.environ.get("CAREER_OS_STORE") or DEFAULT_STORE


class StyleStore:
    """Reads and writes E-05 records under `<store>/visual_styles/<id>.json`."""

    def __init__(self, root=None):
        self.root = store_root(root)

    def collection_dir(self):
        return os.path.join(self.root, COLLECTION)

    def path(self, style_id):
        return os.path.join(self.collection_dir(), style_id + ".json")

    def all_styles(self):
        """Every stored style, read back off disk rather than from memory."""
        pattern = os.path.join(self.collection_dir(), "*.json")
        styles = []
        for path in sorted(glob.glob(pattern)):
            with open(path, "r", encoding="utf-8") as handle:
                styles.append(VisualStyle.from_dict(json.load(handle)))
        return styles

    def get(self, style_id):
        path = self.path(style_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return VisualStyle.from_dict(json.load(handle))

    def approved_styles(self):
        """The styles whose approved is true. Possibly empty, which is a real state.

        pm/03-interfaces.md S-10 records the case where no style has ever been approved:
        every render is refused and nothing reaches scoring or approval. An empty result
        here is that state, not an error to be worked around.
        """
        return [style for style in self.all_styles() if style.approved]

    def write(self, style, overwrite=False):
        """Store one E-05 record. Never sets approved on the owner's behalf."""
        if not style.id:
            raise ValueError("a VisualStyle needs an id")
        path = self.path(style.id)
        if os.path.exists(path) and not overwrite:
            raise ValueError("visual style %r already stored" % style.id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(style.to_dict(), handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        return style.id


def default_style(approved=False):
    """The style defined in this module, as an unapproved E-05 record by default.

    `approved` is a parameter only so that a test can build an approved style in its own
    temporary store. Nothing in the product calls it with true.
    """
    return VisualStyle(
        id=CAREER_OS_DEFAULT_ID,
        name="Career OS default, single column A4",
        approved=approved,
        approved_at=None,
    )


__all__ = [
    "A4_HEIGHT",
    "A4_WIDTH",
    "BlockSpec",
    "CAREER_OS_DEFAULT_ID",
    "COLLECTION",
    "SPECS",
    "SpecNotFound",
    "StyleNotFound",
    "StyleSpec",
    "StyleStore",
    "VisualStyle",
    "default_style",
    "store_root",
]
