# Options: delivering Tier 1

Walkthrough step 4. Roster generated with the owner 2026-09-09 and closed by her in the same session.
Costs in hours are the PM's estimate, unvalidated, and are superseded by step 6 sizing.
Buy candidates were not priced: the owner closed the roster by selecting option 3 before the pricing
pass ran, so the cost cell reads unpriced with that reason rather than being left blank.

| # | Option | What it is | Cost | Forecloses | Door | Outcome |
|---|---|---|---|---|---|---|
| 0 | Do nothing | Keep applying by hand, or keep not applying | Zero applications, ongoing, per TODAY in pm/01-discovery.md | Nothing | two way | not selected |
| 1 | Buy | Teal, Jobscan, Rezi, Kickresume or Careerflow performs the tailoring | Not priced because the owner closed the roster before the pricing pass ran | Claim provenance, owner styling, owner data model | two way | not selected |
| 2 | Build in resume-editor-v0 | Extend the writable fork that already renders PDFs and holds career data | 8 to 14 hours | This repo as the product; retains the stopgap shape | two way | KILLED by owner |
| 3 | Build here, fresh | New product code in this repository, career facts imported as evidence | 20 to 30 hours | Reuse of the existing renderer | two way | SELECTED by owner |
| 4 | Finish the stub in place | Lift the freeze on resume-system, implement tailor.mjs where it already is | 6 to 12 hours | The freeze's protection | one way | KILLED by owner |
| 5 | Do not automate yet | Codify the standard, apply to three real jobs by hand using the rubric as the gate | 3 to 5 hours | A day of build time | two way | not selected |
| 6 | Split it | Tailoring engine here reading existing career JSON, rendering handed to resume-editor-v0 | 10 to 16 hours | A single codebase; adds a cross-repo seam | two way | KILLED by owner |

Owner's stated reason for killing 2, 4 and 6, verbatim: "this is a fresh build not importing BAD CODE
AND DESIGN FROM ELSEWHERE". No reason was stated for 0, 1 or 5, and none is invented here.

## Per option

**0 Do nothing**
Has to be true: the cost of another week without applications is bearable.
Early tell: still not applying by Friday 2026-09-11.

**1 Buy**
Has to be true: a bought tool will not fabricate claims, and will accept the owner's styling.
Early tell: the first output contains a claim the owner never made.

**2 Build in resume-editor-v0**
Has to be true: the fork's renderer and data are good enough to build on unchanged.
Early tell: the first tailoring run requires the renderer to be changed.

**3 Build here, fresh**
Has to be true: a renderer good enough to send can be built inside the window.
Early tell: no sendable PDF exists by mid-afternoon 2026-09-10.

**4 Finish the stub in place**
Has to be true: the freeze can be lifted safely and the reason for it no longer applies.
Early tell: something under the freeze breaks on the first commit.

**5 Do not automate yet**
Has to be true: three hand-made applications teach more than a half-built system.
Early tell: the rubric fails to discriminate between the owner's good and bad documents.

**6 Split it**
Has to be true: two repositories can be crossed without a day going into the seam.
Early tell: more than one hour goes into wiring before any tailoring happens.

## Field completeness

7 options, 5 fields each (what it is, cost, forecloses, has to be true, early tell) = 35 of 35 written.
No field is blank. One cost carries a reason in place of a number, stated above.
