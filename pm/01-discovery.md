# Discovery: job application pipeline

Walkthrough step 1. Written 2026-09-09. Owner: Ally Haire.
Fields TRIED and EXISTS were answered from tool evidence, not memory. The lanes that
produced them are named inline.

ASK: "/walkthrough we are making a job application pipeline that already has LEGACY
  spec. It is well overdue, massively overbudget and standards have been extremely
  bad. The company will die if the FULL PRODUCT IS NOT PRODUCED PROPERLY and
  exceeding expectations in the next day. THERE IS NO ROOM FOR ERROR, no room for
  guesses, no room FOR REPEATING WORK, no room for unverified claims, no room for
  mistaken paths or any other gaps. The planning must be meticulously efficient,
  autistically detailed and thoroughly executed to meet USER requirements (not code
  tests)"

WHAT_IT_IS: A job application pipeline, already specified in a legacy document, to
  be delivered as a complete working product within one day, to a standard that
  exceeds what has been produced so far. Confirmed by owner.

WHO_ITS_FOR: Ally, as user zero and first user, then anyone else applying for jobs.
  Corrected by owner: it is a product, not a personal tool. No external user before
  it is built, so day one has one user and multi-user concerns are out of day-one
  scope.

WHY_IT_SHOULD_EXIST: Applications are not happening at all. Money and opportunity
  drain while nothing is submitted. The blocker is resume tailoring, in the owner's
  words "a shitshow". LLM attempts returned "slop, unverified shit and low effort
  output", so tailoring is where the pipeline dies.

TODAY: No jobs are applied for. When tailoring is attempted the output is not
  sendable, so the application is abandoned rather than submitted.

TRIED: Effort went into the management layer first, by deliberate choice. Owner's
  ruling, this session: "you cant build the product if you cant manage it". The
  prior unmanaged attempt is what produced the slop, so the control plane is the
  precondition, not a detour. What that produced, measured by lane D1-legacy-spec,
  24 of 24 authority files opened:
  - Legacy register `how/campaigns/career-os-requirements.md` holds 116
    requirements (78 stated S-NN, 23 inferred I-NN, 15 suggested G-NN). 3 are
    product-facing (S-76, S-77, S-78). 113 govern autonomy, delegation, drift,
    truthfulness and process.
  - 741 lines of tracked coordination code, plus ~3,150 untracked lines and data in
    `.worktrees/issue-5`. `git grep` for resume/tailor/cover-letter/job-ad/render
    across all tracked code returns zero hits. No product code exists in this repo.
  - 147 GitHub issues, 144 open. 137 of them are machine-generated backlog tickets,
    all `status:backlog`. 1 PR ever, #10, open and unmerged.
  Four defects found in the management layer itself, each verified:
  1. The register's stated top blocker, S-26, says GitHub `project` scope is absent
     and the work is "unbuildable by anyone until you grant the scope".
     `gh auth status` shows `project` present, and a 147-item board already exists.
     The blocker is false and has been gating work that was never blocked.
  2. `STATE.md:36` says "System blockers: None" while CONTROL-004, CONTROL-005 and
     CTRL-002 each record themselves as blocked, and issue #5 still carries
     `agent-running` with PR #10 mergeable and unreviewed.
  3. LANE-D-salvage never ran. No `rescue/issue-5` branch exists anywhere.
     `how/programme.json`, 2,603 lines, has never been in any commit.
  4. Register citation S-33 names a 14-class taxonomy at
     `who/governance/coordinator.md:52-64`. That range holds 8 classes.
  Open risk, untouched: the untracked root `.gitignore` ignores `.worktrees/` and
  `.career-os/`. Committing it as written makes the uncommitted programme.json
  permanently invisible to git status.

EXISTS: No product exists, anywhere. Measured against S-78
  (career-os-requirements.md:275), the only requirement that describes the product:
  "jobs found daily, resumes and cover letters tailored, approve-to-send, tracker,
  automatic follow-ups, application status derived from email. Five surfaces."
  Of those five, zero are built. Owner's ruling this session: "there isnt a product
  here. thats the point."
  What does exist, and what it is not, per lane D2-adjacent-estates:
  - `resume-system`: a resume renderer and editor. Produces real PDF bytes (18 in
    editor/out/, two in renders/, 6 and 7 pages, ~400KB, confirmed by `file`).
    Its tailoring script `scripts/tailor.mjs:3` declares itself a stub with the LLM
    call left as a TODO. It is one part of one surface, not the pipeline.
    Reported under a hard code freeze, not independently confirmed.
  - Career data: real and structured. 9 experience records, 3 projects, 20 talks,
    9 recognition entries, schema validated. This is an input to the product, not
    the product.
  - `resume-editor-v0`: a clean-tree fork of the above stopgap, 16 commits, own
    remote, cut out 2026-08-31 to stay writable. Same category, still not the
    pipeline.
  - `CorpusDB.adna` (77 files), m11 job application pipeline mission (31 files):
    documents only, zero entry points. m11 dates from July and is superseded.
  - Six or more further copies: `_resume-backups`, two dated `resume-data-backup`
    directories, `resume-recovery-2026-08-27`, `Job-Applications/resume`,
    `personal-brand/resume`. Predecessors and snapshots, none of them a product.
  - This repo: 0 lines of product code, verified by `git grep -il -E
    'resume|cover.letter|tailor|job.ad|render'` over all tracked code, no hits.
  Coverage: 6 of 23 locations settled to full evidence, 17 by existence and date
  only. No claim of "working and deployed" was verified anywhere.
  Verdict per walkthrough: BUILD. Not extend, not review. Existing pieces are
  inputs and predecessors, to be marked superseded rather than treated as progress.

CONSTRAINT: The owner's attention. Over 100 hours spent with nothing shippable. Not
  compute, not the calendar, not the one-day deadline, which is downstream of this.
  The system must produce sendable output without her supervising each step,
  because supervision is the resource that has already run out.

RUIN: Output she would refuse to send. Observable on a finished document as any of:
  poor styling; poor word choices; content not matching the job description; the
  wrong portfolio pieces selected; a cover letter of sloppy AI prose instead of high
  level language demonstrating exceptional skill and competency; nothing matching
  decades of research into what lands with hirers. That research lives "across the
  internet" and is captured nowhere on this machine, so no written standard
  currently exists in any repo against which output could be judged.
  Direct conflict on the record: `.worktrees/issue-5/docs/product/vision.md:35`
  defers cover letters to post-v1. The owner names a sloppy cover letter as the
  first refusal trigger. S-78 requires cover letters. The legacy v1 scope and the
  acceptance standard disagree, and this must be resolved in step 3.
