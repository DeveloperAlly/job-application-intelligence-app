# Architecture: Career OS

This document names the components of Career OS, the seams between them, the path one job
advertisement takes through them, and how each component fails. It follows ADR-001, which places the
build greenfield in this repository with a per item reuse allowlist and an absolute denylist, so no
component here is a port of anything in the existing estate. It chooses no library, no framework, no
storage product, no model and no host: those are step 6. Components are marked T1, T2 or T3 against
the owner's tiering, and only the T1 components are load bearing for the current build. Every
responsibility is drawn from pm/03-interfaces.md, pm/03-data-contract.md or pm/03-evals.md, and where
those files do not determine a responsibility the gap is named rather than filled.

## Components

### C-01 Advertisement intake  [T1]

Responsible for: turning one submitted address or one pasted block of text into a stored
advertisement carrying its source text unmodified.

### C-02 Advertisement extractor  [T1]

Responsible for: producing the fixed field set R-120 names, each field either a value quoted from the
source text or the literal unknown token.

### C-03 Model gateway  [T1]

Responsible for: carrying one structured request across the boundary to a language model, returning
either a response of the declared shape or a recorded malformed response.

### C-04 Evidence store  [T1]

Responsible for: admitting and serving claims about the owner's history only where each carries the
source and the date R-117 makes mandatory.

### C-05 Portfolio register  [T1]

Responsible for: holding the portfolio pieces eligible for selection, each with the address D-04
checks resolves.

### C-06 Evidence selector  [T1]

Responsible for: producing an ordered inclusion list over a closed candidate set, with one rationale
sentence for every candidate on either side of the decision.

### C-07 Resume composer  [T1]

Responsible for: producing resume content in which every claim carries the identifier of the evidence
record it came from.

### C-08 Cover letter composer  [T1]

Responsible for: producing cover letter content whose company specific sentences are named, every
claim carrying the identifier of the evidence record it came from.

### C-09 Claim traceability gate  [T1]

Responsible for: deciding whether a document version may be shown to a person, by resolving every
claim in it against a stored evidence record.

### C-10 Rubric registry  [T1]

Responsible for: holding the rubric version in force with its nine dimensions, so that a score names
the version it was taken under.

### C-11 Rubric scorer  [T1]

Responsible for: returning one verdict per rubric dimension for one document revision, measured on
the rendered artefact rather than on the source content.

### C-12 Visual style registry  [T1]

Responsible for: holding which visual style the owner has approved, so that a render asking for any
other can be refused.

### C-13 Document renderer  [T1]

Responsible for: producing the output file a person would actually send, in the one approved visual
style.

### C-14 Approval surface  [T1]

Responsible for: recording the owner's decision against one exact document version, having shown her
the rendered file, the score, the evidence behind every claim, the traceability verdict.

### C-15 Document editor  [T1]

Responsible for: turning the owner's edit into a new document revision rather than into a change to
the revision an approval could already have attached to.

### C-16 Provenance ledger  [T1]

Responsible for: holding, for every generated document version, the six values R-137 requires to
explain how that version was produced.

### C-17 Outbound gate  [T1]

Responsible for: refusing any transmission whose artefacts lack a current approval for the exact
version being carried.

### C-18 Transmission executor  [T1]

Responsible for: performing exactly the one export, upload or send that the outbound gate permitted.

### C-19 Record store  [T1]

Responsible for: durably holding every record under the entity shapes pm/03-data-contract.md defines.

### C-20 Invariant checker  [T1]

Responsible for: reporting, with its denominator, which of the thirty invariants in
pm/03-data-contract.md currently holds over the stored records.

### C-21 Settings register  [T1]

Responsible for: holding the values the owner has set, keeping an unset value distinguishable from a
defaulted one.

### C-22 Application register  [T2]

Responsible for: recording, for each application sent through this system, the five values R-132
names.

### C-23 Status surface  [T2]

Responsible for: showing the state of every application on one surface without the owner opening a
file.

### C-24 Discovery feed  [T3]

Responsible for: presenting each matching advertisement to the owner no more than once.

### C-25 Mailbox status deriver  [T3]

Responsible for: deriving an application status from an inbound message, citing the passage it was
derived from.

### C-26 Follow-up scheduler  [T3]

Responsible for: raising one action per application that has been silent for the interval the owner
set.

### C-27 Message approval register  [T3]

Responsible for: holding the single use approval that authorises one outbound message.

### C-28 Posting identity resolver  [T3]

Responsible for: deciding which stored advertisements are one posting, so that R-139's two advertisements
sharing employer, role title and overlapping source text are presented once and not twice.

### C-29 Sentence map gate  [T1]

Responsible for: refusing to let a document revision reach a person while it holds a sentence that appears
in no entry of its claim map, which is what R-143 requires and what C-09 states it cannot see.

## Seams

Every seam below is an entry of the same name in pm/03-interfaces.md. Nothing is invented here: where
this architecture needs a boundary that file does not carry, it is listed under "Boundaries with no
entry in pm/03-interfaces.md" rather than given an identifier.

- S-01 Advertisement intake: joins the owner's submission to C-01, whose write lands in C-19.
- S-02 Advertisement field extraction: joins C-02 to C-03, over the source text C-01 stored.
- S-03 Discovery feed: joins C-24 to the owner, reading the enablement flag from C-21. T3.
- S-04 Evidence record store: joins C-04 to its readers, which are C-06, C-07, C-08, C-09 and C-11.
- S-05 Evidence selection and ranking: joins C-06 to C-03, over candidates drawn from C-04 and C-05.
- S-06 Resume generation: joins C-07 to C-03, carrying the rubric reference held by C-10.
- S-07 Cover letter generation: joins C-08 to C-03, carrying the same rubric reference.
- S-08 Rubric scoring: joins C-11 to the rendered artefact C-13 produced, against the version C-10 holds.
- S-09 Claim traceability check: joins C-09 to C-04, and is what stands between C-07 or C-08 and C-14.
- S-10 Render to output document: joins C-13 to C-12, which supplies the only style it may use.
- S-11 Approval surface: joins C-14 to the owner, consuming what S-08 and S-09 returned.
- S-12 Edit and rescore: joins C-15 back to C-09 and C-11 for the new revision.
- S-13 Application record: joins C-22 to the approval records C-14 holds. T2.
- S-14 Status surface: joins C-23 to C-22. T2.
- S-15 Email derived status: joins C-25 to C-22, under the access flag C-21 holds. T3.
- S-16 Follow up action: joins C-26 to C-22, using the interval C-21 holds. T3.
- S-17 Outbound gate: joins C-17 to C-18, reading approvals from C-14 and, when the intent is email, from C-27.
- S-18 Generation provenance record: joins C-16 to C-07 and C-08, which produce the values it stores.
- S-19 Portfolio piece write: joins the owner to C-05, whose write lands in C-19. This is the R-125 write path listed below as missing when this file was written.
- S-20 Visual style approval: joins the owner to C-12, and is the only way a style becomes the one R-127 admits.
- S-21 Rubric version adoption: joins the owner to C-10, bringing one version into force for R-126 and R-128 and naming its unestablished thresholds at adoption.
- S-22 User settings write: joins the owner to C-21, and is where R-138's match criteria are set before C-24 may run at all.
- S-23 Posting identity resolution: joins C-28 to C-19, grouping the advertisements R-139 makes one posting. T3.
- S-24 Sentence map completeness check: joins C-29 to what C-07 and C-08 produced and stands in front of C-14, blocking any revision holding a sentence absent from its claim map, per R-143. T1.

Boundaries with no entry in pm/03-interfaces.md. In each case pm/03-interfaces.md is the file that is
short, not this one, because the entity exists in pm/03-data-contract.md and a numbered requirement
demands it. They are named here and left open.

- The write path into C-05. E-02 PortfolioPiece exists in the data contract and R-125 is T1, but no
  seam describes how a portfolio piece enters the system. Only its read path is specified, as the
  candidate_portfolio input of S-05. Closed by S-19.
- The approval act into C-12. E-05 VisualStyle carries approved as a stored fact and R-127 is T1, but
  no seam describes how a style becomes the approved one. Only its read path is specified, as the
  style_id input of S-10. Closed by S-20.
- The adoption act into C-10. E-06 RubricVersion and E-07 RubricDimension exist and R-126 and R-128
  are T1, but no seam describes how a rubric version comes into force. Only its read path is
  specified, as the rubric_version input of S-08. Closed by S-21.
- The write path into C-21. E-17 UserSetting exists and its approved style reference is on the T1
  path, but no seam describes how any setting is set. Three seams read settings and none writes them.
  Closed by S-22.

All four were closed in pm/03-interfaces.md as S-19 to S-22 by the same amendment that added R-138 to
R-143 to these three files. They are left stated above rather than struck out, because the record that
this architecture found them missing is what caused them to be written.

Two further boundaries are internal by decision rather than missing. C-19 is reached by every
component that owns records, and pm/03-interfaces.md specifies that persistence boundary once only,
as S-04 for evidence records; every other entity reaches the store through the seam of the component
that produces it, which is consistent with that file's statement that it says nothing about which
seams live inside the same component. C-20 reads C-19 directly and has no seam of its own, because
the invariants are checks over stored state rather than a contract between two parties.

## Data flow

One advertisement, from ingestion to an approved rendered document. Components and seams are named in
the order they are crossed. Steps 1 to 12 are T1 and are the current build. Steps 13 and 14 are T2 and
are named so the T1 shape does not have to be torn up to reach them.

1. The owner submits an address or a pasted block of text. C-01 receives it across S-01, writes the
   advertisement with its source text unmodified into C-19, and returns an identifier. A second
   submission of the same address returns the existing identifier rather than a new one.
2. C-02 sends the stored source text to C-03 across S-02. C-03 returns one entry per field of the
   fixed field set, or a recorded malformed response. Every value that is not the unknown token
   carries the quoted substring it came from, which is what makes "did not infer" checkable.
3. C-02 discards any proposed value it cannot locate in the source text, forcing that field to the
   unknown token and recording the proposal as a dropped term. The advertisement is now readable with
   its required skills, or is readable with every field unknown, which is a state a person must
   resolve before generation is worth attempting.
4. C-06 reads the eligible evidence from C-04 across S-04 and the eligible pieces from C-05, then
   sends both closed sets with the extracted required skills to C-03 across S-05. It stores one
   inclusion or omission decision per candidate, each with its rationale and, where included, its
   rank.
5. C-07 sends the included evidence in rank order, the extracted fields, the rubric reference from
   C-10 and the style constraints from C-12 to C-03 across S-06. It receives resume content, a claim
   map covering every claim, and the three provenance values.
6. C-08 does the same across S-07 for the cover letter, additionally receiving the sentences the model
   asserts are specific to this posting.
7. C-16 records the provenance for both document versions across S-18, at the moment of generation
   rather than at query time, so the rubric version stored is the one the document was written against.
8. C-09 resolves every claim in the claim map against C-04 across S-09. A claim with no reference, an
   unresolvable reference, or a reference to a record that itself lacks a source or a date, blocks the
   document version and is named with its text and position. A blocked version does not proceed.
9. C-13 renders the unblocked version across S-10, using only the style C-12 marks approved, and
   returns the file, its page count and the text as it comes back out of the file.
10. C-11 scores the rendered artefact across S-08 against the version C-10 holds, measuring every text
    dimension on the extracted text rather than on the source content. It returns one verdict per
    dimension, the failing dimension identifiers by name, and the version it scored under.
11. C-14 presents the rendered file, the score, the claim to evidence pairs from step 8 and the
    traceability verdict to the owner across S-11. It records her decision against that exact revision
    and, on approval, issues the authorisation C-17 requires. If she edits instead, C-15 takes the
    edit across S-12, creates a new revision, and control returns to step 8 for that revision.
12. C-17 checks across S-17 that every artefact in the intent carries an approval for the exact
    revision being carried, then permits or refuses. C-18 performs the one permitted export. A gate
    record exists for every decision, so a transmission with no gate record behind it is detectable.
13. C-22 records the application across S-13, naming the approved document versions that were sent. T2.
14. C-23 shows that application beside every other on one surface across S-14, with the time each
    status was last determined and from what. T2.

C-19 is written at steps 1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13 and read at every step after the first.
C-20 runs over C-19 independently of this path and reports each invariant with its denominator, which
is zero for twenty nine of the thirty until records exist.

Six requirements were approved after the numbered steps above were written. They are recorded here
rather than renumbered into the list, so that every step number keeps the meaning it already had.

- At step 8, C-29 runs beside C-09 across S-24 over the same revision. C-09 resolves the claims that
  are in the map; C-29 counts the sentences that are not, and blocks the revision when any sentence of
  it appears in no entry of the map. R-143 is the reason this component exists, and F-09 is the record
  of why C-09 alone cannot cover it.
- Also at step 8, C-09 refuses an evidence record whose own source is a document this system
  generated, so a claim cannot be made traceable by citing the system's own output. That is R-140, and
  INV-26 in pm/03-data-contract.md is the check behind it.
- At step 11, C-14 presents every failed dimension and admits a failing document only as an explicit
  recorded override, which is R-141. The override covers a failing dimension and nothing else: a
  revision blocked by C-09 or C-29 has no override and does not reach C-14 at all.
- At step 13, C-22 also accepts an application submitted outside this system, carrying employer,
  role, date and documents sent with no advertisement behind it, which is R-142 and which required
  job_ad_id to become optional in the data contract. T2.
- Before step 1 can feed C-24 at all, the owner sets match criteria through S-22. R-138 requires
  them to be defined and forbids the system inferring them, so C-24 returns nothing and names the
  unset criteria rather than choosing a rule. T3.
- Between step 1 and any presentation by C-24, C-28 resolves posting identity across S-23, so that
  two advertisements R-139 makes one posting are presented once. T3.

## Failure modes

### F-01 C-01 Advertisement intake

How it fails: an address retrieves a login wall, a consent interstitial or an empty client side shell,
and that page is stored as the advertisement.
Observable when it does: an advertisement whose source text is present while every extracted field is
unknown, which is the same observable as a genuine posting the model failed on.
Blast radius: one advertisement, plus every document generated for it, because selection, generation
and scoring all run against required skills that were never really extracted.
Detection method: the count of advertisements whose source text exceeds a stated length while every
extracted field is the unknown token, over the count of advertisements. INV-06 fires only when a field
is absent, never when every field carries the unknown token, so it stays green through this failure.
Downstream sees: a resume tailored to nothing, scored against an empty required term list, with D-03
returning a vacuous overlap rather than a miss.

### F-02 C-02 Advertisement extractor

How it fails: the model files a preferred skill under required skills, or the reverse. Both terms
occur in the source text, so the occurrence check passes and the misfiling is invisible to it.
Observable when it does: a required skill list containing a term the posting marked preferred, visible
only by reading each stored source span back against the section it came from.
Blast radius: one advertisement and every document written for it. D-03 then measures overlap against
the wrong term set, so a passing score is a score against a false target.
Detection method: none automatic. The source span is stored, so the check is a person reading the span
against the section. This is the only T1 correctness check in this architecture with no command behind
it.
Downstream sees: a resume that scores well on D-03 while omitting a term the employer actually
required.

### F-03 C-03 Model gateway

How it fails: the model returns prose, a partial object, or a shape that does not carry one entry per
declared field, or returns nothing at all after the call has been abandoned.
Observable when it does: a recorded malformed response with the raw output retained, against an
advertisement or document version that has no result.
Blast radius: every seam that crosses this boundary, which is S-02, S-05, S-06 and S-07, so the whole
T1 chain halts at whichever step was in flight. No partial content is stored, by design.
Detection method: the count of recorded malformed responses per seam over the count of attempts at
that seam. The denominator is attempts, never successes.
Downstream sees: a stalled advertisement with the failing seam named, rather than a document. This
failure is loud, which is the intended behaviour.

### F-04 C-04 Evidence store

How it fails: a record is edited after documents have cited it, so the claim on the document no longer
matches the record standing behind it.
Observable when it does: a difference between the claim text stored on the document and the current
text of the cited record, while the identifier still resolves.
Blast radius: every document that cited that record, including approved documents and documents
already sent. This is the only failure in this architecture that reaches documents which have already
left the machine.
Detection method: compare each document claim's stored text against the current text of the record it
cites, reporting the difference set over the count of claims. INV-02 checks only that the identifier
resolves, so it stays green through this failure.
Downstream sees: a verdict of traceable on a claim nothing supports, which is R-118 passing while the
thing R-118 exists for has failed.

### F-05 C-05 Portfolio register

How it fails: a piece's address stops resolving, or a linked repository is a fork presented as
original work.
Observable when it does: D-04 returning a status other than 200 for a link in the rendered document,
or a fork marker on a piece that was selected as original.
Blast radius: one document at a time, but the cost lands on a document that has been sent, which
cannot be recalled.
Detection method: the D-04 link check over the links found in the extracted text, with the denominator
being the count of links found. A document containing no links returns vacuous, not pass.
Downstream sees: a scored document whose portfolio dimension is vacuous rather than passing, which
R-128 must not present as clean.

### F-06 C-06 Evidence selector

How it fails: included plus omitted does not equal the candidate set, so a candidate is dropped into
neither list.
Observable when it does: a count comparison between the two returned lists and the candidate set, and
a candidate with no selection decision recorded at all.
Blast radius: one document. The record of why each item was included or omitted, which R-124 requires,
is incomplete for that document only.
Detection method: the count reconciliation at the seam, plus INV-10 for empty rationales and INV-11
for rank uniqueness and contiguity. All three carry a real denominator, which is the candidate count.
Downstream sees: a resume missing evidence with no recorded reason, which reads to the owner as a
judgement rather than as a defect.

### F-07 C-07 Resume composer

How it fails: a claim carries an identifier that resolves, to a record whose text does not support it,
for example a headcount or a percentage larger than the record states.
Observable when it does: a number in the claim that does not appear in the cited record. The non
numeric residue, a verb inflated from contributed to led, is observable to no command named in any
authority file for this product.
Blast radius: one document, and the owner's standing with the employer who reads it. This is the RUIN
condition recorded in pm/01-discovery.md reached with every automatic gate green.
Detection method: the numeric join D-08 performs, reported as numeric claims with no matching source
over the count of numeric claims. The denominator is numeric claims, never claims.
Downstream sees: a traceable verdict, a passing D-08 over the numeric subset, and an unsupported
sentence in front of an employer.

### F-08 C-08 Cover letter composer

How it fails: the letter references a prior work item that is verifiable outside the document but is
not in the closed evidence set it was given.
Observable when it does: a letter blocked for the one sentence that would have scored best on D-05.
Blast radius: one letter, repeatedly rather than once, because the strongest sentence available is
exactly the one the evidence discipline forbids.
Detection method: the traceability check at S-09 names the claim. The number to report is blocked
letters over letters generated, not blocked letters alone.
Downstream sees: an owner shown a block instead of a letter, whose correct fix is to add the missing
evidence record rather than to weaken the gate.

### F-09 C-09 Claim traceability gate

How it fails: a claim present in the document is absent from the claim map, so the gate never sees it
and passes the document.
Observable when it does: a document that passes carrying an unchecked sentence, distinguishable only
by comparing the sentence count of the document against the claim count of the map.
Blast radius: every document. This is the gate R-118 rests on, so a hole here makes R-118 advisory
across the entire product rather than enforced.
Detection method: the numeric subset joins as D-08 does; the residue of unmapped non numeric sentences
has no command in any authority file. Report mapped sentences over total sentences, never the
violation count alone.
Downstream sees: an approval surface presenting as fully traceable a document that was only partly
checked.

### F-10 C-10 Rubric registry

How it fails: the rubric version is read at query time rather than stored at scoring time.
Observable when it does: a provenance record whose rubric version tracks the current file rather than
the scoring event.
Blast radius: every stored score. Scores silently change meaning whenever the rubric changes, so no
comparison between two documents scored on different days is sound.
Detection method: one document record carrying two different rubric versions, one at generation and
one at scoring. INV-12 counts one score per dimension per revision but never compares the two version
references, so it stays green through this failure.
Downstream sees: a score that cannot be reproduced, which under the evidence rules governing this
project is withdrawn rather than defended.

### F-11 C-11 Rubric scorer

How it fails: a dimension whose threshold is unestablished returns pass. Six of the nineteen threshold
entries in pm/03-evals.md are in that state, across four of the nine dimensions, so returning pass is
not a hypothetical defect.
Observable when it does: a document reported as passing on D-01, D-04, D-05 or D-09 when nothing was
compared against. The correct verdict is not decidable, and a document is then neither passing nor
failing on that dimension.
Blast radius: every document ever scored, for as long as those thresholds are unestablished. No
document can be fully passing, so no clean score exists to show the owner.
Detection method: the INV-15 predicate in pm/03-data-contract.md, run against pm/03-evals.md. It is
the one invariant of the thirty that is currently red rather than vacuous, and its denominator is
nineteen threshold entries.
Downstream sees: an approval surface that can never show a fully passing document, so the owner
approves against a partial score every time.

### F-12 C-12 Visual style registry

How it fails: no style is marked approved, or more than one is.
Observable when it does: a render refused with the requested style and the approved style both named,
or a render that silently picks one of two approved styles.
Blast radius: every render, so the whole T1 chain stops at rendering. Nothing can be scored on the
dimensions measured over the rendered artefact and nothing can reach approval.
Detection method: INV-13 over rendered documents, reporting documents whose style is not approved over
the count of rendered documents. It is vacuous until a first render exists.
Downstream sees: no rendered file, therefore no score and no approval, because S-08 and S-11 both
require the rendered artefact rather than the source content.

### F-13 C-13 Document renderer

How it fails: the text extracted back out of the rendered file differs from the source content, with
spaces inserted between letters or words split across lines.
Observable when it does: the letter spacing artefact check returning matches on the extracted text
while the source content has none, and fewer than three standard section titles found.
Blast radius: every document. Every text dimension of the rubric is measured on extracted text, so a
rendering defect makes the entire score describe a document the reader will never see, while the file
may fail an applicant tracking system that looked clean on screen. This component also carries the
whole cost of ADR-001: rendering is the one capability that demonstrably already works in the estate,
the denylist forbids reusing its implementation, templates and pipeline, and nothing downstream of
step 9 in the data flow can run until this component exists.
Detection method: the D-07 letter spacing count over the extracted text, which must be zero, and the
count of standard section titles found, which must be at least three. Both require a rendered file, so
both are vacuous today.
Downstream sees: a passing score on a document that parses badly, which is exactly what R-127 and D-07
exist to prevent.

### F-14 C-14 Approval surface

How it fails: an approval is recorded, the document is then edited, and the approval carries forward
to the new revision.
Observable when it does: an approval record whose document revision is not the current revision of
that document.
Blast radius: one send, which cannot be recalled. pm/02-triage.yaml records this product's blast as
irreversible for this reason.
Detection method: compare the revision on each approval record against the current revision of its
document, reporting mismatches over the count of approvals. INV-16 checks that a listed document is
approved but never that the approval belongs to the revision being carried.
Downstream sees: the outbound gate treating a stale approval as authorisation, unless the gate
compares revisions for itself.

### F-15 C-15 Document editor

How it fails: two edits are submitted against the same base revision and the second overwrites the
first without either being shown the conflict.
Observable when it does: a revision chain in which one submitted edit has no corresponding revision.
Blast radius: one document and one lost edit. Small with the single user pm/01-discovery.md describes
today, larger the moment the product has the second user it is intended for.
Detection method: the count of submitted edits over the count of revisions created. Any difference is
a lost edit.
Downstream sees: a score attached to content the owner did not write, or attached to the revision she
believes she replaced.

### F-16 C-16 Provenance ledger

How it fails: the recorded model identifier is a family name rather than a specific version.
Observable when it does: a provenance record that cannot distinguish two runs months apart.
Blast radius: every generated document. No difference between two documents can be explained, so no
regression in output quality can be attributed to anything.
Detection method: a format check on the recorded identifier, over the count of provenance records.
INV-21 requires the identifier to be non empty but never requires it to be a version, so it stays
green through this failure.
Downstream sees: an owner told which model wrote a document by a claim rather than by evidence.

### F-17 C-17 Outbound gate

How it fails: a transmission path exists that never consults the gate.
Observable when it does: a send, an upload or an export with no gate record behind it.
Blast radius: total for R-129 and R-136. The gate can be perfectly correct and entirely unenforced,
and its correctness is no evidence at all about what left the machine.
Detection method: the count of transmissions over the count of gate records, where the transmission
count has to come from somewhere other than the gate for the comparison to mean anything.
Downstream sees: an unapproved document at an employer, with the system's own records showing that
nothing was sent.

### F-18 C-18 Transmission executor

How it fails: the export succeeds and the file that lands is not the file that was approved.
Observable when it does: a difference between the artefact recorded against the approved revision and
the artefact that was written out.
Blast radius: one application, irrecoverable once it has left.
Detection method: a fingerprint comparison between the approved artefact and the emitted artefact.
pm/03-data-contract.md carries such a fingerprint for advertisement source text only, so no field
exists today to compare rendered files against.
Downstream sees: an approval record describing a different document from the one the employer read.

### F-19 C-19 Record store

How it fails: a write is acknowledged and is not durable, for example an advertisement retrieval
succeeds while the write of its source text does not.
Observable when it does: a retrieval record with no advertisement behind it, which is what
distinguishes a lost body from a fetch that never happened.
Blast radius: whichever records were in flight, and every correctness claim made about the store.
Every invariant is evaluated over what this component returns, so a silent partial write makes a green
invariant meaningless rather than wrong.
Detection method: the thirty invariant predicates, each reporting its denominator. Twenty nine of the
thirty report zero records checked today, which is vacuous rather than passing.
Downstream sees: a system reporting consistency over a set from which the failure is missing.

### F-20 C-20 Invariant checker

How it fails: it runs over an empty or absent record set and reports no violations.
Observable when it does: a result carrying a denominator of zero. pm/03-data-contract.md records
exactly that state today for twenty nine of its thirty invariants.
Blast radius: every claim of correctness anyone makes from these checks, which is the whole quality
argument for the product.
Detection method: the denominator itself. Any invariant reporting zero records checked is vacuous, and
seventeen of the thirty predicates have never been seen fire against a real violation, so they are
not yet trusted even when they are not vacuous.
Downstream sees: a green board over an empty store, which is the precise failure the evidence rules
governing this project exist to prevent.

### F-21 C-21 Settings register

How it fails: an unset value is served as though it were a chosen one, for example a follow up
interval the owner never set.
Observable when it does: behaviour running on a value that no user record shows being set.
Blast radius: mostly T3 behaviour, plus one T1 path, because the approved style reference lives here
and a defaulted style reference would let an unapproved render through C-12.
Detection method: compare the set of settings holding a stored value against the set the reading
components require, reporting unset values as unset rather than as numbers.
Downstream sees: the system choosing on the owner's behalf, which pm/03-data-contract.md deliberately
refuses by supplying no default for the interval.

### F-22 C-22 Application register

How it fails: the same application is recorded twice, once by the send path and once by hand.
Observable when it does: two application identifiers for one real application, both listed on the
status surface.
Blast radius: the register's counts, the follow up clock, and any status derived from a message, which
attaches to whichever of the two records it matched first.
Detection method: the count of applications over the count of distinct advertisements carrying a sent
document. Any excess is a duplicate.
Downstream sees: two rows for one employer, with a follow up raised against the copy that never
received the reply.

### F-23 C-23 Status surface

How it fails: a row shows blank because a status has never been derived for it.
Observable when it does: a blank cell that a reader cannot distinguish from no response.
Blast radius: the owner's decisions about which applications to chase, which is the only thing this
surface is for.
Detection method: the count of applications whose status has never been derived over the count of
applications, rendered on the surface rather than computed and hidden.
Downstream sees: an owner who does not chase an application that was rejected months ago.

### F-24 C-24 Discovery feed

How it fails: the same posting appears on two boards under different addresses, is ingested as two
advertisements, and both are presented.
Observable when it does: two identifiers with near identical source text, each with a presentation
record on the same day.
Blast radius: the once each guarantee R-122 makes, which is violated in the owner's experience while
every stored record looks correct.
Detection method: a similarity comparison across stored source text between advertisements. INV-07
counts presentations per advertisement identifier and cannot see this case at all. INV-24 and INV-25
count by posting group instead and do see it, but only where C-28 grouped the pair; where C-28 did not,
INV-25 and INV-07 are the same check and neither fires.
Downstream sees: the owner reading the same job twice, which is the user visible failure R-122 exists
to prevent.

### F-25 C-25 Mailbox status deriver

How it fails: a message is matched to the wrong application because two applications are open at the
same employer.
Observable when it does: a citation that resolves cleanly to a passage naming a different role.
Blast radius: two applications, one now wrong in each direction, and a follow up clock that restarts
on the wrong row.
Detection method: none automatic. INV-18 checks that the cited message exists, never that it is the
right message. The check is a person reading the cited passage.
Downstream sees: a status change carrying a citation that looks correct, which is worse than a status
change carrying none.

### F-26 C-26 Follow-up scheduler

How it fails: an action is raised for an application already rejected, because the closing message was
never recognised as one.
Observable when it does: an open action on a closed application.
Blast radius: the owner's trust in the action list, which is the only property that makes the list
worth reading.
Detection method: the count of open actions whose application carries a closing status, over the count
of open actions.
Downstream sees: a prompt to chase an employer who has already said no.

### F-27 C-27 Message approval register

How it fails: one approval is used to authorise a second message.
Observable when it does: one approval identifier appearing against two send records.
Blast radius: R-136 entirely, since per message means one approval authorises exactly one message.
Detection method: a uniqueness count over approval identifiers against send records. INV-20 requires
an approval and a scope of this message on any sent message, but never checks that the approval was
used once.
Downstream sees: a message the owner never read leaving the machine under an approval she gave for a
different one.

### F-28 C-28 Posting identity resolver

How it fails: two genuinely different roles at one employer carry the same role title and a largely
boilerplate advertisement body, are collapsed into one posting, and one of them is never presented.
Observable when it does: a posting group holding two advertisements whose required skill lists differ,
with one presentation record between them.
Blast radius: the postings the owner never sees, which is unbounded in the direction that matters,
because a job that was never presented leaves no trace the owner can notice. The opposite failure,
grouping too little, only shows the same job twice.
Detection method: the count of advertisements grouped with another over the count of advertisements,
read beside the count of groups whose members disagree on employer or required skills. INV-24 checks
that duplicates share a group and INV-25 that a group is presented once; neither can tell a correct
grouping from an over eager one, and no requirement supplies the threshold that would settle it.
Downstream sees: a discovery feed that is quietly short, with every stored record consistent.

### F-29 C-29 Sentence map gate

How it fails: the rule this component uses to divide a document into sentences differs from the rule
the composer used to build the claim map, so two sentences are joined into one and an unsupported
clause rides into an approved document inside a sentence that matched the map.
Observable when it does: a mapped total that does not equal the claim count recorded for the same
revision, and a sentence in the rendered document longer than any single entry of the claim map.
Blast radius: every generated document. This is the gate R-143 rests on, and unlike C-09 it is the
last check between a fabricated sentence and an employer, so a hole here is the RUIN condition
pm/01-discovery.md records reached with every automatic gate green.
Detection method: mapped sentences over total sentences for each revision, with the sentence rule
recorded beside the result so two disagreeing runs are distinguishable from a document that changed.
INV-29 requires the count to exist for every revision and INV-30 requires a document holding an
unmapped sentence to be blocked; neither can detect the two rules disagreeing, because both sides
report their own totals.
Downstream sees: an approval surface presenting a document as fully mapped when the map and the
document were divided differently, which is the same class of failure as F-09 and is the reason both
components exist rather than one.
