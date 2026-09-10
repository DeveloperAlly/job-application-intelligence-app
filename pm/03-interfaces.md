# Interfaces: job application pipeline

A seam here is any place two parts of this product meet where the two sides could be built by different people on different days: a call one part makes into another, a record one part writes and another reads, a surface a person acts on, or the boundary where a program hands a prompt to a model and has to survive whatever comes back. Each entry names the seam, the requirements it serves, what goes in, what must come back, and what is observable when the contract is broken. This file does not choose a transport, a storage product, a model, a framework or a process boundary, and it says nothing about which of these seams live inside the same component: those are step 5 decisions. It names record types without defining their fields, which belongs to the data contract, and it names rubric dimensions by their IDs in pm/03-evals.md without restating them.

## S-01 Advertisement intake

Serves: R-119, R-120

**Inputs**
- source_kind: one of "url" or "pasted_text", required, which of the two accepted forms the caller is supplying
- source_value: a single URL, or a block of text, required, the advertisement itself
- captured_at: a date and time, required, when the caller obtained the advertisement

**Outputs**
- advertisement_id: an opaque identifier, the handle every later seam uses for this posting
- source_text: the full advertisement text exactly as retrieved or pasted, unmodified, which is what R-120 requires be retained
- retrieval_record: the URL, the fetch time and the response status, present only when source_kind was "url", absent for pasted text
- intake_status: one of "stored", "duplicate" or "rejected"

**Error cases**
The URL cannot be retrieved because the host does not resolve, the response is not a success, or the fetch times out. Nothing is stored, no advertisement_id is issued, and the caller sees the submitted URL returned with the failure kind and status code, so a person can tell a dead link from a paywall.
The URL retrieves a login wall, a consent interstitial or an empty client-side shell rather than a posting. Nothing in the requirements tells the seam how to recognise that, so the defensible behaviour is to store what was retrieved and let extraction mark every field unknown. What is observable is an advertisement whose source_text is present and whose extracted fields are all unknown, which is the same observable as a genuine posting the model failed on. This ambiguity is not resolved here.
source_kind is "url" but source_value is not a URL, or source_kind is missing. The submission is rejected, no advertisement_id is issued, and the rejection names which of the two accepted forms was expected.
The same URL is submitted twice. The seam returns the existing advertisement_id with intake_status "duplicate" rather than issuing a second one, because R-122 requires a posting be presented once. What is observable is that the count of advertisements does not increase while the caller still receives a usable identifier.
The retrieval succeeds and the write of source_text fails. No advertisement_id is issued, and the observable is a retrieval_record with no advertisement behind it, which is what distinguishes a lost body from a fetch that never happened.

## S-02 Advertisement field extraction

Serves: R-120, R-121, R-137

This is a prompt boundary between a program and a model. It is specified to the same standard as a call boundary because the model can return anything.

**Inputs**
- advertisement_id: an identifier, required, the posting being extracted
- source_text: the full unmodified advertisement text, required, and the only content about this posting the model is given
- field_list: the fixed set employer, role title, seniority, location, work arrangement, required skills, preferred skills, required, set by R-120 and not extensible by the caller
- unknown_token: the exact value the model must emit for a field it cannot determine, required, so that "unknown" is a value and not an absence

**Outputs**
- extraction: one entry per field in field_list, each either a value or the unknown_token, never missing
- required_skills and preferred_skills: lists of terms, each term a string that occurs in source_text, because R-121 forbids inferring a value
- source_span: for every field that is not unknown, the quoted substring of source_text the value came from, which is what makes "did not infer" checkable rather than asserted
- extraction_status: one of "complete" or "partial", where partial means at least one field is unknown
- dropped_terms: the list of terms the model proposed that could not be found in source_text and were therefore discarded
- model_id: the model version that produced this extraction, required by R-137, which covers every model output and names advertisement extraction explicitly. Without it, which model read a posting is a claim and not a record

**Error cases**
The model returns a value for a field that cannot be located in source_text. The field is forced to unknown and the proposed value is recorded in dropped_terms, because R-121 forbids inference. What is observable is a field the model answered and the system refused, visible as a dropped term with no source_span.
The model returns prose, a partial object, or a shape that does not carry one entry per field. No extraction is recorded, the advertisement is left with extraction not attempted, and the raw model output is retained so the malformed response can be read back rather than described from memory.
The model omits a field rather than marking it unknown. The field is treated as unknown, and the record keeps the difference between "the model said unknown" and "the model did not answer", because those two point at different fixes.
The model paraphrases a term the advertisement writes differently, returning an expanded name where the posting used an abbreviation. The occurrence check fails, the term lands in dropped_terms, and what is observable is a required skill visible to a human reader in source_text that is absent from required_skills. Whether the right behaviour is to drop the term or keep the paraphrase is not settled by R-120 or R-121; dropping is what "shall not infer" supports.
The model files a preferred skill under required skills, or the reverse. Both terms occur in source_text, so the occurrence check passes and the misfiling is invisible to it. It is observable only by reading each source_span back against the section it came from, and nothing in the requirements makes that automatic.
Every field comes back unknown while source_text plainly names the employer. This is indistinguishable at this seam from the login wall case in S-01, and both surface as an advertisement with full source text and no extracted fields.

## S-03 Discovery feed

Serves: R-122

**Inputs**
- discovery_enabled: a flag, required, because R-122 scopes this seam to "where daily discovery is enabled"
- match_criteria: the user's standing criteria for what counts as a matching advertisement, required, and undefined by any requirement in this register
- exclusion_set: the advertisement identifiers already presented, dismissed or applied to, required
- as_of: the day the feed is being produced for, required

**Outputs**
- feed_items: advertisement identifiers not present in exclusion_set, each with the reason it matched
- presentation_records: one per returned item, carrying the advertisement identifier and the time it was presented, which is what makes "once each" enforceable later

**Error cases**
The same posting appears on two boards under different URLs and is ingested as two advertisements. The exclusion set is keyed by advertisement identifier, so both are presented, and R-122 is violated in the user's experience while every record looks correct. What is observable is two identifiers with near identical source_text and two presentation records on the same day.
A dismissal is recorded by the user and the write fails. The item is not in exclusion_set the next day and is presented again, observable as one advertisement identifier carrying two presentation records on different days.
Discovery is enabled and match_criteria has never been set. No requirement in this register defines the matching rule, so the seam has no defensible behaviour between returning everything and returning nothing. It must return nothing and report the unset criteria rather than pick a rule, and the observable is an empty feed with a named cause.
The user applies to a posting outside this system, so no applied marker exists. The posting is presented again, and the only observable is the user recognising it, which no command can detect.

## S-04 Evidence record store

Serves: R-117

**Inputs**
- claim_text: the statement about the user's history, required on write
- source: what attests the claim, required on write, and the field whose absence R-117 makes fatal
- claim_date: the date the claim refers to, required on write
- query: on read, a selection over the stored records such as a skill term or a date range, required on read

**Outputs**
- evidence_record_id: an identifier issued only when source and claim_date are both present
- records: on read, the matching records, each carrying its identifier, its claim text, its source and its date
- write_status: one of "stored" or "rejected", with the missing field named on rejection

**Error cases**
A write arrives with no source, or with no date. It is rejected and no identifier is issued, because R-117 makes both mandatory rather than desirable. What is observable is that the record count does not change and the rejection names which field was absent.
A record is written whose source is a document this system generated. The record then attests itself through its own output, and every traceability check downstream passes while nothing outside the system supports the claim. R-117 does not exclude this, so the seam cannot reject it on the requirement alone; what it can do is record the source kind, making the circular case observable as an evidence record whose source resolves to a generated document.
A record is edited after documents have cited it. The document's claim no longer matches the record it points at, and R-118 still reports the claim as traceable because the identifier resolves. What is observable is a difference between the claim text stored on the document and the current text of the cited record.
A read for a required skill returns nothing. Generation then has no material for that skill, and the observable is an empty result rather than an error, which the selection seam must convert into a stated omission instead of silence.

## S-05 Evidence selection and ranking

Serves: R-124, R-125

This is a prompt boundary between a program and a model.

**Inputs**
- required_skills: the extracted required skills for this advertisement, required, the thing relevance is measured against
- candidate_experience: the evidence records eligible for inclusion, required, and the closed set the model may choose from
- candidate_portfolio: the portfolio pieces eligible for selection, required, also a closed set
- advertisement_extraction: the remaining extracted fields, optional, for context the required skills do not carry

**Outputs**
- included: an ordered list of evidence record identifiers, the order being the relevance order R-124 requires
- included_rationale: one sentence per included item saying why it was included, required by R-124 for every item
- omitted: the identifiers from candidate_experience that were not included
- omitted_rationale: one sentence per omitted item, required by R-124, which asks why each item was included or omitted
- portfolio_selected: the chosen portfolio pieces with one rationale sentence each, required by R-125

**Error cases**
The model returns an included identifier that is not in candidate_experience or candidate_portfolio. The selection is rejected whole rather than filtered, because a fabricated identifier means the model was not treating the candidate set as closed. What is observable is an identifier that does not resolve in the evidence store.
The model returns an item with an empty rationale, or a rationale that repeats the item's own text. R-124 and R-125 make the rationale mandatory, so the selection is rejected and the count of items with no rationale is reported.
The counts do not reconcile: included plus omitted is not equal to the size of candidate_experience. Some candidate was silently dropped into neither list, so the record of why each item was included or omitted is incomplete. This is observable as a simple count comparison and is the cheapest check at this seam.
Every candidate is omitted. The resume would have no experience content at all, and the observable is an empty included list with a full omitted list, which must stop generation rather than produce an empty document.
The rationale mentions no term from required_skills. The rationale cannot be shown false by any command, but a rationale with zero overlap with the required skills is observable and is the only automatic signal that relevance was asserted rather than applied.

## S-06 Resume generation

Serves: R-123, R-124, R-137

This is a prompt boundary between a program and a model, and it is the seam where an unsupported sentence becomes a document.

**Inputs**
- selection: the included list and its order from S-05, required, and the only evidence content the model may draw on, which is what R-123 means by "drawing only on evidence records"
- evidence_records: the full text of exactly those records, required
- advertisement_extraction: employer, role title, seniority and required skills, required, for targeting
- rubric_reference: the identifier and version of pm/03-evals.md the document is being written against, required, so that the version scored is the version written to
- style_constraints: the register and structural constraints the approved style imposes, required

**Outputs**
- document_content: the resume content, structured but not rendered, since rendering is S-10
- claim_map: for every claim in document_content, the evidence_record_id it came from, with no claim absent from the map
- content_order: the order claims appear in, which must equal the order in selection
- model_id: the model version that produced the document, required by R-137
- prompt_version: the prompt version used, required by R-137
- rubric_version: the rubric version the document was written against, required by R-137

**Error cases**
The model returns a claim with no evidence reference. The document is not rendered and does not reach the approval surface, and the untraceable claim is named with its text and its position, which is exactly what R-118 requires. This is the failure this seam exists to catch, and a generation seam without this case is not finished.
The model returns a claim carrying an evidence_record_id that does not resolve in the evidence store. Treated identically to a missing reference and blocked, observable as an identifier that returns nothing on lookup.
The model returns a claim whose identifier resolves but whose text is not supported by the record it cites, for example a headcount or a percentage larger than the record states. The identifier check passes and the document is wrong. The detectable subset is numeric: a number appearing in the claim that does not appear in the cited record, which is the same check D-08 runs. The non numeric residue, a verb inflated from "contributed to" to "led", is not detectable by any command named here.
The model reintroduces an item S-05 placed in the omitted list, or reorders content away from the selection order. R-124 makes ordering part of the contract, so this is a generation failure and not a style preference. What is observable is a claim citing an omitted identifier, or a content_order that does not equal the selection order.
The model returns nothing, or returns after the call has been abandoned. No document exists and no partial content is stored, and the observable is a failed generation attempt recorded against the advertisement identifier with no document reaching approval.
The document violates a rubric dimension, for example it runs long or opens a bullet with a responsibility phrase. That is not an error at this seam. It is a scoring outcome at S-08, and the generation seam must not silently rewrite or suppress the document to avoid it, because the failing score is information the user is entitled to see under R-128.

## S-07 Cover letter generation

Serves: R-126, R-137

This is a prompt boundary between a program and a model.

**Inputs**
- advertisement_extraction: employer, role title and required skills, required, since D-05 makes company specific detail the difference between a letter and a template
- selected_evidence: the evidence records the letter may draw on, required, the same closed set discipline as S-06
- letter_dimensions: the dimensions of pm/03-evals.md the letter is written against, required. R-126 names "the register and language dimensions". pm/03-evals.md contains one dimension about letter language, D-05, and no dimension named register. This input is therefore under specified and the gap is recorded rather than closed by guessing.
- prior_letter_corpus: the text of previously sent letters, required, because D-05 compares against them
- rubric_reference: identifier and version of the rubric, required

**Outputs**
- letter_text: the letter
- claim_map: for every claim in the letter, the evidence_record_id it came from
- company_specific_spans: the sentences the model asserts could not be pasted into another application, which is what D-05 is judged on
- model_id, prompt_version, rubric_version: the three provenance values R-137 requires

**Error cases**
The model returns a claim with no evidence reference. The letter is blocked from the approval surface and the claim is named, on the same terms as S-06 and for the same reason under R-118.
The letter contains no sentence naming the specific employer, product or posting. D-05 is a binary dimension, so this is a scoring failure at S-08 rather than a generation error, and the observable is a D-05 verdict of fail with the sentence count that qualified as company specific reported as zero.
A sentence closely matches one in prior_letter_corpus. pm/03-evals.md records the cross letter similarity ceiling as unestablished, so no threshold exists to compare against. The seam returns the similarity number and no verdict, and the observable at S-08 is a subcheck reported as not decidable rather than passed.
The model references a prior work item that is verifiable outside the document but is not in selected_evidence. D-05 rewards the reference and R-123's evidence discipline forbids the source. The claim is blocked as untraceable, and the observable is a letter blocked for a sentence that would have scored well, which is the intended precedence: evidence before score.
The dimension set the letter is scored against differs from letter_dimensions because R-126's "register" dimension does not exist. The observable is a document whose recorded rubric coverage names fewer dimensions than the requirement text implies, which is an open gap and not a defect the seam can fix.

## S-08 Rubric scoring

Serves: R-126, R-128

**Inputs**
- document: the content, and the rendered file where a dimension is defined over the rendered artefact rather than the text, required
- rubric_version: the version of pm/03-evals.md to score against, required, and it must be the version recorded at generation
- dimension_set: D-01 through D-09, required, the nine dimensions the rubric defines
- required_terms: the required skills extracted for this advertisement, required for D-03
- prior_letter_corpus: required for D-05
- evidence_index: required for D-08, which joins numeric claims against stored source records

**Outputs**
- dimension_results: one entry per dimension, each carrying the dimension identifier, the measured value, the threshold applied, a verdict of pass, fail, not decidable, vacuous or not yet judged, and the output of the check that produced it
- document_status: failing if any dimension is at or below its threshold, which is R-128's condition
- failing_dimensions: the identifiers of the dimensions that failed, named, because R-128 requires the dimension be named and not just the failure reported
- rubric_version_used: echoed back, so a score is never read against a rubric it was not produced under

**Error cases**
A dimension's threshold is recorded in pm/03-evals.md as unestablished. Six thresholds across four dimensions are in that state. The dimension cannot return pass or fail, and returning pass is the defect, because an unestablished threshold means nothing was measured against. The verdict is not decidable and the document is neither passing nor failing on that dimension.
A dimension carries a human judgement clause and no person has judged it. The verdict is not yet judged, and a document scored entirely by machine is incomplete rather than passing. The observable is a score with unjudged dimensions and a document_status that must not read as clean.
A check runs over an empty set, for example the link checks of D-04 on a document containing no links. The result is vacuous, not a pass, and must be reported as vacuous, because a document with no portfolio links has not demonstrated portfolio quality, it has avoided the question.
The rendered document cannot be parsed and text extraction returns nothing. Every text based dimension then runs over an empty string and would report clean. All of them must report vacuous, and the observable is a full set of vacuous verdicts on a document that exists.
The generator enforces a formatting or wording rule that has no row in pm/03-evals.md. D-06 fails, and the observable is the difference between the list of enforced rule identifiers and the row identifiers in the rubric file being non empty.
The rubric_version used at scoring differs from the rubric_version recorded at generation. The score does not describe the document that was written, and the observable is one document record carrying two different rubric versions, which R-137 makes visible by requiring the version be recorded.

## S-09 Claim traceability check

Serves: R-118, R-130, R-140

**Inputs**
- document: the content whose claims are being checked, required
- claim_map: the claim to evidence mapping the generating seam produced, required
- evidence_store_read: the ability to resolve each referenced identifier, required

**Outputs**
- verdict: one of "traceable" or "blocked", where blocked stops the document reaching the approval surface under R-118
- untraceable_claims: for each, the claim text and its position in the document, which is R-118's requirement that the untraceable claim be named
- claim_evidence_pairs: for every claim, the evidence record behind it, which is the set the approval surface displays under R-130

**Error cases**
A claim carries an identifier that resolves to a record with no source or no date. The record violates R-117, so the claim is not traceable to evidence even though the lookup succeeded. It is reported as untraceable and both the claim and the deficient record are named.
A claim is present in the document but absent from claim_map, so the check never sees it. The gate then passes a document containing an unchecked statement. The detectable subset is numeric tokens, the same join D-08 performs, and the residue of unmapped non numeric sentences is not settled by any requirement here.
The document contains no claims at all. Every check passes over an empty set, so the verdict is vacuous rather than traceable, and a document that trivially passes this gate must be visibly distinguished from one that earned it.
The document reaches the approval surface before this check has returned. R-118 is violated by ordering rather than by logic, and the observable is an approval surface record timestamped earlier than the traceability verdict for the same document version.

## S-10 Render to output document

Serves: R-127

**Inputs**
- document_content: the resume or cover letter content, required
- style_id: the user's approved visual style, required, and R-127 admits only the approved one
- output_kind: resume or cover letter, required

**Outputs**
- rendered_file: the PDF
- page_count: read from the rendered file, which D-01 is measured on
- extracted_text: the text as it comes back out of the rendered file, which is what every text dimension of the rubric must be measured on rather than the source content
- style_id_used: echoed back, so the approved style can be verified after the fact

**Error cases**
The requested style_id is not the approved one. The render refuses and names the style requested and the style approved, because R-127 does not permit an unapproved visual style to be produced at all.
The text extracted from the rendered file differs from the source content, with spaces inserted between letters or words split across lines. Every text check then runs against text the reader will never see, and the rendered document may fail an applicant tracking system while the source content looks clean. What is observable is the letter spacing artefact check returning matches on extracted_text while the source content has none.
The style places content in a page header region, or produces more than one text column. The render still succeeds; this is a D-01 and D-07 scoring failure at S-08 rather than a render error, and the observable is a successful render with a failing D-01.
The rendered file exceeds the upload limit the rubric records for the target vendor. The render succeeds and the document cannot be submitted, observable from the file size alone.
The render succeeds but the claim positions in the rendered file no longer correspond to the positions in claim_map, so the approval surface cannot point at the right place in the document. The observable is a claim whose recorded position does not land on that claim in the rendered file.

## S-11 Approval surface

Serves: R-118, R-129, R-130, R-141

**Inputs**
- document_version: the exact version being presented, required, since approval attaches to a version and not to a document
- rendered_file: required, because the user approves what will be sent, not an intermediate form
- score: the dimension results from S-08, required
- claim_evidence_pairs: from S-09, required, since R-130 requires the evidence record be displayed for every claim
- traceability_verdict: required, since a blocked document must not be presented as approvable

**Outputs**
- approval_record: the document version, the decision, who made it and when
- transmit_authorisation: the token S-17 requires before any send, upload or export, issued only on approval, which is what makes R-129 enforceable rather than advisory

**Error cases**
A document whose traceability verdict is blocked is presented for approval. R-118 forbids it reaching this surface, so the surface refuses to render it as approvable and shows the named untraceable claims instead. The observable is a blocked document with no approval control available.
A claim is displayed with no evidence record because claim_map is incomplete. R-130 requires the record for every claim, so the surface must refuse rather than show an empty panel next to a claim, and the observable is a refusal naming the claim with no evidence.
Approval is recorded and the document is then edited. The approval belongs to the earlier version and must not carry forward, and the observable is an approval record whose document version is not the current one, which S-17 must treat as no approval at all.
A document with failing dimensions is approved by the user. R-128 requires the failure be marked and the dimension named, and R-129 gives the user the decision; nothing in this register forbids approving a failing document. The approval record therefore carries the failing dimension identifiers so the choice is visible afterwards. Whether a failing document should be approvable at all is not settled by these requirements.

## S-12 Edit and rescore

Serves: R-131

**Inputs**
- document_version: the unapproved version being edited, required
- edited_content: the user's replacement content, required
- edit_scope: which claims or sections changed, optional, and if absent the whole document is rechecked

**Outputs**
- new_document_version: a new version rather than a mutation of the old one, so the version an approval attached to still exists
- score: a fresh score for the new version, which R-131 requires after each edit
- claim_map and traceability_verdict: both recomputed, because a hand edited sentence is a new claim

**Error cases**
The user's edit introduces a sentence that no evidence record supports. R-118 applies to the edited document exactly as it does to the generated one, so the document is blocked and the new claim is named. The observable is a block whose named claim is user authored rather than model authored.
An edit is submitted for a document that has already been approved. R-131 scopes editing to unapproved documents, so the edit is refused and the refusal names the approval record standing in the way.
The rescore fails or is skipped and the surface continues to display the previous version's score. The user then reads a score for content that no longer exists. The surface must show no score rather than a stale one, and the observable is a score whose document version does not equal the current version.
Two edits are submitted against the same base version. The second overwrites the first without either user seeing the conflict, and the observable is a version chain in which one submitted edit has no corresponding version.
The edit removes a claim that other claims depended on for context while leaving the dependent claims in place. Nothing in the requirements makes this detectable, and the only observable is a rescore in which the affected dimensions move without an obvious cause.

## S-13 Application record

Serves: R-132, R-142

**Inputs**
- employer: the hiring organisation, required, and permitted to be the unknown value when extraction could not determine it
- role: the role title, required, same allowance for unknown
- application_date: the date the application was sent, required
- documents_sent: the identifiers of the approved document versions that were sent, required
- status: the initial status, required

**Outputs**
- application_id: the identifier the status surface and the email derivation seam both key on
- application_record: the five recorded values, readable without opening a file, which is what R-133 depends on

**Error cases**
A document identifier is recorded as sent that has no approval record. R-129 forbids transmission without approval, so an application citing an unapproved document is evidence that something bypassed the outbound gate. The observable is a sent document identifier with no matching approval record.
Employer or role is unknown because extraction marked it unknown under R-121. The record stores unknown rather than a guess, and the status surface must display unknown rather than blank, because a blank cell reads as an absent record and unknown reads as an absent fact.
The user applies through a company portal outside this system and no record is created. The register undercounts, and the only observable is an advertisement that was never marked applied and never appears in the register. Nothing in these requirements closes that path.
The same application is recorded twice, once by the send path and once by hand. Two application identifiers exist for one real application, the status surface shows both, and email derivation may attach a message to whichever it matches first.

## S-14 Status surface

Serves: R-133

**Inputs**
- application_records: all of them, required
- current_statuses: the latest status for each, required
- status_provenance: for each status, where it came from and when it was last derived, required, since R-134 requires a citation when the source is a message

**Outputs**
- status_view: one surface listing every application with employer, role, date, documents sent, current status, when the status was last determined and from what
- staleness: for each row, how long since the status was last determined

**Error cases**
An application's status has never been derived and the row shows blank. Blank is not "no response" and the surface must distinguish the two, because a person reading blank as "waiting" will not chase an application that was actually rejected months ago.
A status derived from email contradicts a status the user set by hand. The surface shows one value and the conflict is invisible. What is observable is a status history carrying two sources with different values, and the surface must show that the value is contested rather than pick one silently.
The surface can only be produced by opening a file or running an export. R-133 forbids that explicitly, so the observable defect is the existence of a step in which the user must open something to learn the state of an application.
A status is displayed that was derived before the last message arrived. The row is stale rather than wrong, and staleness is what makes the difference readable.

## S-15 Email derived status

Serves: R-134

**Inputs**
- mailbox_access: the granted scope, required, since R-134 is conditional on access being granted
- messages: the messages available under that scope, required
- application_register: the applications to match messages against, required

**Outputs**
- status_derivations: for each, the application identifier, the new status, the message identifier it was derived from and the quoted passage, which is the citation R-134 requires
- unmatched_messages: messages that appear relevant and matched no application, so the gap is visible rather than silent

**Error cases**
A derivation is produced with no message identifier. R-134 requires the citation, so the derivation is refused rather than recorded as a bare status change, and the observable is a rejected derivation with its proposed status named.
A message is matched to the wrong application because two applications are open at the same employer. The status changes on the wrong row and the citation still resolves, so the error is only observable by reading the cited passage and seeing it names a different role.
A rejection is worded so it is not recognisable as one, or an interview invitation arrives inside a thread about something else. The status does not change, the follow up timer keeps running, and the observable is a follow up action raised against an application that is already closed.
Mailbox access is granted and then revoked. Derivation stops, statuses stay where they were, and every row silently ages. The surface must show that derivation is no longer running, otherwise the observable is indistinguishable from a quiet inbox.

## S-16 Follow up action

Serves: R-135

**Inputs**
- follow_up_interval: the interval the user set, required, and R-135 makes it user set rather than defaulted
- last_inbound_date: the date of the last response for the application, required, or absent when no response has ever arrived
- application_date: required, used as the basis when last_inbound_date is absent
- now: the current date, required

**Outputs**
- follow_up_actions: one per qualifying application, naming the application, the interval that elapsed, the date the interval was measured from and the date raised

**Error cases**
The interval has never been set. R-135 conditions the trigger on a user set interval, so the seam raises nothing and reports the missing setting rather than choosing a default, and the observable is an empty action list with a named cause rather than silence.
No status has ever been derived, so last_inbound_date is absent and the interval is measured from application_date instead. The action still fires, and the observable is a follow up whose stated basis is the application date, which tells the user the system never saw a response rather than that a response was late.
An action is raised for an application already marked rejected. The interval elapsed because the closing message was never recognised at S-15, and the observable is an action item on a closed application.
The interval elapses again while the first action is still open. R-135 says an action shall be raised and does not say how many times, so whether repetition is correct is unsettled. The observable either way is more than one open action for a single application.

## S-17 Outbound gate

Serves: R-129, R-136

**Inputs**
- intent: what is about to leave the machine, required, one of send an email, upload a document, or export a file
- artefacts: the document versions the intent would carry, required
- document_approvals: the approval records for exactly those versions, required by R-129
- message_approval: the explicit approval for this specific message, required by R-136 when the intent is to send email

**Outputs**
- decision: permitted or refused
- refusal_reason: on refusal, the artefact or message that lacks approval, named specifically rather than reported as a category
- gate_record: one per decision, so that any transmission with no gate record is detectable afterwards

**Error cases**
An email send carries approved documents but no per message approval. R-136 requires approval of the message itself, separately from the documents, so the send is refused and the refusal names the missing message approval.
A document approval exists but for an earlier version than the one being sent. The approval does not transfer across versions, so the send is refused, and the observable is an approval record whose document version does not match the artefact.
An approval is reused for a second message. Per message means one approval authorises one message, so the second send is refused, and the observable is one approval identifier appearing against two send records.
A draft is created rather than sent. R-136 forbids sending without approval and says nothing about drafting, so a draft is permitted and the observable is a draft that exists with no send record. Whether draft creation should itself require approval is not settled by this register.
A transmission path exists that does not consult this gate. R-129 and R-136 are then unenforced no matter how correct this seam is, and the only observable is a send, upload or export with no gate record behind it, which is why the gate record exists.

## S-18 Generation provenance record

Serves: R-137

**Inputs**
- document_version: the exact version the provenance describes, required
- model_id: the model version that produced it, required, and a version rather than a family name
- prompt_version: the prompt version used, required
- evidence_ids_used: the evidence records the document actually cites, required
- rubric_version: the rubric version the document was scored against, required
- produced_at: required

**Outputs**
- provenance_record: retrievable for any generated document version, carrying all six values
- provenance_status: complete or incomplete, with the missing values named

**Error cases**
A generated document exists with no provenance record. Every statement about which model wrote it is then a claim and not evidence, and the observable is a document version absent from the provenance index.
The model identifier records a family name rather than a specific version. R-137 asks which model produced the document, and a family name cannot distinguish two runs months apart. The observable is a provenance record that cannot be used to reproduce or explain a difference between two documents.
evidence_ids_used records the records that were supplied to the model rather than the records the document actually cites. The provenance overstates the evidence base, and the observable is a difference between the provenance list and the claim map.
The rubric version is read at query time rather than stored at scoring time. The record then always reports whatever the current rubric is, the stored score silently changes meaning when the rubric changes, and the observable is a provenance record whose rubric version tracks the file rather than the event.

## S-19 Portfolio piece write

Serves: R-125

**Inputs**
- title: the display name of the piece, required
- url: the address the piece lives at, required, and the address D-04 checks resolves
- kind: one of repository, article, talk, product or other, required
- topics: the technologies or domains the piece evidences, required, and the field relevance to an advertisement is computed against
- evidence_record_id: the evidence record this piece is also asserted as, optional, present only when the piece is claimed in a document

**Outputs**
- portfolio_piece_id: the identifier S-05 draws candidates by
- write_status: one of "stored" or "rejected", with the missing field named on rejection

**Error cases**
A piece is written with an empty topics list. Nothing in R-125 forbids it, and the piece is stored. What is observable is a piece that can never be selected on relevance, because relevance is computed against topics, so it sits in the candidate set and is omitted every time with a rationale that says nothing.
The address does not resolve at write time. Nothing in R-125 requires the address be checked when the piece is written, so it is stored and the failure surfaces only at D-04 on a rendered document, which is after the piece has already been selected and after the document has been composed around it.
Two pieces are written for the same work under different addresses. Both enter the candidate set and both may be selected, and the observable is two selected pieces carrying the same title.
evidence_record_id is supplied and names a record that does not exist. The write succeeds because R-125 does not make the reference mandatory, and the failure surfaces at S-09 as an untraceable claim rather than here as a rejected write.
A piece is edited or removed after a document has cited it. This is the same shape as the S-04 case: the document's claim no longer matches the piece behind it while the identifier still resolves, and no requirement here settles whether a cited piece may be changed.

## S-20 Visual style approval

Serves: R-127

**Inputs**
- style_id: the style the decision concerns, required
- decision: one of "approve" or "withdraw", required, since a style becoming approved and a style ceasing to be approved are the same boundary
- decided_at: when the decision was made, required

**Outputs**
- approved_style_id: the style approved after this decision, or absent when the decision withdrew the only approval
- previous_approved_style_id: what was approved before, so that a change of style is readable after the fact rather than inferred
- decision_record: the style, the decision, and when it was made

**Error cases**
A second style is approved while one is already approved. R-127 says the user's approved visual style in the singular, so approving a second must withdraw the first, and the observable of a failure is two styles carrying approved true at once, which is the F-12 condition in pm/05-architecture.md.
No style has ever been approved. S-10 then refuses every render, so nothing can be scored on the dimensions measured over the rendered artefact and nothing reaches approval. The observable is a refused render naming an approved style that does not exist.
Approval is withdrawn after documents have been rendered under that style. Those files already exist and R-127 does not say whether they must be re-rendered or withdrawn, so the observable is a rendered document citing a style that is no longer approved, and this seam cannot settle which is correct.
A style is approved that has never produced a rendered document. Nothing is known about whether it renders text a machine can read, which is what D-07 measures, so the observable is an approved style with no rendered artefact behind it and no evidence that the approval is safe.

## S-21 Rubric version adoption

Serves: R-126, R-128

**Inputs**
- version_label: the human readable version being brought into force, required
- source_document: the rubric this version is taken from, required, which today is pm/03-evals.md
- dimension_set: the nine dimension identifiers with the thresholds the source document records, required, including which thresholds it records as unestablished
- adopted_at: when this version comes into force, required

**Outputs**
- rubric_version_id: the identifier every score and every generated document records under R-137
- dimension_records: one per dimension, carrying its identifier, its name, whether its threshold is established, and where established, the value, the unit and the direction
- unestablished_thresholds: the dimensions that cannot return pass or fail under this version, named at adoption rather than discovered at scoring

**Error cases**
A version is adopted whose dimension_set does not carry all nine identifiers. Scoring then ranges over fewer dimensions than the rubric defines and a document is reported complete against a partial set. The observable is a version whose dimension record count is not nine.
A version is adopted while documents are in flight. A document generated against the previous version is then scored against this one, which S-08 already treats as an error, and R-137 is what makes it visible by requiring the version be recorded at both ends.
Six threshold entries across four dimensions are recorded as unestablished today. Adoption succeeds, and no document scored under this version can ever be fully passing. The observable is an adoption whose unestablished_thresholds output is not empty.
The source document is edited after adoption without a new version being adopted. The stored version label no longer describes the rubric text it names. Nothing in the data contract fingerprints the source document, so this is not detectable from the stored record, which is a gap rather than a behaviour.

## S-22 User settings write

Serves: R-122, R-127, R-134, R-135, R-138

**Inputs**
- setting_name: which of the settings the data contract carries is being written, required
- value: the value the user is setting, required on a set
- action: one of "set" or "unset", required, because unset must be reachable and must not be expressible as a value
- set_at: when the user set it, required on a set

**Outputs**
- setting_record: the setting, its value, and whether it has ever been set
- unset_settings: the settings holding no value, named rather than served as defaults

**Error cases**
Daily discovery is enabled while match_criteria has never been set. R-138 requires the user to define the criteria before discovery runs and forbids the system inferring them, so the write may record the enablement and discovery must not run. What is observable is an enabled flag beside an unset criteria value, which is the empty feed with a named cause that S-03 already describes.
The follow up interval is read before it was ever set and a default is served as though the user chose it. R-135 makes the interval user set, so this seam must keep unset distinguishable from zero, and the observable of a failure is behaviour running on a number no user record shows being set.
approved_visual_style_id is set to a style whose own approved flag is false. Two records then disagree about which style is approved. S-10 must treat the style registry as the authority, and the observable is a settings value naming a style that S-20 never approved.
match_criteria is changed after feeds have been produced under the old value. E-15 stores the interval in force on each follow up action so that history is not rewritten, and nothing equivalent exists for match_criteria. The observable is a past feed whose criteria cannot be recovered, and no requirement asks for one.

## S-23 Posting identity resolution

Serves: R-139

**Inputs**
- candidate_advertisement: the newly stored advertisement with its employer, role title and source text, required
- existing_advertisements: those already stored with the same three values, required
- overlap_rule: the rule by which two source texts count as overlapping, required, and not defined by R-139

**Outputs**
- posting_group_id: the group the candidate joins, newly issued when nothing matches
- matched_advertisement_ids: the advertisements judged to be the same posting
- overlap_measure: the measure computed for each match, so the decision can be read back rather than trusted

**Error cases**
Employer or role title is the unknown token because extraction failed. Two unextracted advertisements then share a key of unknown and unknown and would be collapsed into one posting. Unknown is an undetermined employer and not a shared one, so the seam must refuse to group on unknown keys, and the observable is two advertisements grouped with no determined employer between them.
R-139 says overlapping source text and names no threshold. The check recorded against R-139 in pm/03-requirements.md uses at least half the word set, which is a number that requirement does not supply. The observable is a pair grouped or not grouped entirely on a value no requirement fixes.
The same posting is reworded between two boards and falls below the overlap threshold. It stays two postings and is presented twice, which is the failure R-139 exists to prevent, and the only observable is the user recognising the job.
Two genuinely different roles at one employer carry the same role title and a largely boilerplate body. They are collapsed into one posting and one of them is never presented. This is the opposite error, it is silent, and no stored record distinguishes it from a correct grouping.
Grouping runs before extraction has produced employer and role title. There is nothing to key on, the advertisement enters its own group, and nothing revisits it once extraction completes. The observable is a single member group beside a duplicate that was ingested later.

## S-24 Sentence map completeness check

Serves: R-143

This is the seam that stands between a sentence no evidence record supports and an employer reading it.

**Inputs**
- document_version: the exact revision being checked, required
- body_text: the text of that revision, required
- claim_map: the claim to evidence mapping the generating seam produced, required, from S-06 or S-07
- sentence_rule: the rule by which body_text is divided into sentences, required, and not defined by R-143

**Outputs**
- sentence_total: how many sentences were found, which is the denominator this check is judged on
- mapped_total: how many of them appear in claim_map
- unmapped_sentences: each sentence present in the document and absent from the map, with its position
- verdict: one of "complete" or "blocked", where blocked stops the document reaching the approval surface under R-143

**Error cases**
A sentence is present in body_text and absent from claim_map. The document is blocked and the sentence is named with its position. This is the case the seam exists for. S-09 blocks a claim that cannot be traced to a record; R-143 blocks a sentence that was never offered as a claim at all, and S-09 states in its own error cases that it never sees such a sentence.
The sentence rule used here and the rule the composer used to build claim_map disagree. A sentence the composer mapped is counted unmapped and a correct document is blocked, or two sentences are joined and an unsupported clause rides into an approved document inside a sentence that matched. The observable is a mapped_total that does not equal the claim count recorded for the same revision.
R-143 says factual sentence and nothing in the register distinguishes a factual sentence from any other. The conservative reading is every sentence, which blocks a document for a greeting or a closing line. Any exemption list is a hole in the gate, and no requirement authorises one, so the seam runs on the conservative reading and the cost is false blocks.
The document is edited and the check is not rerun. The verdict then describes an earlier revision, and the observable is a completeness verdict whose revision is not the current one, which is the same shape as the stale score at S-12.
The check runs on a document with no body text. Every sentence is trivially mapped over an empty set. The verdict is vacuous rather than complete, and a document that passes this way must be visibly distinguished from one that earned it.

## Coverage

Every requirement in the approved list maps to at least one seam, and every seam maps to at least one requirement.

- R-117 -> S-04
- R-118 -> S-09, S-11
- R-119 -> S-01
- R-120 -> S-01, S-02
- R-121 -> S-02
- R-122 -> S-03, S-22
- R-123 -> S-06
- R-124 -> S-05, S-06
- R-125 -> S-05, S-19
- R-126 -> S-07, S-08, S-21
- R-127 -> S-10, S-20, S-22
- R-128 -> S-08, S-21
- R-129 -> S-11, S-17
- R-130 -> S-09, S-11
- R-131 -> S-12
- R-132 -> S-13
- R-133 -> S-14
- R-134 -> S-15, S-22
- R-135 -> S-16, S-22
- R-136 -> S-17
- R-137 -> S-02, S-06, S-07, S-18
- R-138 -> S-22
- R-139 -> S-23
- R-140 -> S-09
- R-141 -> S-11
- R-142 -> S-13
- R-143 -> S-24

27 of 27 requirements served. No requirement is left without a seam.

## Open gaps

These are named rather than resolved, because nothing in the approved requirements or in pm/03-evals.md settles them.

- R-126 names "the register and language dimensions of pm/03-evals.md". That file has one dimension covering cover letter language, D-05, and no dimension named register. S-07 cannot be told which dimensions it is being held to beyond D-05.
- S-03 needs a matching rule and no requirement defines one. Discovery cannot be built from R-122 alone. R-138 was approved after this was written and narrows it rather than closing it: the user must define the criteria and the system must not infer them, which S-22 now carries, but no requirement says how a defined criterion is matched against a posting.
- Six thresholds across four dimensions of pm/03-evals.md are recorded as unestablished. S-08 can only return not decidable for those, so a document can never be fully passing or fully failing on them.
- R-122 keys "presented once" to an advertisement, and the same posting cross listed on two boards produces two advertisements. Nothing in the requirements says whether those are one posting or two. R-139 was approved after this was written and settles it: they are one posting, resolved at S-23 and grouped by the posting_group_id the data contract now carries. What R-139 does not settle is the overlap threshold at which two texts count as the same posting.
- R-117 does not forbid an evidence record whose source is a document this system generated, so circular provenance is permitted by the requirement even though it makes R-118 vacuous for that claim. R-140 was approved after this was written and closes it: such a record is not accepted as provenance for a claim, which S-09 now enforces and INV-26 checks.
- R-128 marks a document failing and R-129 gives the user approval. Nothing says whether a failing document may be approved, so S-11 permits it and records the failing dimensions. R-141 was approved after this was written and settles it: every failed dimension is presented and approval is permitted only as an explicit recorded override, which S-11 now carries. R-141 covers a failing dimension and says nothing about a document blocked under R-118 or R-143, so the override must not be readable as a route past a traceability block.
- R-132 records applications made through this system. An application made on a company portal never reaches S-13, and no requirement closes that path. R-142 was approved after this was written and closes it: such an application is recordable with employer, role, date and documents sent, which S-13 now carries and which required job_ad_id to become optional in the data contract.
- R-143 says every factual sentence, and nothing in the register distinguishes a factual sentence from any other. S-24 runs on the conservative reading, every sentence, which blocks a document for a greeting or a closing line. No requirement authorises an exemption list and any exemption would be a hole in the gate.
- R-143 assumes a document divides into sentences and defines no rule for doing it. S-24 takes the rule as an input and stores it with the result. Two runs under different rules produce different denominators for the same document.
- S-21 adopts a rubric version from a source document and nothing fingerprints that document. An edit to the source after adoption is not detectable from the stored version record.
- S-22 writes match_criteria and nothing records which criteria a past feed ran under. A follow up action stores the interval in force on the action; there is no equivalent for discovery, so a past feed cannot be explained after the criteria change.
- R-137 requires provenance for generated documents. Advertisement extraction at S-02 is also model output and carries no provenance requirement, so which model extracted a posting is not recorded. This reading of R-137 was too narrow: the requirement text covers every model output and names advertisement extraction explicitly. S-02 now returns model_id and E-03 now carries it, checked by INV-22. What remains open is that an advertisement is stored at intake before extraction runs, so the field is absent on an advertisement that has not been extracted.
