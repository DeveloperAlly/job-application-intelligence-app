"""Getting the posting text for a URL submission, and saying where it came from.

S-01 names four ways a URL submission can fail to produce an advertisement: the
host does not resolve, the response is not a success, the fetch times out, or the
address returns a login wall, a consent interstitial or an empty client side
shell. The first three raise RetrievalFailed carrying the failure kind and the
status code, so a dead link is distinguishable from a paywall.

The fourth is a deliberate deviation from S-01, recorded here rather than hidden.
S-01 says the defensible behaviour for a shell is to store what was retrieved and
let extraction mark every field unknown. F-01 in pm/05-architecture.md then names
exactly that as the way this component fails, and the owner's instruction for this
task is that a page shell must not be stored as if it were the advertisement. So a
retrieval whose posting text is shorter than MINIMUM_POSTING_TEXT_CHARS is refused
and nothing is stored. That threshold is a chosen number, not one any requirement
supplies, and it is the only heuristic in this package.

Two retrieval strategies exist. Which one runs is decided by the host, never by
the content.

- ASHBY. jobs.ashbyhq.com renders through JavaScript, so the page body carries no
  posting text a reader would recognise. The organisation's public posting API is
  fetched instead and the posting's own descriptionPlain field is taken verbatim.
- GENERIC. Any other host: the response body is fetched, and the posting text is
  the body itself for text/plain, or the visible text of the document for HTML.
  The undecoded body is retained beside the record either way.
"""

import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

USER_AGENT = "career-os-intake/1.0 (+job advertisement intake)"
TIMEOUT_SECONDS = 20
MINIMUM_POSTING_TEXT_CHARS = 200

ASHBY_HOSTS = ("jobs.ashbyhq.com",)
ASHBY_BOARD_API = "https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true"
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


class RetrievalFailed(Exception):
    """A URL did not yield a posting. Nothing is stored and no identifier is issued.

    kind is one of: unreachable, timeout, http_error, malformed_response,
    posting_not_found, posting_text_absent, client_side_shell.
    status is the HTTP status code when there was one, otherwise None.
    """

    def __init__(self, message, kind, url, status=None):
        super().__init__(message)
        self.kind = kind
        self.url = url
        self.status = status

    def as_dict(self):
        return {
            "url": self.url,
            "failure_kind": self.kind,
            "http_status": self.status,
            "detail": str(self),
        }


class Response:
    """One HTTP response, with the body kept as bytes."""

    def __init__(self, url, status, body, content_type=None):
        self.url = url
        self.status = status
        self.body = body
        self.content_type = content_type or ""


class Retrieval:
    """What a strategy produced, and the provenance of the text it produced."""

    def __init__(
        self,
        submitted_url,
        fetched_url,
        status,
        body,
        text,
        text_source,
        content_type="",
        decoded_with=None,
    ):
        self.submitted_url = submitted_url
        self.fetched_url = fetched_url
        self.status = status
        self.body = body
        self.text = text
        self.text_source = text_source
        self.content_type = content_type
        self.decoded_with = decoded_with

    @property
    def text_is_whole_body(self):
        if self.decoded_with is None:
            return False
        try:
            return self.text.encode(self.decoded_with) == self.body
        except (UnicodeEncodeError, LookupError):
            return False


def fetch_bytes(url, timeout=TIMEOUT_SECONDS):
    """The only place this package touches the network. Injectable for tests."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as handle:
            return Response(
                handle.geturl(),
                handle.status,
                handle.read(),
                handle.headers.get("Content-Type", ""),
            )
    except urllib.error.HTTPError as error:
        body = b""
        try:
            body = error.read()
        except Exception:  # noqa: BLE001 - the body is best effort on an error path
            pass
        raise RetrievalFailed(
            "response was not a success: HTTP " + str(error.code),
            "http_error",
            url,
            error.code,
        ) from error
    except socket.timeout as error:
        raise RetrievalFailed("fetch timed out", "timeout", url, None) from error
    except urllib.error.URLError as error:
        reason = getattr(error, "reason", error)
        if isinstance(reason, socket.timeout):
            raise RetrievalFailed("fetch timed out", "timeout", url, None) from error
        raise RetrievalFailed(
            "host did not resolve or refused the connection: " + str(reason),
            "unreachable",
            url,
            None,
        ) from error


def strategy_for(url):
    """ASHBY or GENERIC, decided by host alone."""
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return "ASHBY" if host in ASHBY_HOSTS else "GENERIC"


def retrieve(url, fetcher=fetch_bytes):
    """Return a Retrieval, or raise RetrievalFailed. Stores nothing."""
    if strategy_for(url) == "ASHBY":
        retrieval = _retrieve_ashby(url, fetcher)
    else:
        retrieval = _retrieve_generic(url, fetcher)
    if len(retrieval.text.strip()) < MINIMUM_POSTING_TEXT_CHARS:
        raise RetrievalFailed(
            "retrieved "
            + str(len(retrieval.text.strip()))
            + " characters of text, under the "
            + str(MINIMUM_POSTING_TEXT_CHARS)
            + " character floor: this is a shell, an interstitial or a wall, not a posting",
            "client_side_shell",
            url,
            retrieval.status,
        )
    return retrieval


def _retrieve_ashby(url, fetcher):
    org, posting_id = _split_ashby_url(url)
    if not org or not posting_id:
        raise RetrievalFailed(
            "not an Ashby posting address of the form /<organisation>/<posting id>",
            "malformed_response",
            url,
            None,
        )
    api_url = ASHBY_BOARD_API.format(org=urllib.parse.quote(org))
    response = fetcher(api_url)
    if response.status != 200:
        raise RetrievalFailed(
            "posting API returned HTTP " + str(response.status),
            "http_error",
            api_url,
            response.status,
        )
    try:
        payload = json.loads(response.body.decode("utf-8"))
        jobs = payload["jobs"]
    except (ValueError, KeyError, UnicodeDecodeError) as error:
        raise RetrievalFailed(
            "posting API response was not a job board document: " + str(error),
            "malformed_response",
            api_url,
            response.status,
        ) from error

    matches = [j for j in jobs if str(j.get("id", "")).lower() == posting_id.lower()]
    if not matches:
        raise RetrievalFailed(
            "posting " + posting_id + " is not on the " + org + " board, which lists "
            + str(len(jobs))
            + " postings",
            "posting_not_found",
            api_url,
            response.status,
        )
    text = matches[0].get("descriptionPlain") or ""
    if not text.strip():
        raise RetrievalFailed(
            "posting " + posting_id + " carries no descriptionPlain",
            "posting_text_absent",
            api_url,
            response.status,
        )
    return Retrieval(
        submitted_url=url,
        fetched_url=api_url,
        status=response.status,
        body=response.body,
        text=text,
        text_source="ashby posting-api job-board: jobs[id=" + posting_id + "].descriptionPlain, verbatim",
        content_type=response.content_type,
        decoded_with=None,
    )


def _split_ashby_url(url):
    parts = [p for p in urllib.parse.urlsplit(url).path.split("/") if p]
    if len(parts) < 2 or not _UUID.match(parts[1]):
        return None, None
    return parts[0], parts[1]


def _retrieve_generic(url, fetcher):
    response = fetcher(url)
    if response.status != 200:
        raise RetrievalFailed(
            "response was not a success: HTTP " + str(response.status),
            "http_error",
            url,
            response.status,
        )
    charset = _charset(response.content_type)
    decoded = response.body.decode(charset, errors="replace")
    if "html" in response.content_type.lower() or _looks_like_html(decoded):
        text = html_to_text(decoded)
        source = "response body, visible text of the HTML document"
        decoded_with = None
    else:
        text = decoded
        source = "response body, verbatim"
        decoded_with = charset
    return Retrieval(
        submitted_url=url,
        fetched_url=response.url or url,
        status=response.status,
        body=response.body,
        text=text,
        text_source=source,
        content_type=response.content_type,
        decoded_with=decoded_with,
    )


def _charset(content_type):
    match = re.search(r"charset=([\w\-]+)", content_type or "", re.IGNORECASE)
    if not match:
        return "utf-8"
    try:
        "".encode(match.group(1))
    except LookupError:
        return "utf-8"
    return match.group(1)


def _looks_like_html(text):
    head = text[:2048].lstrip().lower()
    return head.startswith("<!doctype html") or head.startswith("<html")


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "head"}
    BREAK = {
        "p", "div", "br", "li", "tr", "section", "article", "header", "footer",
        "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table", "blockquote",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skipping = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skipping += 1
        elif tag in self.BREAK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skipping:
            self.skipping -= 1
        elif tag in self.BREAK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skipping:
            self.parts.append(data)


def html_to_text(document):
    """Visible text of an HTML document.

    This is a normalisation: entities are resolved and markup is dropped. The
    undecoded response body is retained beside the record, so the original is not
    lost by this passing through.
    """
    parser = _TextExtractor()
    parser.feed(document)
    parser.close()
    joined = "".join(parser.parts)
    lines = [line.strip() for line in joined.splitlines()]
    kept = [line for line in lines if line]
    return "\n".join(kept)
