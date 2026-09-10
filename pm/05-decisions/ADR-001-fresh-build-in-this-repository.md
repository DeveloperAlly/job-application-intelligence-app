ACCEPTED

# ADR-001: Career OS is built fresh in this repository

CONTEXT
Step 1 EXISTS established that a resume renderer, a populated career data bank and two editor
codebases already exist on this machine (resume-system, resume-editor-v0, plus at least six
predecessor and backup copies), while this repository holds 0 lines of product code, verified by
`git grep -il -E 'resume|cover.letter|tailor|job.ad|render'` over all tracked code returning no hits.
resume-system's tailoring script declares itself a stub with the LLM call left as a TODO, and
resume-system is under a code freeze. Three of the seven options on the roster (2, 4 and 6) proposed
reusing that estate. That made the choice a decision rather than a default.

DECISION
Career OS is built greenfield in this repository. Reuse from the existing estate is per item and
never by default: an artefact may be brought in only if it is named, justified in one line as useful
to a greenfield build, and verified against its source. Owner's refinement, verbatim, 2026-09-09:
"reuse whats actually useful for a GREENFIELD app only".

REUSE ALLOWLIST, per item, nothing inherited by default
- Career facts. Imported as EvidenceRecord instances conforming to E-01 in pm/03-data-contract.md,
  each verified against its source. Facts are evidence, not code or design.
- Brand assets the owner owns outright: font files and colour values, only where she confirms they
  are her approved visual style. Assets, not layout decisions.
- Rendered PDFs from the estate, usable only as reference exemplars for scoring, never as templates
  and never as a source of layout code.
Anything not on this list requires a named justification before it crosses.

REUSE DENYLIST, absolute
- Any JavaScript, TypeScript, Python or shell source from resume-system, resume-editor-v0 or any
  predecessor or backup copy.
- Any schema, migration or data model definition from the estate.
- The editor surface, its state handling and its data flow.
- Layout implementations, templates and rendering pipelines.

ALTERNATIVES
- Option 0, do nothing. Not selected. The owner stated no reason for this option and none is invented here.
- Option 1, buy (Teal, Jobscan, Rezi, Kickresume, Careerflow). Not selected. No reason stated by the owner. Not priced, because the roster closed before the pricing pass ran.
- Option 2, build in resume-editor-v0. Killed by the owner, whose stated reason for killing the reuse options was, verbatim: "this is a fresh build not importing BAD CODE AND DESIGN FROM ELSEWHERE".
- Option 4, finish the stub in place under a lifted freeze. Killed by the owner, same stated reason. It was also the only one-way door on the roster.
- Option 5, do not automate yet and apply by hand against the rubric. Not selected. No reason stated by the owner.
- Option 6, split tailoring here and rendering in resume-editor-v0. Killed by the owner, same stated reason.

CONSEQUENCES
Makes easy: building to the contracts in pm/03-data-contract.md and pm/03-interfaces.md without
inheriting an existing shape; one repository; no cross-repo seam; no dependency on a frozen path.
Makes hard: rendering to PDF must be built rather than reused, and rendering is the one capability
that demonstrably already works elsewhere. The day-one window absorbs that cost.
Forecloses: reuse of the working renderer implementation, the existing editor surface, and the
existing schemas.
Does not foreclose: the three allowlisted classes above. The allowlist is the mechanism that keeps
"greenfield" from meaning "retype the owner's career history", and the denylist is what keeps it from
decaying into a port of the old codebase one useful file at a time.

DATE
2026-09-09, decided by Ally Haire.
