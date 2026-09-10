# Data contract: job application pipeline

This file states what the system is allowed to store, in entities and fields, and the invariants that must hold across them. It is a contract, not a design: it names no database, no file format, no library, no host, and no table layout. Types are contract level (string, integer, boolean, timestamp, enum with its values listed, array of a type, reference to an entity), never vendor types. Every entity here exists because a numbered requirement demands it, and every requirement is accounted for in the Coverage section at the end. How any of this is physically stored, indexed or migrated is step 5 and is deliberately absent.

Two conventions used below.

- The detection commands address the record set through the environment variable `CAREER_OS_STORE`, defaulting to the unbound placeholder path `./store-unbound`. That path does not exist and is not a storage decision. It is a hole that step 5 binds to a real location.
- The commands assume each record is readable as one JSON object per record under a collection name. That is a reading convention for the checks only, so that the invariants are executable today rather than aspirational prose. Step 5 may bind them to anything, provided the same predicates remain checkable.

Commands are run from the repository root.

## Entities

### E-01 EvidenceRecord

Serves: R-117, R-118, R-123, R-124, R-130, R-137

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier, cited by documents and claims |
| claim_text | string | yes | none | the assertion about the user's history in the form it may appear in a document |
| kind | enum(role, achievement, skill, education, metric, publication, other) | yes | none | needed because R-124 selects experience content specifically, so experience must be distinguishable from other evidence |
| source | string | yes | none | where the claim comes from, per R-117 |
| source_kind | enum(document, url, system_record, person_attestation, self_reported) | yes | none | what sort of thing the source is, so a reader can judge it |
| date | timestamp | yes | none | the date the record carries, per R-117. Whether this is the date of the event or the date of the source is an open ambiguity, recorded rather than resolved |

### E-02 PortfolioPiece

Serves: R-125

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| title | string | yes | none | display name of the piece |
| url | string | yes | none | the address the piece lives at, which D-04 of pm/03-evals.md checks resolves |
| kind | enum(repository, article, talk, product, other) | yes | none | what the piece is |
| topics | array of string | yes | empty array | the technologies or domains the piece evidences, which is what relevance to an advertisement is computed against |
| evidence_record_id | reference to E-01 | no | none | present when the piece is also asserted as a claim in a document, so that R-118 traceability holds for it |

### E-03 JobAd

Serves: R-119, R-120, R-121, R-122, R-123, R-124, R-125, R-137, R-139

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| intake_kind | enum(url, pasted_text) | yes | none | the two accepted intake forms, per R-119 |
| source_url | string | no | none | present only when intake_kind is url |
| source_text | string | yes | none | the full advertisement text, retained unmodified, per R-120 |
| source_text_digest | string | yes | none | fingerprint of source_text taken at ingest, so that later modification is detectable. Without it, unmodified is an unfalsifiable claim |
| ingested_at | timestamp | yes | none | when the advertisement entered the system |
| employer | string | yes | unknown | extracted per R-120, literal unknown when undetermined per R-121 |
| role_title | string | yes | unknown | as above |
| seniority | string | yes | unknown | as above |
| location | string | yes | unknown | as above |
| work_arrangement | enum(remote, hybrid, onsite, unknown) | yes | unknown | as above |
| required_skills | array of string | yes | empty array | extracted per R-120 |
| required_skills_determined | boolean | yes | false | an empty list cannot distinguish an advertisement listing no required skills from a failed extraction, so R-121 forces this companion flag |
| preferred_skills | array of string | yes | empty array | extracted per R-120 |
| preferred_skills_determined | boolean | yes | false | same reason as required_skills_determined |
| model_id | string | no | none | which model produced this advertisement's extraction, per R-137, which names every model output including advertisement extraction. Absent before extraction has been recorded, because S-01 stores an advertisement before S-02 runs. Without this field the extraction half of R-137 has nothing to record and can never pass |
| posting_group_id | string | no | none | the posting this advertisement is an instance of. Two advertisements sharing employer, role title and overlapping source text carry the same value, which is how R-139 stores one posting rather than recomputing it at every read. Absent until employer and role title are determined, since there is nothing to key on before that |

### E-04 AdPresentation

Serves: R-122

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| job_ad_id | reference to E-03 | yes | none | the advertisement that was shown |
| presented_at | timestamp | yes | none | when it was shown, which is what once each is measured against |
| disposition | enum(presented, dismissed, applied) | yes | presented | the outcome that makes an advertisement ineligible for re-presentation |
| disposition_at | timestamp | no | none | set when disposition moves off presented |

### E-05 VisualStyle

Serves: R-127

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| name | string | yes | none | the style's name |
| approved | boolean | yes | false | R-127 says the user's approved visual style, so approval is a stored fact, not an assumption |
| approved_at | timestamp | no | none | set when approved becomes true |

### E-06 RubricVersion

Serves: R-126, R-128, R-137

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier, cited by every generated document per R-137 |
| version_label | string | yes | none | the human readable version this scoring ran against |
| source_document | string | yes | none | the rubric this version was taken from, which today is pm/03-evals.md |
| adopted_at | timestamp | yes | none | when this version became the one in force |

### E-07 RubricDimension

Serves: R-126, R-128

| field | type | required | default | notes |
|---|---|---|---|---|
| id | enum(D-01, D-02, D-03, D-04, D-05, D-06, D-07, D-08, D-09) | yes | none | exactly the nine dimension IDs declared in pm/03-evals.md, in order: visual styling and layout, word choices in experience bullets, content matching the job description, portfolio piece selection, cover letter language, conformance to the measured evidence base, machine parseability, verifiability of every claim, front loading for a scanning reader |
| rubric_version_id | reference to E-06 | yes | none | the version this dimension belongs to |
| name | string | yes | none | the dimension name as written in the rubric |
| threshold_established | boolean | yes | false | false where the rubric records the threshold as unestablished. Six threshold entries in pm/03-evals.md are in that state today, so this field is not hypothetical |
| threshold_value | string | no | none | string rather than a number because units differ across dimensions (pages, counts, percentages) |
| threshold_unit | enum(count, pages, percent, boolean) | no | none | absent when threshold_established is false |
| direction | enum(at_most, at_least, exactly) | no | none | which side of the threshold fails, per R-128 |

### E-08 GeneratedDocument

Serves: R-123, R-126, R-127, R-128, R-129, R-131, R-137, R-141

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| job_ad_id | reference to E-03 | yes | none | the advertisement the document was tailored for, per R-123 |
| document_kind | enum(resume, cover_letter) | yes | none | the two kinds R-123 and R-126 name |
| revision | integer | yes | 1 | incremented on every user edit, because R-131 requires a re-score after each edit and a score must attach to the thing scored |
| body_text | string | yes | none | the document content |
| model_id | string | yes | none | which model produced it, per R-137 |
| rubric_version_id | reference to E-06 | yes | none | which rubric version it was scored against, per R-137 |
| evidence_record_ids | array of reference to E-01 | yes | empty array | which evidence records it used, per R-137 |
| visual_style_id | reference to E-05 | no | none | set when rendered, per R-127 |
| render_format | enum(pdf) | no | none | R-127 names PDF and nothing else |
| render_uri | string | no | none | where the rendered file is, set only once rendered |
| approval_state | enum(draft, blocked, awaiting_approval, approved) | yes | draft | blocked is the R-118 state, approved is the R-129 gate on transmission |
| approved_at | timestamp | no | none | set only when approval_state is approved |
| blocked_claim_ids | array of reference to E-09 | yes | empty array | the untraceable claims R-118 requires be named |
| scoring_state | enum(unscored, passing, failing) | yes | unscored | R-128 marks a document failing |
| failing_dimension_ids | array of string | yes | empty array | the dimensions R-128 requires be named |
| approval_override_reason | string | no | none | the reason recorded when a document whose scoring_state is failing is approved anyway, which R-141 makes the only route to approving one. Absent on every document not approved over a failing dimension, and its absence is what keeps the override explicit rather than assumed. Without this field R-141's recorded override is unstorable |

### E-09 DocumentClaim

Serves: R-118, R-130

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| document_id | reference to E-08 | yes | none | the document the claim appears in |
| document_revision | integer | yes | none | which revision of that document, since edits change the claim set |
| claim_text | string | yes | none | the claim as it appears in the document |
| evidence_record_id | reference to E-01 | no | none | the record the claim came from, which R-130 requires be displayed beside it |
| traceable | boolean | yes | false | false is the condition that triggers the R-118 block |

### E-10 SelectionDecision

Serves: R-124, R-125

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| document_id | reference to E-08 | yes | none | the document the decision was made for |
| candidate_kind | enum(evidence_record, portfolio_piece) | yes | none | R-124 covers experience content, R-125 covers portfolio pieces, and both must record a reason |
| evidence_record_id | reference to E-01 | no | none | set when candidate_kind is evidence_record |
| portfolio_piece_id | reference to E-02 | no | none | set when candidate_kind is portfolio_piece |
| decision | enum(included, omitted) | yes | none | R-124 requires a reason for omission as well as inclusion |
| rationale | string | yes | none | why it was included or omitted, per R-124 and R-125 |
| rank | integer | no | none | the position in the ordering R-124 requires, set only when decision is included |
| matched_required_skills | array of string | yes | empty array | which of the advertisement's required skills this candidate matched, which is the relevance R-124 orders by |

### E-11 DimensionScore

Serves: R-126, R-128, R-131

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| document_id | reference to E-08 | yes | none | the document scored |
| document_revision | integer | yes | none | the revision scored, so R-131 re-scoring after each edit is visible rather than overwritten |
| rubric_version_id | reference to E-06 | yes | none | the version scored against, per R-137 |
| dimension_id | reference to E-07 | yes | none | one of D-01 to D-09 |
| measured_value | string | yes | none | the measured result, in the unit the dimension declares. String because units are heterogeneous across the nine dimensions |
| outcome | enum(pass, fail, unmeasurable) | yes | unmeasurable | unmeasurable is required because six threshold entries in the rubric are unestablished, so some dimensions cannot yield pass or fail today |
| scored_at | timestamp | yes | none | when the score was taken |

### E-12 Application

Serves: R-132, R-133, R-134, R-135, R-142

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| job_ad_id | reference to E-03 | no | none | the advertisement applied to. Optional rather than required, because R-142 requires an application submitted outside this system to be recordable and no advertisement was ever ingested for it. While this was required, such an application could not be stored at all |
| employer | string | yes | none | per R-132 |
| role_title | string | yes | none | per R-132 |
| applied_at | timestamp | yes | none | the date R-132 requires, and the clock R-135 measures from |
| document_ids | array of reference to E-08 | yes | empty array | the documents sent, per R-132 |
| status | enum(applied, acknowledged, screening, interviewing, offer, rejected, withdrawn, no_response) | yes | applied | the current status R-132 records and R-133 surfaces |
| status_source | enum(user_set, derived_from_message) | yes | user_set | distinguishes a status the user set from one derived under R-134 |
| status_updated_at | timestamp | yes | none | when status last changed |
| last_response_at | timestamp | no | none | none means no response has arrived, which is the R-135 trigger condition |

### E-13 InboundMessage

Serves: R-134

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| external_message_id | string | yes | none | the identifier in the mail system, without which the R-134 citation does not resolve to anything the user can open |
| received_at | timestamp | yes | none | when it arrived |
| sender | string | yes | none | who sent it |
| subject | string | yes | none | the subject line |
| application_id | reference to E-12 | no | none | the application it was matched to, absent when unmatched |

### E-14 StatusDerivation

Serves: R-134

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| application_id | reference to E-12 | yes | none | the application whose status was derived |
| inbound_message_id | reference to E-13 | yes | none | the message the derivation cites, per R-134 |
| derived_status | enum(applied, acknowledged, screening, interviewing, offer, rejected, withdrawn, no_response) | yes | none | same value set as Application.status |
| derived_at | timestamp | yes | none | when the derivation was made |

### E-15 FollowUpAction

Serves: R-135

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| application_id | reference to E-12 | yes | none | the silent application |
| raised_at | timestamp | yes | none | when the action was raised |
| due_after_days | integer | yes | none | the interval that was in force when it was raised, stored on the action so that a later settings change does not rewrite history |
| state | enum(open, done, dismissed) | yes | open | the action's own lifecycle |

### E-16 OutboundMessage

Serves: R-136

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| application_id | reference to E-12 | no | none | the application the message concerns |
| recipient | string | yes | none | who it goes to |
| subject | string | yes | none | the subject line |
| body_text | string | yes | none | the message body the user approves |
| approved_at | timestamp | no | none | none means not approved, and R-136 forbids sending in that state |
| approval_scope | enum(this_message) | yes | this_message | the enum has exactly one legal value by construction, because R-136 forbids any standing or blanket approval |
| sent_at | timestamp | no | none | none means not sent |

### E-17 UserSetting

Serves: R-122, R-127, R-134, R-135, R-138

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| daily_discovery_enabled | boolean | yes | false | the where clause of R-122 |
| email_access_granted | boolean | yes | false | the where clause of R-134 |
| follow_up_interval_days | integer | yes | none | the user set interval R-135 names. No default is supplied because inventing one would be the system choosing on the user's behalf |
| approved_visual_style_id | reference to E-05 | no | none | the style R-127 renders in |
| match_criteria | string | no | none | the user's standing definition of what counts as a matching advertisement, per R-138. No default is supplied and nothing is inferred, because R-138 forbids the system inferring them, so an unset value must stay unset and stop discovery rather than be filled in. Without this field R-138 has nothing to check |

### E-18 SentenceMapCheck

Serves: R-143

| field | type | required | default | notes |
|---|---|---|---|---|
| id | string | yes | none | stable identifier |
| document_id | reference to E-08 | yes | none | the document whose sentences were counted |
| document_revision | integer | yes | none | the revision counted, because an edit changes the sentence set, which is the same reason E-11 carries the revision |
| sentence_total | integer | yes | none | how many sentences were found in that revision's body_text. This is the denominator R-143 is judged on, and it is what makes a check over an empty document visible as vacuous rather than complete |
| mapped_total | integer | yes | none | how many of those sentences appear in that document's claim map at that revision, which is the condition R-143 states |
| unmapped_sentences | array of string | yes | empty array | the sentences present in the document and absent from the claim map, named rather than counted, because R-143 blocks the document on them and a bare count cannot be read back |
| sentence_rule | string | yes | none | the rule by which body_text was divided into sentences. R-143 defines no such rule, so the rule used is stored beside the result; without it, two runs that disagree cannot be told apart from a document that changed |
| checked_at | timestamp | yes | none | when the census was taken |

## Invariants

Status values are limited to three. `red` means the command ran and exited non-zero for the stated reason. `vacuous` means the command ran over an empty or absent set, which is not a pass. There is no fourth value, and in particular there is no green here, because nothing is built.

| ID | invariant | detection command | status |
|---|---|---|---|
| INV-01 | Every EvidenceRecord has a non-empty source and a non-empty date. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('evidence');bad=[r.get('id') for r in rs if not r.get('source') or not r.get('date')];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-02 | Every DocumentClaim marked traceable references an EvidenceRecord id that exists. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];ids={r.get('id') for r in L('evidence')};rs=L('document_claims');bad=[c.get('id') for c in rs if c.get('traceable') and c.get('evidence_record_id') not in ids];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-03 | Every GeneratedDocument that has at least one untraceable claim is in approval_state blocked and its blocked_claim_ids names exactly those claims. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];cl=L('document_claims');rs=L('documents');u=lambda d:sorted([c.get('id') for c in cl if c.get('document_id')==d.get('id') and not c.get('traceable')]);bad=[d.get('id') for d in rs if u(d) and (d.get('approval_state')!='blocked' or sorted(d.get('blocked_claim_ids',[]))!=u(d))];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-04 | A JobAd has a non-empty source_url if and only if its intake_kind is url. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('job_ads');bad=[a.get('id') for a in rs if (a.get('intake_kind')=='url')!=bool(a.get('source_url'))];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-05 | Every JobAd's stored source_text still hashes to the source_text_digest recorded at ingest. | `python3 -c "import os,glob,json,hashlib;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('job_ads');bad=[a.get('id') for a in rs if hashlib.sha256((a.get('source_text') or '').encode()).hexdigest()!=a.get('source_text_digest')];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-06 | No extracted field on a JobAd is empty or absent: an undetermined scalar carries the literal unknown, and both skill lists carry their determined flag. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];F=('employer','role_title','seniority','location','work_arrangement');K=('required_skills','required_skills_determined','preferred_skills','preferred_skills_determined');rs=L('job_ads');bad=[a.get('id') for a in rs if any(not a.get(f) for f in F) or any(k not in a for k in K)];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-07 | At most one AdPresentation exists per job_ad_id. | `python3 -c "import os,glob,json,collections;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('ad_presentations');n=collections.Counter(p.get('job_ad_id') for p in rs);bad=[k for k,v in n.items() if v>1];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-08 | No AdPresentation was shown after its advertisement was dismissed or applied to: presented_at never exceeds disposition_at. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('ad_presentations');bad=[p.get('id') for p in rs if p.get('disposition') in ('dismissed','applied') and p.get('disposition_at') and p.get('presented_at')>p.get('disposition_at')];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-09 | Every evidence id on a GeneratedDocument exists in the evidence set, and no resume has an empty evidence_record_ids. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];ids={r.get('id') for r in L('evidence')};rs=L('documents');bad=[d.get('id') for d in rs if any(e not in ids for e in d.get('evidence_record_ids',[])) or (d.get('document_kind')=='resume' and not d.get('evidence_record_ids'))];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-10 | Every SelectionDecision carries a non-empty rationale. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('selection_decisions');bad=[s.get('id') for s in rs if not (s.get('rationale') or '').strip()];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-11 | Within a document the ranks of included SelectionDecisions are unique and contiguous from 1, and no omitted decision carries a rank. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('selection_decisions');inc=lambda k:[s for s in rs if s.get('document_id')==k and s.get('decision')=='included'];bad=[k for k in {s.get('document_id') for s in rs} if sorted([s.get('rank') or 0 for s in inc(k)])!=list(range(1,1+len(inc(k))))]+[s.get('id') for s in rs if s.get('decision')=='omitted' and s.get('rank') is not None];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-12 | For every document revision that exists there is exactly one DimensionScore per dimension of that document's rubric version. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];dims=L('rubric_dimensions');sc=L('dimension_scores');rs=L('documents');bad=[d.get('id') for d in rs if sorted(s.get('dimension_id') for s in sc if s.get('document_id')==d.get('id') and s.get('document_revision')==d.get('revision'))!=sorted(x.get('id') for x in dims if x.get('rubric_version_id')==d.get('rubric_version_id'))];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-13 | Every rendered GeneratedDocument references a VisualStyle whose approved is true. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];ok={v.get('id') for v in L('visual_styles') if v.get('approved')};rs=L('documents');bad=[d.get('id') for d in rs if d.get('render_uri') and d.get('visual_style_id') not in ok];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-14 | Every GeneratedDocument with at least one failing DimensionScore at its current revision is in scoring_state failing and names exactly those dimensions. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];sc=L('dimension_scores');rs=L('documents');f=lambda d:sorted({s.get('dimension_id') for s in sc if s.get('document_id')==d.get('id') and s.get('document_revision')==d.get('revision') and s.get('outcome')=='fail'});bad=[d.get('id') for d in rs if f(d) and (d.get('scoring_state')!='failing' or sorted(set(d.get('failing_dimension_ids',[])))!=f(d))];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-15 | Every threshold entry in the rubric source carries an established value, so that every DimensionScore can be compared against something. | `python3 -c "import re;t=open('pm/03-evals.md').read();e=re.findall(r'^- (D-[0-9][0-9])',t,re.M);bad=re.findall(r'- (D-[0-9][0-9])[^\n]*threshold unestablished',t);print('threshold entries checked',len(e),'unestablished',len(bad),'dimensions affected',sorted(set(bad)));raise SystemExit(1 if bad else 0)"` | red, run 2026-09-09, 6 of 19 threshold entries are unestablished, affecting D-01, D-04, D-05 and D-09 |
| INV-16 | No document id appears in an Application's document_ids unless that document is approved with an approved_at set. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];docs={d.get('id'):d for d in L('documents')};rs=L('applications');bad=[(a.get('id'),x) for a in rs for x in a.get('document_ids',[]) if docs.get(x,{}).get('approval_state')!='approved' or not docs.get(x,{}).get('approved_at')];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-17 | Every Application has a non-empty employer, role_title, applied_at and status. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('applications');bad=[a.get('id') for a in rs if not all(a.get(k) for k in ('employer','role_title','applied_at','status'))];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-18 | Every StatusDerivation cites an InboundMessage that exists, and every Application whose status_source is derived_from_message has at least one StatusDerivation. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];m={x.get('id') for x in L('inbound_messages')};dv=L('status_derivations');ap=L('applications');bad=[d.get('id') for d in dv if d.get('inbound_message_id') not in m]+[a.get('id') for a in ap if a.get('status_source')=='derived_from_message' and not [d for d in dv if d.get('application_id')==a.get('id')]];print('checked',len(dv)+len(ap),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-19 | Every FollowUpAction points at an existing Application with no recorded response, carries the interval in force, and was raised no earlier than that interval after the application date. | `python3 -c "import os,glob,json,datetime;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];ap={a.get('id'):a for a in L('applications')};st=L('settings');iv=(st[0].get('follow_up_interval_days') if st else None);P=datetime.datetime.fromisoformat;rs=L('follow_up_actions');bad=[f.get('id') for f in rs if f.get('application_id') not in ap or ap[f.get('application_id')].get('last_response_at') or not f.get('due_after_days') or f.get('due_after_days')!=iv or (P(f.get('raised_at'))-P(ap[f.get('application_id')].get('applied_at'))).days<f.get('due_after_days')];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-20 | No OutboundMessage has a sent_at unless it also has an approved_at and an approval_scope of this_message. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('outbound_messages');bad=[m.get('id') for m in rs if m.get('sent_at') and (not m.get('approved_at') or m.get('approval_scope')!='this_message')];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-21 | Every GeneratedDocument records a non-empty model_id, a rubric_version_id that exists, and a non-empty evidence_record_ids. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rv={r.get('id') for r in L('rubric_versions')};rs=L('documents');bad=[d.get('id') for d in rs if not d.get('model_id') or d.get('rubric_version_id') not in rv or not d.get('evidence_record_ids')];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-22 | Every JobAd that carries a recorded extraction records the model that produced it. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=L('job_ads');E=lambda a:any((a.get(f) or 'unknown')!='unknown' for f in ('employer','role_title','seniority','location','work_arrangement')) or a.get('required_skills_determined') or a.get('preferred_skills_determined');ex=[a for a in rs if E(a)];bad=[a.get('id') for a in ex if not a.get('model_id')];print('checked',len(ex),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-23 | Every UserSetting with daily_discovery_enabled true carries a non-empty match_criteria. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=[s for s in L('settings') if s.get('daily_discovery_enabled')];bad=[s.get('id') for s in rs if not s.get('match_criteria')];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-24 | Any two JobAds with a determined employer and role title that share both, and whose source texts overlap by at least half their words, carry the same non-empty posting_group_id. | `python3 -c "import os,glob,json,itertools;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=[a for a in L('job_ads') if (a.get('employer') or 'unknown')!='unknown' and (a.get('role_title') or 'unknown')!='unknown'];k=lambda a:((a.get('employer') or '').strip().lower(),(a.get('role_title') or '').strip().lower());o=lambda x,y:len(set(x.split()).intersection(y.split()))/max(1,len(set(x.split()).union(y.split())));bad=[(a.get('id'),b.get('id')) for a,b in itertools.combinations(rs,2) if k(a)==k(b) and o((a.get('source_text') or '').lower(),(b.get('source_text') or '').lower())>=0.5 and (not a.get('posting_group_id') or a.get('posting_group_id')!=b.get('posting_group_id'))];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-25 | At most one AdPresentation exists per posting_group_id, which is what R-139 means by presenting one posting once. | `python3 -c "import os,glob,json,collections;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];g={a.get('id'):a.get('posting_group_id') for a in L('job_ads')};rs=L('ad_presentations');n=collections.Counter(g.get(p.get('job_ad_id')) for p in rs);bad=[x for x,v in n.items() if v>1];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-26 | No DocumentClaim marked traceable rests on an EvidenceRecord whose source_kind is document and whose source resolves to a document this system generated. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];gen={str(d.get('id')) for d in L('documents')}.union({str(d.get('render_uri')) for d in L('documents') if d.get('render_uri')});ev={r.get('id'):r for r in L('evidence')};rs=[c for c in L('document_claims') if c.get('traceable')];bad=[c.get('id') for c in rs if c.get('evidence_record_id') in ev and ev[c.get('evidence_record_id')].get('source_kind')=='document' and str(ev[c.get('evidence_record_id')].get('source')) in gen];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-27 | No GeneratedDocument whose scoring_state is failing is in approval_state approved without a non-empty approval_override_reason. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=[d for d in L('documents') if d.get('scoring_state')=='failing'];bad=[d.get('id') for d in rs if d.get('approval_state')=='approved' and not (d.get('approval_override_reason') or '').strip()];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-28 | Every Application recorded with no job_ad_id still carries employer, role_title, applied_at and a document_ids list. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];rs=[a for a in L('applications') if not a.get('job_ad_id')];bad=[a.get('id') for a in rs if not all(a.get(k) for k in ('employer','role_title','applied_at')) or a.get('document_ids') is None];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-29 | Every GeneratedDocument has a SentenceMapCheck at its current revision, so that no document passes R-143 by never having been counted. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];ch=L('sentence_map_checks');rs=L('documents');bad=[d.get('id') for d in rs if not [c for c in ch if c.get('document_id')==d.get('id') and c.get('document_revision')==d.get('revision')]];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |
| INV-30 | Every GeneratedDocument whose SentenceMapCheck at its current revision names at least one unmapped sentence is in approval_state blocked. | `python3 -c "import os,glob,json;S=os.environ.get('CAREER_OS_STORE','./store-unbound');L=lambda c:[json.load(open(f)) for f in sorted(glob.glob(S+'/'+c+'/*.json'))];ch=L('sentence_map_checks');rs=L('documents');u=lambda d:[s for c in ch if c.get('document_id')==d.get('id') and c.get('document_revision')==d.get('revision') for s in c.get('unmapped_sentences',[])];bad=[d.get('id') for d in rs if u(d) and d.get('approval_state')!='blocked'];print('checked',len(rs),'violations',len(bad),bad);raise SystemExit(1 if bad else 0)"` | vacuous, run 2026-09-09, no store exists |

Twenty nine of the thirty commands report a denominator of zero records checked. That is vacuous, not passing. Thirteen of the thirty predicates (INV-01, INV-02, INV-16, INV-20, INV-22, INV-23, INV-24, INV-25, INV-26, INV-27, INV-28, INV-29, INV-30) were additionally exercised against a planted violating record supplied in memory rather than from a store, and each exited 1 and named the violator, so those thirteen are known to be capable of firing. The remaining seventeen have been run but have never been seen red, and are not yet trusted.

## Coverage

- R-117 -> E-01, INV-01
- R-118 -> E-08, E-09, INV-02, INV-03
- R-119 -> E-03, INV-04
- R-120 -> E-03, INV-05, INV-06
- R-121 -> E-03, INV-06
- R-122 -> E-04, E-17, INV-07, INV-08
- R-123 -> E-01, E-03, E-08, INV-09
- R-124 -> E-01, E-10, INV-10, INV-11
- R-125 -> E-02, E-10, INV-10
- R-126 -> E-06, E-07, E-11, INV-12
- R-127 -> E-05, E-08, E-17, INV-13
- R-128 -> E-07, E-08, E-11, INV-14, INV-15
- R-129 -> E-08, E-12, INV-16
- R-130 -> E-09, INV-02
- R-131 -> E-08, E-11, INV-12
- R-132 -> E-12, INV-17
- R-133 -> E-12, INV-17
- R-134 -> E-13, E-14, E-17, INV-18
- R-135 -> E-15, E-17, INV-19
- R-136 -> E-16, INV-20
- R-137 -> E-03, E-06, E-08, INV-21, INV-22
- R-138 -> E-17, INV-23
- R-139 -> E-03, E-04, INV-24, INV-25
- R-140 -> E-01, E-08, E-09, INV-26
- R-141 -> E-08, E-11, INV-27
- R-142 -> E-12, INV-28
- R-143 -> E-08, E-09, E-18, INV-29, INV-30

27 of 27 requirements served. No requirement is unserved.

Every entity is claimed by at least one requirement: E-01 by R-117, E-02 by R-125, E-03 by R-119, E-04 by R-122, E-05 by R-127, E-06 by R-126, E-07 by R-126 and R-128, E-08 by R-123, E-09 by R-118, E-10 by R-124, E-11 by R-126, E-12 by R-132, E-13 by R-134, E-14 by R-134, E-15 by R-135, E-16 by R-136, E-17 by R-122, E-18 by R-143.

Two coverage caveats stated rather than hidden. R-133 asks that status be visible on one surface without opening a file, which is an interface obligation; the only thing this contract can carry is that every Application holds a current status, which INV-17 checks. R-124 requires ordering by relevance, and INV-11 checks only that the ordering is well formed, because whether the order is the correct relevance order is a judgement the evals file scores under D-03, not a property a data check can settle.

## Open ambiguities

These are recorded, not resolved.

1. E-01 date. R-117 says a record carries a source and a date, but does not say whether that date is when the claimed event happened or when the source was created. One field is modelled. If both are needed, this contract is short by one field.
2. E-01 versus E-02. Whether a portfolio piece is a kind of evidence record or a separate noun is not settled by any requirement. They are modelled separately because a portfolio piece carries an address that must resolve, and an evidence record does not.
3. Temporal precision. Career history is often known only to the month, and timestamp implies more precision than the evidence supports. No requirement settles the precision, so timestamp is used throughout and the loss is recorded here.
4. E-11 measured_value is a string because the nine dimensions measure in different units. A requirement that scores be compared or aggregated across dimensions would make that wrong.
5. R-129 forbids transmission before approval, and R-132 records documents sent. Whether an Application may list a document before it is sent, or only after, is not stated. INV-16 takes the stricter reading: anything listed must already be approved.
6. R-143 says factual sentence. Nothing in the register distinguishes a factual sentence from any other, so E-18 counts every sentence, which is the conservative reading and the one the requirement's own check uses. A greeting or a closing line therefore blocks a document unless it is in the claim map. No field here carries an exemption, because an exemption list is a hole in the gate and no requirement authorises one.
7. R-143 assumes a document divides into sentences and defines no rule for doing it. E-18 stores the rule used with the result rather than fixing one here. Two runs under different rules produce different denominators for the same document.
8. R-139 says overlapping source text and names no threshold. INV-24 uses at least half the word set, which is the value the requirement's own check in pm/03-requirements.md uses, not a value R-139 supplies. Where employer or role title is the literal unknown, INV-24 excludes the pair, because unknown is an undetermined employer and not a shared one.
9. R-142 records an application submitted outside this system as one with no job_ad_id. That is indistinguishable from an application whose advertisement reference was lost, and no field records the difference, because R-142 does not name one. INV-16 additionally forbids listing a document this system never approved, so documents sent outside the system that this system did not generate cannot be listed at all.
10. R-137 requires provenance for every model output including advertisement extraction. An advertisement is stored at intake before extraction runs, so model_id is optional on E-03 and INV-22 checks only advertisements that carry a recorded extraction. The row for R-137 in pm/03-requirements.md requires model_id on every advertisement, which cannot hold for one stored and not yet extracted. That register row is not this file's to change and the difference is recorded here.
