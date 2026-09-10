"""The controlled skill vocabulary and the matcher over it.

Why a vocabulary rather than free noun phrase extraction: R-121 forbids
inferring a value, and the concrete test the owner set is that a skill term
appearing in the extracted fields but nowhere in the source text was invented.
A vocabulary decides which substrings of the posting count as skills. It never
supplies content: every emitted term is a slice of source_text taken by offset,
so the emitted string cannot differ from the posting even by case.

The cost of this choice, stated rather than hidden: recall is bounded by the
vocabulary. A posting naming a skill that is not listed here yields a miss, and a
miss is invisible to the R-121 command, which only checks that what was emitted
occurs in the text. This is the deterministic counterpart of the F-02 failure in
pm/05-architecture.md and is named in the task return.

Case rule. An entry written entirely in capitals (ignoring digits and
separators) is matched case sensitively, because matching REST or API case
insensitively would fire on the ordinary words "rest" and "api" inside prose.
Every other entry is matched case insensitively.

Overlap rule. At any character position the longest matching entry wins, and
matches never overlap, so "B2B SaaS/API" yields "B2B SaaS" and "API" rather than
"B2B SaaS", "SaaS" and "API".
"""

import re

# Grouped only for readability. The matcher sees one flat set.
ROLES_AND_FUNCTIONS = (
    "Sales Engineer",
    "Customer Engineer",
    "Solutions Engineer",
    "Solutions Architect",
    "Software Engineer",
    "Site Reliability Engineer",
    "Product Manager",
    "Developer Advocate",
    "Developer Relations",
    "Technical Account Manager",
    "sales engineering",
    "solutions architecture",
    "technical discovery",
    "proof-of-concept",
    "pre-sales",
    "presales",
    "customer success",
)

PLATFORMS_AND_TECHNOLOGY = (
    "API",
    "APIs",
    "REST",
    "RESTful",
    "GraphQL",
    "gRPC",
    "SDK",
    "SDKs",
    "webhooks",
    "SQL",
    "NoSQL",
    "PostgreSQL",
    "Postgres",
    "MySQL",
    "Redis",
    "Kafka",
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "Ruby",
    "Rust",
    "Kubernetes",
    "Docker",
    "Terraform",
    "AWS",
    "GCP",
    "Google Cloud",
    "Azure",
    "Linux",
    "CI/CD",
    "cloud infrastructure",
    "software development",
    "distributed systems",
    "microservices",
    "data residency",
    "observability",
    "system design",
)

ARTIFICIAL_INTELLIGENCE = (
    "AI/ML",
    "ML",
    "machine learning",
    "LLM",
    "LLMs",
    "large language models",
    "deep learning",
    "MLOps",
    "RAG",
    "fine-tuning",
    "prompt engineering",
    "model evaluation",
    "NLP",
    "computer vision",
)

BUSINESS = (
    "B2B SaaS",
    "SaaS",
    "B2B",
    "enterprise sales",
    "account management",
    "QBRs",
    "SLAs",
    "compliance",
    "SOC 2",
    "GDPR",
    "contract negotiations",
    "competitive positioning",
    "stakeholder management",
    "product roadmap",
)

COMMUNICATION = (
    "presentation skills",
    "communication skills",
    "problem-solving",
    "problem solving",
    "customer-facing",
    "public speaking",
    "technical writing",
)

TERMS = (
    ROLES_AND_FUNCTIONS
    + PLATFORMS_AND_TECHNOLOGY
    + ARTIFICIAL_INTELLIGENCE
    + BUSINESS
    + COMMUNICATION
)


def _is_acronym(term):
    letters = [c for c in term if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def _pattern_for(term):
    body = re.escape(term)
    prefix = r"\b" if term[0].isalnum() else ""
    suffix = r"\b" if term[-1].isalnum() else ""
    flags = 0 if _is_acronym(term) else re.IGNORECASE
    return re.compile(prefix + body + suffix, flags)


_COMPILED = tuple(
    sorted(
        ((term, _pattern_for(term)) for term in TERMS),
        key=lambda pair: (-len(pair[0]), pair[0]),
    )
)


def find(haystack, start=0, end=None, source=None):
    """Every vocabulary term occurring in haystack[start:end], longest match first.

    `haystack` is the masked working copy. `source` is the real source text, and
    the emitted term is sliced from it by offset, never from the vocabulary, so
    a quarantined region cannot contribute a term and the casing is always the
    posting's own.

    Returns a list of dicts: term, start, end, vocabulary_entry.
    """
    if end is None:
        end = len(haystack)
    if source is None:
        source = haystack
    taken = [False] * len(haystack)
    hits = []
    for term, pattern in _COMPILED:
        for match in pattern.finditer(haystack, start, end):
            if any(taken[match.start():match.end()]):
                continue
            for index in range(match.start(), match.end()):
                taken[index] = True
            hits.append(
                {
                    "term": source[match.start():match.end()],
                    "start": match.start(),
                    "end": match.end(),
                    "vocabulary_entry": term,
                }
            )
    hits.sort(key=lambda hit: hit["start"])
    return hits
